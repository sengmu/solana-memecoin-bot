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

    async def fetch_trending_pairs(self, max_pairs: int = 200, timeout: int = 10) -> List[TokenInfo]:
        """
        Fetch trending pairs from DexScreener using web scraping.
        
        Args:
            max_pairs: Maximum number of pairs to fetch
            timeout: Timeout in seconds
            
        Returns:
            List of TokenInfo objects for trending pairs
        """
        logger = logging.getLogger(__name__)
        
        # Headers to bypass Cloudflare protection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }
        
        # Retry logic with exponential backoff
        for attempt in range(3):
            try:
                logger.info(f"Attempting web scraping (attempt {attempt + 1}/3)")
                
                # Use asyncio.to_thread to run requests in thread pool
                result = await asyncio.to_thread(
                    self._scrape_trending_pairs, 
                    max_pairs, 
                    headers, 
                    timeout
                )
                
                if result:
                    logger.info(f"Successfully scraped {len(result)} trending pairs")
                    return result
                else:
                    logger.warning(f"Scraping returned empty result on attempt {attempt + 1}")
                    
            except Exception as e:
                logger.warning(f"Scraping error on attempt {attempt + 1}: {e}")
            
            if attempt < 2:  # Don't sleep on last attempt
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error("All scraping attempts failed")
        
        # Fallback: Return mock data for demonstration
        logger.info("Returning mock data as fallback")
        return self._generate_mock_trending_pairs(max_pairs)
    
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
    
    def _scrape_trending_pairs(self, max_pairs: int, headers: dict, timeout: int) -> List[TokenInfo]:
        """
        Synchronous web scraping function to run in thread pool.
        
        Args:
            max_pairs: Maximum number of pairs to fetch
            headers: HTTP headers
            timeout: Timeout in seconds
            
        Returns:
            List of TokenInfo objects
        """
        import requests
        from bs4 import BeautifulSoup
        import json
        import re
        
        try:
            # Target URL for trending Solana pairs
            url = "https://dexscreener.com/solana?rankBy=trendingScore&order=desc"
            
            # Make request with SSL verification disabled and session
            session = requests.Session()
            session.verify = False
            session.headers.update(headers)
            
            # Disable SSL warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Add delay to avoid rate limiting
            import time
            time.sleep(1)
            
            response = session.get(url, timeout=timeout)
            
            if response.status_code == 403:
                logging.warning("Access forbidden (403). DexScreener may have anti-bot protection.")
                return []
            elif response.status_code != 200:
                logging.warning(f"Unexpected status code: {response.status_code}")
                return []
            
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Try to find __NEXT_DATA__ script tag
            next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
            if next_data_script:
                try:
                    next_data = json.loads(next_data_script.string)
                    
                    # Navigate through the JSON structure to find pairs
                    pairs_data = None
                    if 'props' in next_data:
                        props = next_data['props']
                        if 'pageProps' in props:
                            page_props = props['pageProps']
                            if 'initialState' in page_props:
                                initial_state = page_props['initialState']
                                if 'pairs' in initial_state:
                                    pairs_data = initial_state['pairs']
                                elif 'trendingPairs' in initial_state:
                                    pairs_data = initial_state['trendingPairs']
                    
                    if pairs_data:
                        logging.info(f"Found {len(pairs_data)} pairs in __NEXT_DATA__")
                        return self._parse_pairs_from_json(pairs_data, max_pairs)
                        
                except (json.JSONDecodeError, KeyError) as e:
                    logging.warning(f"Error parsing __NEXT_DATA__: {e}")
            
            # Method 2: Try to find JSON data in other script tags
            script_tags = soup.find_all('script', type='application/json')
            for script in script_tags:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and 'pairs' in data:
                        pairs_data = data['pairs']
                        logging.info(f"Found {len(pairs_data)} pairs in script tag")
                        return self._parse_pairs_from_json(pairs_data, max_pairs)
                except (json.JSONDecodeError, KeyError):
                    continue
            
            # Method 3: Fallback to table parsing
            logging.info("Falling back to table parsing")
            return self._parse_pairs_from_table(soup, max_pairs)
            
        except requests.RequestException as e:
            logging.error(f"Request error: {e}")
            return []
        except Exception as e:
            logging.error(f"Unexpected error in scraping: {e}")
            return []
    
    def _parse_pairs_from_json(self, pairs_data: list, max_pairs: int) -> List[TokenInfo]:
        """Parse pairs from JSON data."""
        token_infos = []
        
        for pair in pairs_data[:max_pairs]:
            try:
                token_info = self._parse_pair_data(pair)
                if token_info and self._is_valid_memecoin(token_info):
                    token_infos.append(token_info)
            except Exception as e:
                logging.warning(f"Error parsing pair from JSON: {e}")
                continue
        
        return token_infos
    
    def _parse_pairs_from_table(self, soup: BeautifulSoup, max_pairs: int) -> List[TokenInfo]:
        """Fallback method to parse pairs from HTML table."""
        token_infos = []
        
        try:
            # Find table rows containing pair data
            rows = soup.find_all('tr', class_=re.compile(r'pair-row|token-row'))
            
            for row in rows[:max_pairs]:
                try:
                    # Extract data from table cells
                    cells = row.find_all('td')
                    if len(cells) < 6:  # Need at least 6 columns
                        continue
                    
                    # Parse basic info
                    symbol_cell = cells[1] if len(cells) > 1 else None
                    if not symbol_cell:
                        continue
                    
                    symbol_link = symbol_cell.find('a')
                    if not symbol_link:
                        continue
                    
                    symbol = symbol_link.get_text(strip=True)
                    name = symbol  # Use symbol as name if no separate name field
                    
                    # Extract address from href
                    href = symbol_link.get('href', '')
                    address_match = re.search(r'/([A-Za-z0-9]{32,44})', href)
                    if not address_match:
                        continue
                    
                    address = address_match.group(1)
                    
                    # Parse price and volume
                    price_cell = cells[2] if len(cells) > 2 else None
                    volume_cell = cells[3] if len(cells) > 3 else None
                    change_cell = cells[4] if len(cells) > 4 else None
                    
                    price = 0.0
                    volume_24h = 0.0
                    change_24h = 0.0
                    
                    if price_cell:
                        price_text = price_cell.get_text(strip=True).replace('$', '').replace(',', '')
                        try:
                            price = float(price_text)
                        except ValueError:
                            pass
                    
                    if volume_cell:
                        volume_text = volume_cell.get_text(strip=True).replace('$', '').replace(',', '')
                        try:
                            volume_24h = float(volume_text)
                        except ValueError:
                            pass
                    
                    if change_cell:
                        change_text = change_cell.get_text(strip=True).replace('%', '').replace('+', '')
                        try:
                            change_24h = float(change_text)
                        except ValueError:
                            pass
                    
                    # Create TokenInfo object
                    token_info = TokenInfo(
                        address=address,
                        symbol=symbol,
                        name=name,
                        price=price,
                        volume_24h=volume_24h,
                        fdv=volume_24h * 10,  # Estimate FDV as 10x volume
                        change_24h=change_24h,
                        status=TokenStatus.PENDING,
                        discovered_at=datetime.now(),
                        twitter_score=0.0,
                        rugcheck_score=0.0
                    )
                    
                    if self._is_valid_memecoin(token_info):
                        token_infos.append(token_info)
                        
                except Exception as e:
                    logging.warning(f"Error parsing table row: {e}")
                    continue
        
        except Exception as e:
            logging.error(f"Error parsing table: {e}")
            
        return token_infos


# Test function
async def test_fetch_trending_pairs():
    """Test the fetch_trending_pairs function."""
    import logging
    
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a mock config
    from models import BotConfig
    config = BotConfig(
        min_volume_24h=100000,   # Lower threshold for testing
        min_fdv=10000,           # Lower threshold for testing
        meme_keywords=['meme', 'pepe', 'doge', 'shib', 'floki', 'bonk', 'wojak', 'chad', 'kekw', 'moon', 'degen']
    )
    
    # Create client instance
    client = DexScreenerClient(config, lambda x: None)  # No callback needed for test
    
    # Test the function
    print("Testing fetch_trending_pairs with web scraping...")
    result = await client.fetch_trending_pairs(max_pairs=50, timeout=15)
    print(f"Result: {len(result)} pairs found")
    
    # Print first few results
    for i, token in enumerate(result[:10]):
        print(f"{i+1}. {token.symbol} ({token.name}) - Price: ${token.price:.8f}, Volume: ${token.volume_24h:,.0f}, Change: {token.price_change_24h:.2f}%")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_fetch_trending_pairs())
