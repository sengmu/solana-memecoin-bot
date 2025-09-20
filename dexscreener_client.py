"""
DexScreener WebSocket client for discovering trending Solana memecoins.
"""

import asyncio
import json
import logging
import websockets
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
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
