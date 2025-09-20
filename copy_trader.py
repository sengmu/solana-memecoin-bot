"""
Copy trading functionality for monitoring leader wallets and copying their trades.
"""

import asyncio
import aiohttp
import logging
import time
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey as PublicKey

from models import TokenInfo, Trade, TradeType, BotConfig, TradingStats
from jupiter_trader import JupiterTrader


@dataclass
class LeaderTrade:
    """Represents a trade made by a leader wallet."""
    token_address: str
    trade_type: TradeType
    amount: float
    timestamp: datetime
    tx_hash: str
    confidence_score: float = 0.0


class CopyTrader:
    """Monitors leader wallets and copies their trades."""
    
    def __init__(self, config: BotConfig, jupiter_trader: JupiterTrader, on_trade_detected: Callable[[LeaderTrade], None]):
        self.config = config
        self.jupiter_trader = jupiter_trader
        self.on_trade_detected = on_trade_detected
        self.logger = logging.getLogger(__name__)
        self.client = AsyncClient(config.solana_rpc_url)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Leader wallet monitoring
        self.leader_wallet = PublicKey(config.leader_wallet_address) if config.leader_wallet_address else None
        self.last_checked_signature: Optional[str] = None
        self.known_tokens: Dict[str, TokenInfo] = {}
        
        # Copy trading state
        self.running = False
        self.copy_enabled = config.copy_trading_enabled
        self.min_confidence = config.min_confidence_score
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        await self.client.close()
        
    async def start_monitoring(self):
        """Start monitoring leader wallet for new trades."""
        if not self.leader_wallet:
            self.logger.warning("No leader wallet configured for copy trading")
            return
            
        self.running = True
        self.logger.info(f"Starting copy trading monitoring for wallet: {self.leader_wallet}")
        
        while self.running:
            try:
                await self._check_leader_trades()
                await asyncio.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Error in copy trading monitoring: {e}")
                await asyncio.sleep(30)  # Wait longer on error
                
    async def stop_monitoring(self):
        """Stop monitoring leader wallet."""
        self.running = False
        self.logger.info("Stopped copy trading monitoring")
        
    async def _check_leader_trades(self):
        """Check for new trades from leader wallet."""
        try:
            # Get recent signatures for the leader wallet
            signatures = await self._get_recent_signatures()
            
            if not signatures:
                return
                
            # Process new signatures
            for signature_info in signatures:
                signature = signature_info.signature
                
                # Skip if we've already processed this signature
                if self.last_checked_signature and signature == self.last_checked_signature:
                    break
                    
                # Analyze the transaction
                trade = await self._analyze_transaction(signature)
                if trade and trade.confidence_score >= self.min_confidence:
                    self.logger.info(f"Detected leader trade: {trade.trade_type.value} {trade.token_address}")
                    await self.on_trade_detected(trade)
                    
            # Update last checked signature
            if signatures:
                self.last_checked_signature = signatures[0].signature
                
        except Exception as e:
            self.logger.error(f"Error checking leader trades: {e}")
            
    async def _get_recent_signatures(self) -> List[Any]:
        """Get recent signatures for the leader wallet."""
        try:
            # Get signatures for the last hour
            before = None
            if self.last_checked_signature:
                before = self.last_checked_signature
                
            response = await self.client.get_signatures_for_address(
                self.leader_wallet,
                before=before,
                limit=50
            )
            
            return response.value if response.value else []
            
        except Exception as e:
            self.logger.error(f"Error getting recent signatures: {e}")
            return []
            
    async def _analyze_transaction(self, signature: str) -> Optional[LeaderTrade]:
        """Analyze a transaction to determine if it's a token trade."""
        try:
            # Get transaction details
            response = await self.client.get_transaction(
                signature,
                encoding="json",
                max_supported_transaction_version=0
            )
            
            if not response.value:
                return None
                
            transaction = response.value
            meta = transaction.meta
            
            # Check if transaction was successful
            if meta.err:
                return None
                
            # Look for token transfers
            token_transfers = self._extract_token_transfers(transaction)
            
            if not token_transfers:
                return None
                
            # Analyze the transfers to determine trade type and token
            trade_info = self._analyze_token_transfers(token_transfers)
            
            if not trade_info:
                return None
                
            # Calculate confidence score
            confidence_score = await self._calculate_confidence_score(trade_info, transaction)
            
            return LeaderTrade(
                token_address=trade_info['token_address'],
                trade_type=trade_info['trade_type'],
                amount=trade_info['amount'],
                timestamp=datetime.now(),
                tx_hash=signature,
                confidence_score=confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing transaction {signature}: {e}")
            return None
            
    def _extract_token_transfers(self, transaction: Any) -> List[Dict[str, Any]]:
        """Extract token transfers from transaction."""
        transfers = []
        
        try:
            meta = transaction.meta
            if not meta or not meta.inner_instructions:
                return transfers
                
            for inner_instruction in meta.inner_instructions:
                for instruction in inner_instruction.instructions:
                    if hasattr(instruction, 'parsed') and instruction.parsed:
                        parsed = instruction.parsed
                        if parsed.get('type') == 'transfer' or parsed.get('type') == 'transferChecked':
                            transfer_info = parsed.get('info', {})
                            if transfer_info:
                                transfers.append({
                                    'mint': transfer_info.get('mint'),
                                    'source': transfer_info.get('source'),
                                    'destination': transfer_info.get('destination'),
                                    'amount': transfer_info.get('amount'),
                                    'authority': transfer_info.get('authority')
                                })
                                
        except Exception as e:
            self.logger.error(f"Error extracting token transfers: {e}")
            
        return transfers
        
    def _analyze_token_transfers(self, transfers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Analyze token transfers to determine trade information."""
        try:
            # Group transfers by token
            token_transfers = {}
            for transfer in transfers:
                mint = transfer.get('mint')
                if not mint:
                    continue
                    
                if mint not in token_transfers:
                    token_transfers[mint] = []
                token_transfers[mint].append(transfer)
                
            # Find the most significant transfer
            for mint, mint_transfers in token_transfers.items():
                # Skip SOL (wrapped SOL)
                if mint == "So11111111111111111111111111111111111111112":
                    continue
                    
                # Calculate net amount for this token
                net_amount = 0
                for transfer in mint_transfers:
                    amount = int(transfer.get('amount', 0))
                    # Determine direction based on source/destination
                    if transfer.get('source') == str(self.leader_wallet):
                        net_amount -= amount  # Outgoing (sell)
                    elif transfer.get('destination') == str(self.leader_wallet):
                        net_amount += amount  # Incoming (buy)
                        
                if net_amount != 0:
                    return {
                        'token_address': mint,
                        'trade_type': TradeType.BUY if net_amount > 0 else TradeType.SELL,
                        'amount': abs(net_amount) / 1e9,  # Convert to token units
                        'raw_amount': abs(net_amount)
                    }
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing token transfers: {e}")
            return None
            
    async def _calculate_confidence_score(self, trade_info: Dict[str, Any], transaction: Any) -> float:
        """Calculate confidence score for a detected trade."""
        try:
            score = 50.0  # Base score
            
            # Check if we know this token
            token_address = trade_info['token_address']
            if token_address in self.known_tokens:
                token = self.known_tokens[token_address]
                
                # Higher confidence for tokens with good metrics
                if token.volume_24h > 1_000_000:
                    score += 20
                if token.liquidity > 100_000:
                    score += 15
                if token.holders > 1000:
                    score += 10
                    
            # Check transaction size (larger trades might be more significant)
            amount = trade_info['amount']
            if amount > 1000:  # Large amount
                score += 15
            elif amount > 100:  # Medium amount
                score += 10
            elif amount > 10:  # Small amount
                score += 5
                
            # Check if it's a buy (buys are generally more significant)
            if trade_info['trade_type'] == TradeType.BUY:
                score += 10
                
            # Check transaction age (newer transactions are more relevant)
            # This would require parsing the block time, simplified here
            score += 5
            
            return min(score, 100.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {e}")
            return 50.0
            
    async def copy_trade(self, leader_trade: LeaderTrade) -> Optional[Trade]:
        """Copy a trade from the leader wallet."""
        try:
            if not self.copy_enabled:
                self.logger.info("Copy trading is disabled")
                return None
                
            # Get token information
            token = await self._get_token_info(leader_trade.token_address)
            if not token:
                self.logger.warning(f"Could not get token info for {leader_trade.token_address}")
                return None
                
            # Calculate copy amount based on our position size
            copy_amount = self._calculate_copy_amount(leader_trade, token)
            
            if copy_amount <= 0:
                self.logger.warning("Copy amount too small or zero")
                return None
                
            # Execute the copy trade
            if leader_trade.trade_type == TradeType.BUY:
                trade = await self.jupiter_trader.buy_token(token, copy_amount)
            else:
                trade = await self.jupiter_trader.sell_token(token, copy_amount)
                
            if trade:
                self.logger.info(f"Successfully copied {leader_trade.trade_type.value} trade for {token.symbol}")
                
            return trade
            
        except Exception as e:
            self.logger.error(f"Error copying trade: {e}")
            return None
            
    async def _get_token_info(self, token_address: str) -> Optional[TokenInfo]:
        """Get token information from cache or fetch it."""
        try:
            # Check cache first
            if token_address in self.known_tokens:
                return self.known_tokens[token_address]
                
            # Fetch from DexScreener API
            async with self.session.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}") as response:
                if response.status == 200:
                    data = await response.json()
                    pairs = data.get('pairs', [])
                    
                    if pairs:
                        pair = pairs[0]  # Get the first pair
                        base_token = pair.get('baseToken', {})
                        
                        token = TokenInfo(
                            address=token_address,
                            symbol=base_token.get('symbol', ''),
                            name=base_token.get('name', ''),
                            decimals=base_token.get('decimals', 9),
                            price=float(pair.get('priceUsd', 0)),
                            market_cap=float(pair.get('fdv', 0)),
                            fdv=float(pair.get('fdv', 0)),
                            volume_24h=float(pair.get('volume', {}).get('h24', 0)),
                            price_change_24h=float(pair.get('priceChange', {}).get('h24', 0)),
                            liquidity=float(pair.get('liquidity', {}).get('usd', 0)),
                            holders=int(pair.get('info', {}).get('holders', 0)),
                            created_at=datetime.now()
                        )
                        
                        # Cache the token
                        self.known_tokens[token_address] = token
                        return token
                        
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting token info: {e}")
            return None
            
    def _calculate_copy_amount(self, leader_trade: LeaderTrade, token: TokenInfo) -> float:
        """Calculate how much to copy based on our position size limits."""
        try:
            # Get our current SOL balance
            sol_balance = asyncio.create_task(self.jupiter_trader.get_sol_balance())
            
            # Calculate maximum position size in SOL
            max_position_sol = self.config.max_position_size * sol_balance
            
            # Calculate token amount in SOL
            token_value_sol = leader_trade.amount * token.price
            
            # Scale down if necessary
            if token_value_sol > max_position_sol:
                scale_factor = max_position_sol / token_value_sol
                copy_amount = leader_trade.amount * scale_factor
            else:
                copy_amount = leader_trade.amount
                
            # Ensure minimum amount
            min_amount = 0.001  # Minimum 0.001 SOL
            if copy_amount * token.price < min_amount:
                return 0.0
                
            return copy_amount
            
        except Exception as e:
            self.logger.error(f"Error calculating copy amount: {e}")
            return 0.0
            
    def add_known_token(self, token: TokenInfo):
        """Add a token to the known tokens cache."""
        self.known_tokens[token.address] = token
        
    def get_known_tokens(self) -> Dict[str, TokenInfo]:
        """Get all known tokens."""
        return self.known_tokens.copy()
        
    def clear_known_tokens(self):
        """Clear the known tokens cache."""
        self.known_tokens.clear()
