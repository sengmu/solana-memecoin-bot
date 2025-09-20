"""
Wallet monitoring system for tracking new tokens and portfolio changes.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey as PublicKey

from models import TokenInfo, BotConfig, TradingStats

@dataclass
class WalletToken:
    """Represents a token held in the wallet."""
    address: str
    symbol: str
    name: str
    balance: float
    value_usd: float
    price: float
    last_updated: datetime

@dataclass
class PortfolioSnapshot:
    """Snapshot of the wallet portfolio at a point in time."""
    timestamp: datetime
    total_value_usd: float
    sol_balance: float
    tokens: Dict[str, WalletToken]
    new_tokens: List[str]  # New token addresses since last snapshot
    removed_tokens: List[str]  # Removed token addresses since last snapshot

class WalletMonitor:
    """Monitors wallet for new tokens and portfolio changes."""

    def __init__(self, config: BotConfig, on_new_token: Callable[[WalletToken], None],
                 on_portfolio_change: Callable[[PortfolioSnapshot], None]):
        self.config = config
        self.on_new_token = on_new_token
        self.on_portfolio_change = on_portfolio_change
        self.logger = logging.getLogger(__name__)
        self.client = AsyncClient(config.solana_rpc_url)

        # Wallet monitoring state
        self.wallet_pubkey = None
        self.running = False
        self.last_snapshot: Optional[PortfolioSnapshot] = None
        self.known_tokens: Set[str] = set()

        # Load wallet securely
        try:
            import os
            from solders.keypair import Keypair

            private_key = os.getenv('PRIVATE_KEY')
            if not private_key:
                raise ValueError("PRIVATE_KEY environment variable not set")

            wallet = Keypair.from_base58_string(private_key)
            self.wallet_pubkey = wallet.pubkey()
            self.logger.info(f"Wallet monitor initialized for: {self.wallet_pubkey}")
        except Exception as e:
            self.logger.error(f"Failed to initialize wallet monitor: {e}")
            raise

    async def start_monitoring(self, interval: int = 30):
        """Start monitoring wallet for changes."""
        if not self.wallet_pubkey:
            self.logger.error("No wallet configured for monitoring")
            return

        self.running = True
        self.logger.info(f"Starting wallet monitoring (interval: {interval}s)")

        # Take initial snapshot
        await self._take_snapshot()

        while self.running:
            try:
                await asyncio.sleep(interval)
                if self.running:
                    await self._check_for_changes()

            except Exception as e:
                self.logger.error(f"Error in wallet monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def stop_monitoring(self):
        """Stop wallet monitoring."""
        self.running = False
        self.logger.info("Stopped wallet monitoring")

    async def _check_for_changes(self):
        """Check for changes in wallet portfolio."""
        try:
            current_snapshot = await self._take_snapshot()

            if self.last_snapshot:
                # Compare with previous snapshot
                changes = self._compare_snapshots(self.last_snapshot, current_snapshot)

                if changes['new_tokens'] or changes['removed_tokens'] or changes['value_changed']:
                    self.logger.info(f"Portfolio changes detected: {len(changes['new_tokens'])} new, {len(changes['removed_tokens'])} removed")

                    # Notify about new tokens
                    for token_address in changes['new_tokens']:
                        if token_address in current_snapshot.tokens:
                            token = current_snapshot.tokens[token_address]
                            await self.on_new_token(token)

                    # Notify about portfolio changes
                    await self.on_portfolio_change(current_snapshot)

            self.last_snapshot = current_snapshot

        except Exception as e:
            self.logger.error(f"Error checking for changes: {e}")

    async def _take_snapshot(self) -> PortfolioSnapshot:
        """Take a snapshot of the current wallet portfolio."""
        try:
            # Get SOL balance
            sol_balance = await self._get_sol_balance()

            # Get all token accounts
            token_accounts = await self._get_token_accounts()

            # Process each token account
            tokens = {}
            total_value_usd = sol_balance * await self._get_sol_price()

            for account in token_accounts:
                try:
                    token_info = await self._process_token_account(account)
                    if token_info:
                        tokens[token_info.address] = token_info
                        total_value_usd += token_info.value_usd

                except Exception as e:
                    self.logger.error(f"Error processing token account: {e}")
                    continue

            # Identify new and removed tokens
            new_tokens = []
            removed_tokens = []

            if self.last_snapshot:
                current_addresses = set(tokens.keys())
                previous_addresses = set(self.last_snapshot.tokens.keys())

                new_tokens = list(current_addresses - previous_addresses)
                removed_tokens = list(previous_addresses - current_addresses)

                # Update known tokens set
                self.known_tokens.update(new_tokens)
                self.known_tokens.difference_update(removed_tokens)
            else:
                # First snapshot - all tokens are "new"
                new_tokens = list(tokens.keys())
                self.known_tokens.update(new_tokens)

            return PortfolioSnapshot(
                timestamp=datetime.now(),
                total_value_usd=total_value_usd,
                sol_balance=sol_balance,
                tokens=tokens,
                new_tokens=new_tokens,
                removed_tokens=removed_tokens
            )

        except Exception as e:
            self.logger.error(f"Error taking portfolio snapshot: {e}")
            return PortfolioSnapshot(
                timestamp=datetime.now(),
                total_value_usd=0.0,
                sol_balance=0.0,
                tokens={},
                new_tokens=[],
                removed_tokens=[]
            )

    async def _get_sol_balance(self) -> float:
        """Get SOL balance."""
        try:
            response = await self.client.get_balance(self.wallet_pubkey)
            return response.value / 1e9  # Convert lamports to SOL
        except Exception as e:
            self.logger.error(f"Error getting SOL balance: {e}")
            return 0.0

    async def _get_sol_price(self) -> float:
        """Get current SOL price in USD."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd") as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data.get('solana', {}).get('usd', 0))
        except Exception as e:
            self.logger.error(f"Error getting SOL price: {e}")

        return 0.0  # Fallback price

    async def _get_token_accounts(self) -> List[Dict[str, Any]]:
        """Get all token accounts for the wallet."""
        try:
            response = await self.client.get_token_accounts_by_owner(
                self.wallet_pubkey,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"}  # SPL Token program
            )

            accounts = []
            if response.value:
                for account_info in response.value:
                    try:
                        account_data = account_info.account.data.parsed['info']
                        accounts.append({
                            'pubkey': str(account_info.pubkey),
                            'mint': account_data['mint'],
                            'amount': account_data['tokenAmount']['amount'],
                            'decimals': account_data['tokenAmount']['decimals'],
                            'ui_amount': account_data['tokenAmount']['uiAmount']
                        })
                    except Exception as e:
                        self.logger.error(f"Error parsing token account: {e}")
                        continue

            return accounts

        except Exception as e:
            self.logger.error(f"Error getting token accounts: {e}")
            return []

    async def _process_token_account(self, account: Dict[str, Any]) -> Optional[WalletToken]:
        """Process a token account and return token information."""
        try:
            mint = account['mint']
            balance = float(account['ui_amount']) if account['ui_amount'] else 0.0

            # Skip zero balance accounts
            if balance <= 0:
                return None

            # Get token metadata
            token_metadata = await self._get_token_metadata(mint)
            if not token_metadata:
                return None

            # Calculate USD value
            price = token_metadata.get('price', 0.0)
            value_usd = balance * price

            return WalletToken(
                address=mint,
                symbol=token_metadata.get('symbol', ''),
                name=token_metadata.get('name', ''),
                balance=balance,
                value_usd=value_usd,
                price=price,
                last_updated=datetime.now()
            )

        except Exception as e:
            self.logger.error(f"Error processing token account: {e}")
            return None

    async def _get_token_metadata(self, mint: str) -> Optional[Dict[str, Any]]:
        """Get token metadata from DexScreener API."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.dexscreener.com/latest/dex/tokens/{mint}") as response:
                    if response.status == 200:
                        data = await response.json()
                        pairs = data.get('pairs', [])

                        if pairs:
                            pair = pairs[0]  # Get the first pair
                            base_token = pair.get('baseToken', {})

                            return {
                                'symbol': base_token.get('symbol', ''),
                                'name': base_token.get('name', ''),
                                'price': float(pair.get('priceUsd', 0)),
                                'decimals': base_token.get('decimals', 9)
                            }

        except Exception as e:
            self.logger.error(f"Error getting token metadata for {mint}: {e}")

        return None

    def _compare_snapshots(self, previous: PortfolioSnapshot, current: PortfolioSnapshot) -> Dict[str, Any]:
        """Compare two portfolio snapshots and return changes."""
        previous_addresses = set(previous.tokens.keys())
        current_addresses = set(current.tokens.keys())

        new_tokens = list(current_addresses - previous_addresses)
        removed_tokens = list(previous_addresses - current_addresses)

        # Check for value changes
        value_change_threshold = 0.01  # 1% change threshold
        value_changed = abs(current.total_value_usd - previous.total_value_usd) / previous.total_value_usd > value_change_threshold

        return {
            'new_tokens': new_tokens,
            'removed_tokens': removed_tokens,
            'value_changed': value_changed,
            'value_change_percent': ((current.total_value_usd - previous.total_value_usd) / previous.total_value_usd * 100) if previous.total_value_usd > 0 else 0
        }

    async def get_current_portfolio(self) -> Optional[PortfolioSnapshot]:
        """Get current portfolio snapshot."""
        return await self._take_snapshot()

    async def get_token_balance(self, token_address: str) -> float:
        """Get balance for a specific token."""
        try:
            token_pubkey = PublicKey(token_address)
            response = await self.client.get_token_accounts_by_owner(
                self.wallet_pubkey,
                {"mint": token_pubkey}
            )

            if response.value:
                account_info = response.value[0].account.data.parsed['info']
                return float(account_info['tokenAmount']['uiAmount']) if account_info['tokenAmount']['uiAmount'] else 0.0
            else:
                return 0.0

        except Exception as e:
            self.logger.error(f"Error getting token balance for {token_address}: {e}")
            return 0.0

    def get_known_tokens(self) -> Set[str]:
        """Get set of known token addresses."""
        return self.known_tokens.copy()

    def is_token_known(self, token_address: str) -> bool:
        """Check if a token is known to the monitor."""
        return token_address in self.known_tokens
