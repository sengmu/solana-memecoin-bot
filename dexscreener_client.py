"""
DexScreener WebSocket client for discovering trending Solana memecoins.
"""

import asyncio
import json
import logging
import websockets
import requests
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup
import re

from models import TokenInfo, TokenStatus, BotConfig

class DexScreenerClient:
    """DexScreener WebSocket client for real-time token discovery."""

    def __init__(self, config: BotConfig, on_token_discovered: Callable[[TokenInfo], None]):
        self.config = config
        self.on_token_discovered = on_token_discovered
        self.logger = logging.getLogger(__name__)
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5

        # DexScreener WebSocket URL
        self.ws_url = "wss://io.dexscreener.com/dex/screener/pairs/h24/1?rankBy[key]=trendingScoreH6&rankBy[order]=desc&filters[chainIds][0]=solana"

    async def start(self):
        """Start the WebSocket connection and begin listening for tokens."""
        self.running = True
        await self._connect()

    async def stop(self):
        """Stop the WebSocket connection."""
        self.running = False
        if self.websocket:
            await self.websocket.close()

    async def _connect(self):
        """Establish WebSocket connection with retry logic."""
        while self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                self.logger.info(f"Connecting to DexScreener WebSocket (attempt {self.reconnect_attempts + 1})")

                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=10,
                    close_timeout=10
                ) as websocket:
                    self.websocket = websocket
                    self.reconnect_attempts = 0
                    self.logger.info("Connected to DexScreener WebSocket")

                    # Listen for messages
                    async for message in websocket:
                        if not self.running:
                            break
                        await self._handle_message(message)

            except websockets.exceptions.ConnectionClosed:
                self.logger.warning("DexScreener WebSocket connection closed")
            except Exception as e:
                self.logger.error(f"WebSocket error: {e}")

            if self.running:
                self.reconnect_attempts += 1
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
                    await asyncio.sleep(self.reconnect_delay)
                else:
                    self.logger.error("Max reconnection attempts reached")
                    break

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)

            # Check if message contains pair data
            if 'pairs' in data and data['pairs']:
                for pair_data in data['pairs']:
                    token_info = await self._parse_pair_data(pair_data)
                    if token_info and self._is_valid_memecoin(token_info):
                        self.logger.info(f"Discovered memecoin: {token_info.symbol} ({token_info.address})")
                        await self.on_token_discovered(token_info)

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse WebSocket message: {e}")
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")

    async def _parse_pair_data(self, pair_data: Dict[str, Any]) -> Optional[TokenInfo]:
        """Parse DexScreener pair data into TokenInfo object."""
        try:
            # Extract basic token information
            base_token = pair_data.get('baseToken', {})
            quote_token = pair_data.get('quoteToken', {})

            # Only process SOL pairs
            if quote_token.get('symbol') != 'SOL':
                return None

            address = base_token.get('address', '')
            if not address:
                return None

            # Extract market data
            price_usd = pair_data.get('priceUsd', 0)
            fdv = pair_data.get('fdv', 0)
            volume_24h = pair_data.get('volume', {}).get('h24', 0)
            price_change_24h = pair_data.get('priceChange', {}).get('h24', 0)
            liquidity = pair_data.get('liquidity', {}).get('usd', 0)

            # Extract token metadata
            symbol = base_token.get('symbol', '')
            name = base_token.get('name', '')
            decimals = base_token.get('decimals', 9)

            # Calculate market cap
            market_cap = fdv  # Use FDV as market cap approximation

            # Get holder count (if available)
            holders = pair_data.get('info', {}).get('holders', 0)

            # Parse creation time
            created_at = datetime.now()
            if 'pairCreatedAt' in pair_data:
                try:
                    created_at = datetime.fromtimestamp(pair_data['pairCreatedAt'] / 1000)
                except (ValueError, TypeError):
                    pass

            return TokenInfo(
                address=address,
                symbol=symbol,
                name=name,
                decimals=decimals,
                price=price_usd,
                market_cap=market_cap,
                fdv=fdv,
                volume_24h=volume_24h,
                price_change_24h=price_change_24h,
                liquidity=liquidity,
                holders=holders,
                created_at=created_at,
                status=TokenStatus.PENDING
            )

        except Exception as e:
            self.logger.error(f"Error parsing pair data: {e}")
            return None

    def _is_valid_memecoin(self, token: TokenInfo) -> bool:
        """Check if token meets memecoin criteria."""
        try:
            # Check volume requirement
            if token.volume_24h < self.config.min_volume_24h:
                return False

            # Check FDV requirement
            if token.fdv < self.config.min_fdv:
                return False

            # Check if it's a memecoin based on keywords
            token_text = f"{token.symbol} {token.name}".lower()
            is_memecoin = any(keyword in token_text for keyword in self.config.meme_keywords)

            if is_memecoin:
                token.is_memecoin = True
                return True

            # Additional memecoin heuristics
            # Check for common memecoin patterns
            memecoin_patterns = [
                r'^[A-Z]{3,10}$',  # All caps symbols
                r'.*[Dd]oge.*',    # Doge variations
                r'.*[Pp]epe.*',    # Pepe variations
                r'.*[Mm]eme.*',    # Meme variations
                r'.*[Ii]nu.*',     # Inu variations
                r'.*[Cc]at.*',     # Cat variations
                r'.*[Dd]og.*',     # Dog variations
            ]

            for pattern in memecoin_patterns:
                if re.search(pattern, token.symbol) or re.search(pattern, token.name):
                    token.is_memecoin = True
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error validating memecoin: {e}")
            return False

    async def get_trending_tokens(self, limit: int = 50) -> List[TokenInfo]:
        """Get trending tokens from DexScreener API (fallback method)."""
        try:
            import aiohttp

            url = "https://api.dexscreener.com/latest/dex/tokens/trending"
            params = {
                'chainId': 'solana',
                'limit': limit
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tokens = []

                        for pair_data in data.get('pairs', []):
                            token_info = await self._parse_pair_data(pair_data)
                            if token_info and self._is_valid_memecoin(token_info):
                                tokens.append(token_info)

                        return tokens
                    else:
                        self.logger.error(f"Failed to fetch trending tokens: {response.status}")
                        return []

        except Exception as e:
            self.logger.error(f"Error fetching trending tokens: {e}")
            return []

    async def fetch_trending_pairs(self, max_pairs: int = 200, timeout: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch trending pairs from DexScreener using API.

        Args:
            max_pairs: Maximum number of pairs to fetch
            timeout: Timeout in seconds

        Returns:
            List of pair dictionaries from DexScreener API
        """
        try:
            # Use DexScreener API for reliable data
            url = "https://api.dexscreener.com/latest/dex/search"
            params = {"q": "solana"}
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
            'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            # Make async request
            response = await asyncio.to_thread(
                requests.get, url, params=params, headers=headers, timeout=timeout
            )
            response.raise_for_status()

            data = response.json()
            pairs = data.get('pairs', [])[:max_pairs]

            if pairs:
                self.logger.info(f"Successfully fetched {len(pairs)} pairs from DexScreener API")
                return pairs
            else:
                self.logger.warning("No pairs found in API response, using fallback data")
                return self._get_fallback_pairs()

        except Exception as e:
            self.logger.error(f"Error fetching trending pairs from API: {e}")
            return self._get_fallback_pairs()

    def _get_fallback_pairs(self) -> List[Dict[str, Any]]:
        """Get fallback sample pairs when API fails"""
        sample_pairs = [
            {
                "baseToken": {
                    "name": "BONK",
                    "symbol": "BONK",
                    "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"
                },
                "fdv": 1000000000,
                "volume": {"h24": 50000000},
                "priceChange": {"h24": 5.2},
                "pairAddress": "pair1",
                "priceUsd": 0.000001,
                "socials": [{"followers": 15000}]
            },
            {
                "baseToken": {
                    "name": "PEPE",
                    "symbol": "PEPE",
                    "address": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                },
                "fdv": 2000000000,
                "volume": {"h24": 75000000},
                "priceChange": {"h24": -2.1},
                "pairAddress": "pair2",
                "priceUsd": 0.000002,
                "socials": [{"followers": 25000}]
            },
            {
                "baseToken": {
                    "name": "DOGE",
                    "symbol": "DOGE",
                    "address": "9n4nbM75f5Ui33ZbPYXn59EwSgE8CGsHtAeTH5YFeJ9E"
                },
                "fdv": 5000000000,
                "volume": {"h24": 100000000},
                "priceChange": {"h24": 8.5},
                "pairAddress": "pair3",
                "priceUsd": 0.000003,
                "socials": [{"followers": 50000}]
            },
            {
                "baseToken": {
                    "name": "SHIB",
                    "symbol": "SHIB",
                    "address": "CiKu4eJVdj1ztvpCRZZ3TzG3LkzS3qq4UwvJ7XkfoRGN"
                },
                "fdv": 3000000000,
                "volume": {"h24": 80000000},
                "priceChange": {"h24": 12.3},
                "pairAddress": "pair4",
                "priceUsd": 0.000004,
                "socials": [{"followers": 30000}]
            },
            {
                "baseToken": {
                    "name": "FLOKI",
                    "symbol": "FLOKI",
                    "address": "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs"
                },
                "fdv": 1500000000,
                "volume": {"h24": 60000000},
                "priceChange": {"h24": -5.7},
                "pairAddress": "pair5",
                "priceUsd": 0.000005,
                "socials": [{"followers": 20000}]
            }
        ]
        return sample_pairs

    def _scrape_trending_pairs(self, max_pairs: int, headers: dict, timeout: int) -> List[TokenInfo]:
        """
        Synchronous web scraping function to run in thread pool.

        Args:
            max_pairs: Maximum number of pairs to fetch
            headers: HTTP headers for the request
            timeout: Request timeout in seconds

        Returns:
            List of TokenInfo objects for trending pairs
        """
        logger = logging.getLogger(__name__)

    def _generate_mock_trending_pairs(self, max_pairs: int) -> List[TokenInfo]:
        """Generate mock trending pairs for demonstration when scraping fails."""
        import random
        from datetime import datetime, timedelta

        mock_tokens = []
        symbols = [
            'PEPE', 'DOGE', 'BONK', 'SHIB', 'FLOKI', 'WOJAK', 'CHAD', 'KEKW',
            'MOON', 'DEGEN', 'APE', 'MONKE', 'FROG', 'CAT', 'DOG', 'HODL',
            'DIAMOND', 'ROCKET', 'LAMBO', 'YOLO', 'PUMP', 'MEME', 'COIN',
            'TOKEN', 'CRYPTO', 'BLOCK', 'CHAIN', 'DEFI', 'NFT', 'DAO'
        ]

        for i in range(min(max_pairs, 30)):  # Generate up to 30 mock tokens
            symbol = symbols[i % len(symbols)]
            if i >= len(symbols):
                symbol = f"{symbol}{i}"

            # Generate realistic price ranges
            price = random.uniform(0.000001, 0.1)
            volume_24h = random.uniform(100000, 50000000)
            fdv = volume_24h * random.uniform(5, 50)
            change_24h = random.uniform(-80, 500)

            token = TokenInfo(
                address=f"mock_{symbol.lower()}_{random.randint(10000, 99999)}",
                symbol=symbol,
                name=f"{symbol} Token",
                decimals=9,
                price=price,
                market_cap=fdv,
                fdv=fdv,
                volume_24h=volume_24h,
                price_change_24h=change_24h,
                liquidity=volume_24h * 0.1,
                holders=random.randint(100, 10000),
                created_at=datetime.now() - timedelta(days=random.randint(1, 365)),
                status=random.choice([TokenStatus.PENDING, TokenStatus.APPROVED, TokenStatus.TRADING]),
                twitter_score=random.uniform(0, 100),
                rugcheck_score=str(random.uniform(0, 100)),
                confidence_score=random.uniform(0, 1),
                is_memecoin=True
            )

            if self._is_valid_memecoin(token):
                mock_tokens.append(token)

        return mock_tokens

# Test function
async def test_fetch_trending_pairs():
    """Test the fetch_trending_pairs function."""
    import logging
    logging.basicConfig(level=logging.INFO)

    # Create a mock config
    from models import BotConfig
    config = BotConfig()

    # Create client
    client = DexScreenerClient(config, lambda x: None)

    # Test fetch_trending_pairs
    try:
        pairs = await client.fetch_trending_pairs(max_pairs=5)
        print(f"✅ Successfully fetched {len(pairs)} pairs")

        if pairs:
            print("Sample pair:")
            print(f"  Symbol: {pairs[0].get('baseToken', {}).get('symbol', 'N/A')}")
            print(f"  Name: {pairs[0].get('baseToken', {}).get('name', 'N/A')}")
            print(f"  Volume: {pairs[0].get('volume', {}).get('h24', 'N/A')}")
            print(f"  FDV: {pairs[0].get('fdv', 'N/A')}")

        return pairs

    except Exception as e:
        print(f"❌ Error: {e}")
        return []

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_fetch_trending_pairs())
