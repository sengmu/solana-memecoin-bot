"""
Jupiter V6 trading integration with dynamic fees and slippage management.
"""

import asyncio
import aiohttp
import json
import logging
import time
import os
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
import base58

from solana.rpc.async_api import AsyncClient
from solana.rpc.types import TxOpts
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solders.signature import Signature
from solders.transaction import VersionedTransaction

from models import TokenInfo, Trade, TradeType, BotConfig


class JupiterTrader:
    """Jupiter V6 trading integration with advanced features."""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = AsyncClient(config.solana_rpc_url)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Load wallet securely
        try:
            private_key = os.getenv('PRIVATE_KEY')
            if not private_key:
                raise ValueError("PRIVATE_KEY environment variable not set")
            
            self.wallet = Keypair.from_base58_string(private_key)
            self.logger.info(f"Wallet loaded: {self.wallet.pubkey()}")
        except Exception as e:
            self.logger.error(f"Failed to load wallet: {e}")
            raise
            
        # Jupiter API endpoints
        self.jupiter_base_url = "https://quote-api.jup.ag/v6"
        self.jupiter_swap_url = "https://quote-api.jup.ag/v6/swap"
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
        await self.client.close()
        
    async def buy_token(self, token: TokenInfo, amount_sol: float) -> Optional[Trade]:
        """Buy a token using Jupiter V6."""
        try:
            # Calculate dynamic slippage based on volatility
            slippage = await self._calculate_dynamic_slippage(token)
            
            # Get quote
            quote = await self._get_quote(
                input_mint="So11111111111111111111111111111111111111112",  # SOL
                output_mint=token.address,
                amount=int(amount_sol * 1e9),  # Convert to lamports
                slippage_bps=int(slippage * 10000)  # Convert to basis points
            )
            
            if not quote:
                self.logger.error(f"Failed to get quote for {token.symbol}")
                return None
                
            # Get priority fee
            priority_fee = await self._get_priority_fee()
            
            # Execute swap
            trade = await self._execute_swap(quote, token, amount_sol, slippage, priority_fee)
            
            return trade
            
        except Exception as e:
            self.logger.error(f"Error buying token {token.symbol}: {e}")
            return None
            
    async def sell_token(self, token: TokenInfo, amount_tokens: float) -> Optional[Trade]:
        """Sell a token using Jupiter V6."""
        try:
            # Calculate dynamic slippage
            slippage = await self._calculate_dynamic_slippage(token)
            
            # Get token balance
            token_balance = await self._get_token_balance(token.address)
            if token_balance < amount_tokens:
                self.logger.warning(f"Insufficient token balance: {token_balance} < {amount_tokens}")
                return None
                
            # Convert token amount to raw amount
            raw_amount = int(amount_tokens * (10 ** token.decimals))
            
            # Get quote
            quote = await self._get_quote(
                input_mint=token.address,
                output_mint="So11111111111111111111111111111111111111112",  # SOL
                amount=raw_amount,
                slippage_bps=int(slippage * 10000)
            )
            
            if not quote:
                self.logger.error(f"Failed to get quote for selling {token.symbol}")
                return None
                
            # Get priority fee
            priority_fee = await self._get_priority_fee()
            
            # Execute swap
            trade = await self._execute_swap(quote, token, amount_tokens, slippage, priority_fee, TradeType.SELL)
            
            return trade
            
        except Exception as e:
            self.logger.error(f"Error selling token {token.symbol}: {e}")
            return None
            
    async def _get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> Optional[Dict[str, Any]]:
        """Get quote from Jupiter V6 API."""
        try:
            params = {
                'inputMint': input_mint,
                'outputMint': output_mint,
                'amount': str(amount),
                'slippageBps': slippage_bps,
                'swapMode': 'ExactIn',
                'onlyDirectRoutes': 'false',
                'asLegacyTransaction': 'false'
            }
            
            async with self.session.get(f"{self.jupiter_base_url}/quote", params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Jupiter quote failed: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting Jupiter quote: {e}")
            return None
            
    async def _execute_swap(self, quote: Dict[str, Any], token: TokenInfo, amount: float, 
                          slippage: float, priority_fee: int, trade_type: TradeType = TradeType.BUY) -> Optional[Trade]:
        """Execute the swap transaction."""
        try:
            # Get swap transaction
            swap_response = await self._get_swap_transaction(quote)
            if not swap_response:
                return None
                
            # Parse transaction
            swap_transaction = swap_response.get('swapTransaction')
            if not swap_transaction:
                self.logger.error("No swap transaction in response")
                return None
                
            # Decode and sign transaction
            transaction_bytes = base58.b58decode(swap_transaction)
            transaction = VersionedTransaction.from_bytes(transaction_bytes)
            
            # Add priority fee
            if priority_fee > 0:
                transaction = await self._add_priority_fee(transaction, priority_fee)
                
            # Sign transaction
            transaction.sign([self.wallet], self.client._provider.commitment)
            
            # Send transaction
            signature = await self.client.send_transaction(transaction)
            
            # Wait for confirmation
            confirmed = await self._wait_for_confirmation(signature)
            
            # Create trade record
            trade = Trade(
                id=f"{trade_type.value}_{int(time.time())}",
                token_address=token.address,
                trade_type=trade_type,
                amount=amount,
                price=float(quote.get('outAmount', 0)) / 1e9 if trade_type == TradeType.BUY else float(quote.get('inAmount', 0)) / 1e9,
                slippage=slippage,
                priority_fee=priority_fee,
                tx_hash=str(signature),
                success=confirmed
            )
            
            if confirmed:
                self.logger.info(f"Successfully executed {trade_type.value} for {token.symbol}")
            else:
                self.logger.error(f"Transaction failed for {token.symbol}")
                
            return trade
            
        except Exception as e:
            self.logger.error(f"Error executing swap: {e}")
            return None
            
    async def _get_swap_transaction(self, quote: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get swap transaction from Jupiter."""
        try:
            swap_request = {
                'quoteResponse': quote,
                'userPublicKey': str(self.wallet.pubkey()),
                'wrapAndUnwrapSol': True,
                'useSharedAccounts': True,
                'feeAccount': None,
                'trackingAccount': None,
                'computeUnitPriceMicroLamports': None,
                'asLegacyTransaction': False
            }
            
            async with self.session.post(
                self.jupiter_swap_url,
                json=swap_request,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    self.logger.error(f"Jupiter swap request failed: {response.status}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error getting swap transaction: {e}")
            return None
            
    async def _calculate_dynamic_slippage(self, token: TokenInfo) -> float:
        """Calculate dynamic slippage based on token volatility."""
        try:
            # Base slippage
            base_slippage = self.config.default_slippage
            
            # Adjust based on volume
            if token.volume_24h > 10_000_000:  # High volume
                volume_multiplier = 0.5
            elif token.volume_24h > 1_000_000:  # Medium volume
                volume_multiplier = 0.8
            else:  # Low volume
                volume_multiplier = 1.2
                
            # Adjust based on price change
            if abs(token.price_change_24h) > 50:  # High volatility
                volatility_multiplier = 1.5
            elif abs(token.price_change_24h) > 20:  # Medium volatility
                volatility_multiplier = 1.2
            else:  # Low volatility
                volatility_multiplier = 1.0
                
            # Adjust based on liquidity
            if token.liquidity > 1_000_000:  # High liquidity
                liquidity_multiplier = 0.8
            elif token.liquidity > 100_000:  # Medium liquidity
                liquidity_multiplier = 1.0
            else:  # Low liquidity
                liquidity_multiplier = 1.3
                
            # Calculate final slippage
            dynamic_slippage = base_slippage * volume_multiplier * volatility_multiplier * liquidity_multiplier
            
            # Ensure within bounds
            return max(0.001, min(dynamic_slippage, self.config.max_slippage))
            
        except Exception as e:
            self.logger.error(f"Error calculating dynamic slippage: {e}")
            return self.config.default_slippage
            
    async def _get_priority_fee(self) -> int:
        """Get recent prioritization fees for dynamic fee calculation."""
        try:
            # Get recent prioritization fees
            response = await self.client.get_recent_prioritization_fees()
            
            if response.value:
                # Calculate median fee
                fees = [fee.prioritization_fee for fee in response.value]
                fees.sort()
                median_fee = fees[len(fees) // 2] if fees else 0
                
                # Add some buffer
                return int(median_fee * 1.2)
            else:
                # Default fee
                return 1000
                
        except Exception as e:
            self.logger.error(f"Error getting priority fee: {e}")
            return 1000
            
    async def _add_priority_fee(self, transaction: VersionedTransaction, priority_fee: int) -> VersionedTransaction:
        """Add priority fee to transaction."""
        try:
            # This is a simplified implementation
            # In practice, you'd need to modify the transaction to include compute budget instructions
            return transaction
        except Exception as e:
            self.logger.error(f"Error adding priority fee: {e}")
            return transaction
            
    async def _wait_for_confirmation(self, signature: Signature, timeout: int = 60) -> bool:
        """Wait for transaction confirmation."""
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = await self.client.get_signature_statuses([signature])
                    if response.value and response.value[0]:
                        status = response.value[0]
                        if status.confirmation_status:
                            return status.confirmation_status.name == "FINALIZED"
                        elif status.err:
                            self.logger.error(f"Transaction failed: {status.err}")
                            return False
                            
                except Exception as e:
                    self.logger.error(f"Error checking confirmation: {e}")
                    
                await asyncio.sleep(2)
                
            self.logger.error("Transaction confirmation timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for confirmation: {e}")
            return False
            
    async def _get_token_balance(self, token_address: str) -> float:
        """Get token balance for the wallet."""
        try:
            token_pubkey = PublicKey(token_address)
            response = await self.client.get_token_accounts_by_owner(
                self.wallet.pubkey(),
                {"mint": token_pubkey}
            )
            
            if response.value:
                # Get the first token account
                account_info = response.value[0].account.data.parsed['info']
                balance = account_info['tokenAmount']['uiAmount']
                return float(balance) if balance else 0.0
            else:
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error getting token balance: {e}")
            return 0.0
            
    async def get_sol_balance(self) -> float:
        """Get SOL balance."""
        try:
            response = await self.client.get_balance(self.wallet.pubkey())
            return response.value / 1e9  # Convert lamports to SOL
        except Exception as e:
            self.logger.error(f"Error getting SOL balance: {e}")
            return 0.0
            
    async def estimate_swap_amount(self, input_mint: str, output_mint: str, 
                                 input_amount: float) -> Optional[float]:
        """Estimate output amount for a swap."""
        try:
            if input_mint == "So11111111111111111111111111111111111111112":  # SOL
                raw_amount = int(input_amount * 1e9)
            else:
                # For tokens, we need to know decimals
                raw_amount = int(input_amount * 1e9)  # Simplified
                
            quote = await self._get_quote(input_mint, output_mint, raw_amount, 100)  # 1% slippage
            
            if quote:
                out_amount = float(quote.get('outAmount', 0))
                if output_mint == "So11111111111111111111111111111111111111112":  # SOL
                    return out_amount / 1e9
                else:
                    return out_amount / 1e9  # Simplified
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error estimating swap amount: {e}")
            return None
