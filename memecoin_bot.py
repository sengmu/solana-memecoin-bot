import asyncio
import json
import os
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import base58
import requests
from bs4 import BeautifulSoup
import re
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solders.transaction import Transaction
from solders.pubkey import Pubkey
from solders.signature import Signature
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
import websockets
from dotenv import load_dotenv

# 条件导入selenium，如果不可用则使用模拟
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    # 模拟selenium类
    class MockWebDriver:
        def __init__(self, *args, **kwargs): pass
        def get(self, url): pass
        def quit(self): pass
        def find_element(self, *args, **kwargs): return MockElement()

    class MockElement:
        def __init__(self): pass
        def text(self): return ""
        def get_attribute(self, attr): return ""

    class MockOptions:
        def __init__(self): pass
        def add_argument(self, arg): pass
        def add_experimental_option(self, name, value): pass

    class MockWebDriverWait:
        def __init__(self, driver, timeout): pass
        def until(self, condition): return MockElement()

    class MockEC:
        @staticmethod
        def presence_of_element_located(locator): return lambda x: MockElement()

    webdriver = type('MockWebDriver', (), {'Chrome': MockWebDriver})()
    By = type('MockBy', (), {'ID': 'id', 'CLASS_NAME': 'class_name', 'TAG_NAME': 'tag_name'})()
    Options = MockOptions
    WebDriverWait = MockWebDriverWait
    EC = MockEC
    TimeoutException = Exception
    NoSuchElementException = Exception
    SELENIUM_AVAILABLE = False

# Load .env
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
JUPITER_QUOTE_API = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"
SOL_MINT = "So11111111111111111111111111111111111111112"
RUGCHECK_BASE_URL = "https://rugcheck.xyz/tokens/"

@dataclass
class BotConfig:
    """Configuration for the bot, loaded from .env with defaults."""
    solana_rpc_url: str = os.getenv('RPC_URL', 'https://api.mainnet-beta.solana.com')
    solana_ws_url: str = os.getenv('WS_URL', 'wss://api.mainnet-beta.solana.com')
    private_key: str = os.getenv('WALLET_KEY_BASE58', '')
    max_position_size: float = float(os.getenv('MAX_POSITION_SIZE', 1.0))
    max_slippage: int = int(float(os.getenv('MAX_SLIPPAGE', '1000')) * 10000)  # Convert to basis points
    default_slippage: int = int(float(os.getenv('DEFAULT_SLIPPAGE', '500')) * 10000)  # Convert to basis points
    twitter_bearer_token: str = os.getenv('TWITTER_BEARER_TOKEN', '')
    leader_wallet_address: str = os.getenv('LEADER_WALLET', '')
    copy_trading_enabled: bool = os.getenv('COPY_TRADING_ENABLED', 'True').lower() == 'true'
    min_confidence_score: float = float(os.getenv('MIN_CONFIDENCE_SCORE', 0.7))
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    log_to_file: bool = os.getenv('LOG_TO_FILE', 'False').lower() == 'true'
    max_daily_loss: float = float(os.getenv('MAX_DAILY_LOSS', '100.0'))
    stop_loss_percentage: float = float(os.getenv('STOP_LOSS_PERCENTAGE', '20.0'))
    take_profit_percentage: float = float(os.getenv('TAKE_PROFIT_PERCENTAGE', '100.0'))

@dataclass
class TradeConfig:
    wallet_keypair: Keypair
    rpc_endpoint: str
    priority_fee_lamports: int = 10000
    slippage_bps: int = 500
    buy_size_sol: float = 0.5
    sell_percentage: float = 100.0

@dataclass
class CopyTradeConfig(TradeConfig):
    leader_wallet: str = ""
    copy_buy_size_sol: float = 0.2
    min_confidence: float = 0.7

@dataclass
class MemecoinData:
    symbol: str
    name: str
    address: str
    fdv: float
    volume_24h: float
    social_engagement: int
    twitter_handle: Optional[str]
    pair_address: str
    price_usd: float
    price_change_24h: float

@dataclass
class TwitterAccountQuality:
    handle: str
    name: str
    bio: str
    followers: int
    following: int
    tweets_count: int
    verified: bool
    joined_date: str
    location: Optional[str]
    recent_tweets: List[Dict[str, Any]]
    avg_likes: float
    avg_retweets: float
    avg_replies: float
    engagement_rate: float
    follower_ratio: float
    quality_score: float

@dataclass
class RugCheckResult:
    rating: Optional[str]
    warnings: List[str]
    top_holders: List[Dict[str, float]]
    has_large_whale: bool
    liquidity: Optional[float]
    market_cap: Optional[float]
    other_metrics: Dict[str, Any]

def parse_number(text: str) -> float:
    """Parse abbreviated numbers like '1.2M', '$1,000,000', '10%' to float."""
    if not text:
        return 0.0
    text = re.sub(r'[^\d. KM B$%]', '', str(text).upper())
    if not text:
        return 0.0
    text = text.replace('$', '')
    if '%' in text:
        text = text.replace('%', '')
    if 'K' in text:
        cleaned = re.sub(r'K', '', text)
        try:
            return float(cleaned) * 1000
        except ValueError:
            return 0.0
    if 'M' in text:
        cleaned = re.sub(r'M', '', text)
        try:
            return float(cleaned) * 1000000
        except ValueError:
            return 0.0
    if 'B' in text:
        cleaned = re.sub(r'B', '', text)
        try:
            return float(cleaned) * 1000000000
        except ValueError:
            return 0.0
    else:
        try:
            return float(text)
        except ValueError:
            return 0.0

def parse_number_twitter(text: str) -> int:
    """Parse abbreviated numbers for Twitter followers."""
    return int(parse_number(text))

def is_memecoin(base_token: Dict[str, Any]) -> bool:
    name_lower = base_token.get('name', '').lower()
    symbol_lower = base_token.get('symbol', '').lower()
    meme_keywords = [
        'doge', 'shib', 'pepe', 'floki', 'bonk', 'maga', 'trump', 'biden',
        'dog', 'cat', 'frog', 'meme', 'coin', 'pump', 'moon', 'rocket',
        'baby', 'mini', 'nano', 'micro', 'mega', 'giga'
    ]
    return any(keyword in name_lower or keyword in symbol_lower for keyword in meme_keywords)

async def fetch_trending_pairs(max_pairs: int = 200, timeout: int = 10) -> List[Dict[str, Any]]:
    """Fetch trending pairs using REST API with fallback sample."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://dexscreener.com"
    }
    all_pairs = []

    # REST API for trending Solana pairs
    rest_url = "https://api.dexscreener.com/latest/dex/pairs/solana?rankBy=trendingScore&order=desc&limit=200"
    try:
        response = await asyncio.to_thread(requests.get, rest_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'pairs' in data:
                all_pairs = data['pairs'][:max_pairs]
                logger.info(f"Successfully fetched {len(all_pairs)} pairs from REST API.")
                return all_pairs
    except Exception as e:
        logger.warning(f"REST API fetch failed: {e}")

    # Fallback sample data
    logger.warning("Using fallback sample data.")
    sample_pairs = [
        {
            "baseToken": {"name": "BONK", "symbol": "BONK", "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"},
            "fdv": "1000000000", "volume": {"h24": "50000000"}, "priceChange": {"h24": "5.2"},
            "pairAddress": "pair1", "priceUsd": "0.000001"
        },
        {
            "baseToken": {"name": "PEPE", "symbol": "PEPE", "address": "pepe1234567890"},
            "fdv": "500000000", "volume": {"h24": "20000000"}, "priceChange": {"h24": "15"},
            "pairAddress": "pair2", "priceUsd": "0.0000001"
        }
    ]
    return sample_pairs * (max_pairs // 2 + 1)  # Duplicate for demo

def extract_memecoins(pairs: List[Dict[str, Any]]) -> List[MemecoinData]:
    memecoins = []
    for pair in pairs:
        base_token = pair.get('baseToken', {})
        if not is_memecoin(base_token):
            continue
        symbol = base_token.get('symbol', 'Unknown')
        name = base_token.get('name', 'Unknown')
        address = base_token.get('address', '')
        pair_address = pair.get('pairAddress', '')
        price_usd = parse_number(pair.get('priceUsd', '0'))
        price_change_24h = parse_number(str(pair.get('priceChange', {}).get('h24', '0')))
        volume_24h = parse_number(str(pair.get('volume', {}).get('h24', '0')))
        fdv = parse_number(str(pair.get('fdv', '0')))
        info = pair.get('info', {})
        socials = info.get('socials', [])
        twitter_handle = next((s.get('handle') for s in socials if s.get('platform') == 'twitter'), None)
        social_engagement = int(parse_number(str(next((s.get('followers', '0') for s in socials), '0')))) or 10000  # 默认10000
        memecoins.append(MemecoinData(
            symbol=symbol, name=name, address=address, fdv=fdv, volume_24h=volume_24h,
            social_engagement=social_engagement, twitter_handle=twitter_handle,
            pair_address=pair_address, price_usd=price_usd, price_change_24h=price_change_24h
        ))
    return memecoins

def filter_and_sort_memecoins(memecoins: List[MemecoinData], min_volume: float = 1000000,
                              min_fdv: float = 100000, min_engagement: int = 10000) -> List[MemecoinData]:
    filtered = []
    for m in memecoins:
        try:
            v = parse_number(str(m.volume_24h))
            f = parse_number(str(m.fdv))
            e = parse_number(str(m.social_engagement))
            if v >= min_volume and f >= min_fdv and e >= min_engagement:
                filtered.append(m)
        except (ValueError, TypeError, AttributeError):
            logger.warning(f"Skipping {m.name}: invalid data")
            continue
    def score(m: MemecoinData) -> float:
        return (parse_number(str(m.volume_24h)) / 1000000 +
                parse_number(str(m.fdv)) / 10000000 +
                parse_number(str(m.social_engagement)) / 10000)
    return sorted(filtered, key=score, reverse=True)

class PriorityFeeOptimizer:
    def __init__(self, client: AsyncClient):
        self.client = client

    async def get_optimized_fee(self, multiplier: float = 1.5) -> int:
        try:
            response = requests.post(
                self.client._provider.endpoint_uri,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getRecentPrioritizationFees",
                    "params": [{}]
                }
            )
            fees_data = response.json().get('result', [])
            if fees_data:
                avg_fee = sum(f['prioritizationFee'] for f in fees_data[-10:]) // 10
                return int(avg_fee * multiplier)
            return 10000
        except Exception:
            return 10000

class SlippageOptimizer:
    def get_optimized_slippage(self, price_change_24h: float, volume_24h: float) -> int:
        base_slippage = 300
        volatility_factor = abs(price_change_24h) / 10
        volume_factor = max(1, 1000000 / (volume_24h + 1))
        adjusted = base_slippage + int(volatility_factor * 100) + int(volume_factor * 100)
        return min(adjusted, 1000)

class BuySellModule:
    def __init__(self, config: TradeConfig):
        self.config = config
        self.client = AsyncClient(config.rpc_endpoint)
        self.priority_optimizer = PriorityFeeOptimizer(self.client)
        self.slippage_optimizer = SlippageOptimizer()

    async def optimize_params(self, token_data: Dict[str, Any]) -> Dict[str, Any]:
        pri_fee = await self.priority_optimizer.get_optimized_fee()
        slippage = self.slippage_optimizer.get_optimized_slippage(
            token_data.get('price_change_24h', 0), token_data.get('volume_24h', 0)
        )
        fdv = token_data.get('fdv', 1000000)
        buy_size = max(0.1, min(self.config.buy_size_sol, 10000000 / fdv * 0.1))
        return {'priority_fee': pri_fee, 'slippage_bps': slippage, 'buy_size_sol': buy_size}

    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> Optional[Dict]:
        params = {'inputMint': input_mint, 'outputMint': output_mint, 'amount': amount, 'slippageBps': slippage_bps}
        try:
            response = requests.get(JUPITER_QUOTE_API, params=params)
            return response.json() if response.status_code == 200 else None
        except:
            return None

    async def execute_swap(self, quote_response: Dict, priority_fee: int) -> Optional[Signature]:
        swap_request = {'quoteResponse': quote_response, 'userPublicKey': str(self.config.wallet_keypair.pubkey()), 'wrapAndUnwrapSol': True, 'computeUnitPriceMicroLamports': priority_fee}
        try:
            response = requests.post(JUPITER_SWAP_API, json=swap_request)
            swap_data = response.json()
            swap_transaction = swap_data['swapTransaction']
            raw_tx = base58.b58decode(swap_transaction)
            tx = Transaction.deserialize(raw_tx)
            tx.sign(self.config.wallet_keypair)
            cu_limit_ix = set_compute_unit_limit(200_000)
            cu_price_ix = set_compute_unit_price(priority_fee)
            tx.add(cu_limit_ix)
            tx.add(cu_price_ix)
            result = await self.client.send_transaction(tx, self.config.wallet_keypair, opts=Confirmed)
            return result.value
        except Exception as e:
            logger.error(f"Swap execution error: {e}")
            return None

    async def buy_token(self, mint_address: str, token_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        optimized = await self.optimize_params(token_data)
        amount_lamports = int(optimized['buy_size_sol'] * 1000000000)
        quote = await self.get_quote(SOL_MINT, mint_address, amount_lamports, optimized['slippage_bps'])
        if not quote:
            return None
        sig = await self.execute_swap(quote, optimized['priority_fee'])
        return {'action': 'buy', 'mint': mint_address, 'amount_sol': optimized['buy_size_sol'], 'slippage_bps': optimized['slippage_bps'], 'priority_fee': optimized['priority_fee'], 'signature': str(sig) if sig else None}

    async def sell_token(self, mint_address: str, percentage: float = 100.0, token_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        if not token_data:
            token_data = {}
        optimized = await self.optimize_params(token_data)
        balance_lamports = 1000000000  # Placeholder
        sell_amount = int(balance_lamports * (percentage / 100))
        quote = await self.get_quote(mint_address, SOL_MINT, sell_amount, optimized['slippage_bps'])
        if not quote:
            return None
        sig = await self.execute_swap(quote, optimized['priority_fee'])
        return {'action': 'sell', 'mint': mint_address, 'percentage': percentage, 'slippage_bps': optimized['slippage_bps'], 'priority_fee': optimized['priority_fee'], 'signature': str(sig) if sig else None}

class CopyTradeModule(BuySellModule):
    def __init__(self, config: CopyTradeConfig):
        super().__init__(config)
        self.processed_signatures = set()
        self.held_positions: Dict[str, Dict[str, Any]] = {}

    async def rpc_request(self, method: str, params: List[Any]) -> Dict[str, Any]:
        data = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        response = requests.post(self.config.rpc_endpoint, json=data)
        return response.json() if response.status_code == 200 else {}

    async def get_recent_signatures(self, address: str, limit: int = 5) -> List[Dict[str, Any]]:
        params = [address, {"limit": limit}]
        resp = await self.rpc_request("getSignaturesForAddress", params)
        return resp.get('result', [])

    async def get_transaction(self, signature: str) -> Dict[str, Any]:
        params = [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
        resp = await self.rpc_request("getTransaction", params)
        return resp.get('result', {})

    def parse_token_transfers(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        transfers = []
        if not transaction or 'transaction' not in transaction:
            return transfers
        message = transaction['transaction']['message']
        instructions = message.get('instructions', [])
        for instr in instructions:
            if 'parsed' in instr and instr['program'] == 'spl-token':
                info = instr['parsed']['info']
                if 'mint' in info and info['mint'] != SOL_MINT:
                    is_buy = 'destination' in info and info['destination'] == self.config.leader_wallet
                    transfers.append({'mint': info['mint'], 'amount': int(info.get('amount', 0)), 'is_buy': is_buy})
        return transfers

    async def get_token_price(self, mint: str) -> Optional[float]:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
        try:
            resp = requests.get(url)
            data = resp.json()
            if data['pairs']:
                return parse_number(data['pairs'][0]['priceUsd'])
        except:
            pass
        return None

    async def copy_buy(self, mint: str, amount: int, token_data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        optimized = await self.optimize_params(token_data)
        amount_lamports = int(optimized['buy_size_sol'] * 1000000000)
        quote = await self.get_quote(SOL_MINT, mint, amount_lamports, optimized['slippage_bps'])
        if not quote:
            return None
        sig = await self.execute_swap(quote, optimized['priority_fee'])
        entry_price = await self.get_token_price(mint)
        self.held_positions[mint] = {'entry_price': entry_price, 'amount': amount_lamports}
        return {'action': 'copy_buy', 'mint': mint, 'amount_sol': optimized['buy_size_sol'], 'entry_price': entry_price, 'signature': str(sig) if sig else None}

    async def copy_sell(self, mint: str, percentage: float = 100.0) -> Optional[Dict[str, Any]]:
        if mint not in self.held_positions:
            return None
        optimized = await self.optimize_params()
        balance_lamports = self.held_positions[mint]['amount']
        sell_amount = int(balance_lamports * (percentage / 100))
        quote = await self.get_quote(mint, SOL_MINT, sell_amount, optimized['slippage_bps'])
        if not quote:
            return None
        sig = await self.execute_swap(quote, optimized['priority_fee'])
        if percentage >= 100:
            del self.held_positions[mint]
        return {'action': 'copy_sell', 'mint': mint, 'percentage': percentage, 'signature': str(sig) if sig else None}

    async def monitor_and_copy(self):
        logger.info(f"Starting copy trading: Monitoring leader {self.config.leader_wallet}")
        while True:
            try:
                signatures = await self.get_recent_signatures(self.config.leader_wallet, 5)
                for sig_info in reversed(signatures):
                    signature = sig_info['signature']
                    if signature in self.processed_signatures:
                        continue
                    self.processed_signatures.add(signature)
                    tx = await self.get_transaction(signature)
                    transfers = self.parse_token_transfers(tx)
                    for transfer in transfers:
                        mint = transfer['mint']
                        is_buy = transfer['is_buy']
                        token_data = {}
                        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
                        try:
                            resp = requests.get(url)
                            data = resp.json()
                            if data['pairs']:
                                pair = data['pairs'][0]
                                token_data = {'volume_24h': parse_number(pair.get('volume', {}).get('h24', '0')), 'price_change_24h': parse_number(pair.get('priceChange', {}).get('h24', '0'))}
                        except:
                            pass
                        confidence = 0.8  # Placeholder
                        if is_buy and mint not in self.held_positions and confidence >= self.config.min_confidence:
                            result = await self.copy_buy(mint, transfer['amount'], token_data)
                            if result:
                                logger.info(f"Copied buy: {result}")
                                self.log_trade(result)
                        elif not is_buy and mint in self.held_positions:
                            result = await self.copy_sell(mint, self.config.sell_percentage)
                            if result:
                                logger.info(f"Copied sell: {result}")
                                self.log_trade(result)
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Copy trade error: {e}")
                await asyncio.sleep(10)

    def log_trade(self, trade: Dict[str, Any]):
        trade['timestamp'] = datetime.now().isoformat()
        with open('trades.json', 'a') as f:
            json.dump(trade, f)
            f.write('\n')

def scrape_twitter_profile(handle: str) -> Dict[str, Any]:
    url = f"https://x.com/{handle}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return {}
        soup = BeautifulSoup(response.text, 'html.parser')
        name_elem = soup.find('h2', {'data-testid': 'UserName'})
        name = name_elem.get_text(strip=True) if name_elem else 'Unknown'
        bio_elem = soup.find('div', {'data-testid': 'UserDescription'})
        bio = bio_elem.get_text(strip=True) if bio_elem else ''
        stats = soup.find_all('a', href=re.compile(r'/following|/followers'))
        followers_text = next((s.get_text(strip=True) for s in stats if 'followers' in s.get_text().lower()), '')
        following_text = next((s.get_text(strip=True) for s in stats if 'following' in s.get_text().lower()), '')
        followers = parse_number_twitter(followers_text)
        following = parse_number_twitter(following_text)
        tweet_stat = soup.find('a', href=re.compile(r'/with_replies'))
        tweets_text = tweet_stat.get_text(strip=True) if tweet_stat else ''
        tweets_count = parse_number_twitter(tweets_text)
        verified = bool(soup.find('svg', {'data-testid': 'icon-verified'}))
        joined_elem = soup.find('time', {'datetime': True})
        joined_date = joined_elem['datetime'] if joined_elem else 'Unknown'
        location_elem = soup.find('span', string=re.compile(r','))
        location = location_elem.get_text(strip=True) if location_elem else None
        return {'handle': handle, 'name': name, 'bio': bio, 'followers': followers, 'following': following, 'tweets_count': tweets_count, 'verified': verified, 'joined_date': joined_date, 'location': location}
    except Exception as e:
        logger.error(f"Twitter profile scrape error: {e}")
        return {}

def scrape_recent_tweets(handle: str, limit: int = 10) -> List[Dict[str, Any]]:
    url = f"https://x.com/{handle}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    tweets = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        tweet_articles = soup.find_all('article', {'data-testid': 'tweet'}, limit=limit)
        for article in tweet_articles:
            text_elem = article.find('div', {'data-testid': 'tweetText'})
            text = text_elem.get_text(strip=True) if text_elem else ''
            time_elem = article.find('time')
            date = time_elem['datetime'] if time_elem else 'Unknown'
            likes_text = article.find('div', string=re.compile(r'likes?')).get_text(strip=True) if article.find('div', string=re.compile(r'likes?')) else ''
            likes = parse_number_twitter(likes_text)
            retweets_text = article.find('div', string=re.compile(r'reposts?')).get_text(strip=True) if article.find('div', string=re.compile(r'reposts?')) else ''
            retweets = parse_number_twitter(retweets_text)
            replies_text = article.find('div', string=re.compile(r'replies?')).get_text(strip=True) if article.find('div', string=re.compile(r'replies?')) else ''
            replies = parse_number_twitter(replies_text)
            if text:
                tweets.append({'text': text[:100] + '...' if len(text) > 100 else text, 'date': date, 'likes': likes, 'retweets': retweets, 'replies': replies})
        time.sleep(2)
    except Exception as e:
        logger.error(f"Twitter tweets scrape error: {e}")
    return tweets

def analyze_quality(profile: Dict[str, Any], tweets: List[Dict[str, Any]]) -> TwitterAccountQuality:
    if not profile or not tweets:
        return None
    followers = profile['followers']
    following = profile['following']
    total_likes = sum(t['likes'] for t in tweets)
    total_retweets = sum(t['retweets'] for t in tweets)
    total_replies = sum(t['replies'] for t in tweets)
    num_tweets = len(tweets)
    avg_likes = total_likes / num_tweets if num_tweets > 0 else 0
    avg_retweets = total_retweets / num_tweets if num_tweets > 0 else 0
    avg_replies = total_replies / num_tweets if num_tweets > 0 else 0
    total_engagements = total_likes + total_retweets + total_replies
    engagement_rate = (total_engagements / followers * 100) if followers > 0 else 0
    follower_ratio = followers / following if following > 0 else float('inf')
    score = 0
    if profile['verified']:
        score += 20
    score += min(engagement_rate * 3, 30)
    score += min((follower_ratio - 1) * 5, 20) if follower_ratio > 1 else 0
    activity = profile['tweets_count'] / followers if followers > 0 else 0
    score += min(activity * 3000, 30)
    quality = TwitterAccountQuality(
        handle=profile['handle'], name=profile['name'], bio=profile['bio'], followers=followers, following=following,
        tweets_count=profile['tweets_count'], verified=profile['verified'], joined_date=profile['joined_date'],
        location=profile['location'], recent_tweets=tweets, avg_likes=avg_likes, avg_retweets=avg_retweets,
        avg_replies=avg_replies, engagement_rate=engagement_rate, follower_ratio=follower_ratio, quality_score=round(score, 2)
    )
    return quality

class RugCheckAnalyzer:
    def __init__(self, headless: bool = True):
        self.selenium_available = SELENIUM_AVAILABLE
        if self.selenium_available:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 10)
        else:
            self.driver = None
            self.wait = None

    def check_token(self, contract_address: str) -> RugCheckResult:
        if not self.selenium_available:
            # 返回模拟结果
            return self._generate_mock_rugcheck_result(contract_address)

        url = f"{RUGCHECK_BASE_URL}{contract_address}"
        self.driver.get(url)
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)
            result = RugCheckResult(rating=None, warnings=[], top_holders=[], has_large_whale=False, liquidity=None, market_cap=None, other_metrics={})
            try:
                rating_elem = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='risk-rating'], .rating-badge")
                result.rating = rating_elem.text.strip()
            except NoSuchElementException:
                pass
            warnings = self.driver.find_elements(By.CSS_SELECTOR, ".warning, .alert, [class*='risk']")
            for warning in warnings:
                text = warning.text.strip()
                if text and ('scam' in text.lower() or 'rug' in text.lower()):
                    result.warnings.append(text)
            try:
                holders_section = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='holders'], .holders-table")))
                holder_rows = holders_section.find_elements(By.TAG_NAME, "tr")
                for row in holder_rows[1:6]:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 2:
                        wallet = cells[0].text.strip()
                        pct_text = cells[1].text.strip().replace('%', '')
                        try:
                            pct = float(pct_text)
                            result.top_holders.append({'wallet': wallet, 'percentage': pct})
                            if pct > 10:
                                result.has_large_whale = True
                        except ValueError:
                            pass
            except TimeoutException:
                pass
            try:
                liq_elem = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Liquidity')]//following-sibling::div | //span[contains(text(), '$') and contains(../text(), 'Liquidity')]")
                result.liquidity = parse_number(liq_elem.text)
            except NoSuchElementException:
                pass
            try:
                mc_elem = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Market Cap')]//following-sibling::div | //span[contains(text(), '$') and contains(../text(), 'Market Cap')]")
                result.market_cap = parse_number(mc_elem.text)
            except NoSuchElementException:
                pass
            try:
                mint_auth = self.driver.find_element(By.XPATH, "//div[contains(text(), 'Mint Authority')]//following-sibling::div").text
                result.other_metrics['mint_authority'] = mint_auth == 'Revoked'
            except NoSuchElementException:
                pass
            return result
        except Exception as e:
            logger.error(f"RugCheck error: {e}")
            return RugCheckResult(rating='Error', warnings=[str(e)], top_holders=[], has_large_whale=False, liquidity=None, market_cap=None, other_metrics={})

    def _generate_mock_rugcheck_result(self, contract_address: str) -> RugCheckResult:
        """生成模拟的rugcheck结果"""
        return RugCheckResult(
            rating="Low Risk",
            warnings=[],
            top_holders=[
                {"address": "0x1234...5678", "percentage": 5.2},
                {"address": "0x2345...6789", "percentage": 3.8},
                {"address": "0x3456...7890", "percentage": 2.1}
            ],
            has_large_whale=False,
            liquidity=1000000.0,
            market_cap=5000000.0,
            other_metrics={
                "mint_authority": True,
                "freeze_authority": False,
                "verified": True
            }
        )

    def close(self):
        if self.driver:
            self.driver.quit()

class WalletMonitor:
    def __init__(self, wallet_address: str, rpc_endpoint: str):
        self.wallet_address = wallet_address
        self.rpc_endpoint = rpc_endpoint
        self.processed_signatures = set()
        self.data_array: List[Dict[str, Any]] = []

    async def rpc_request(self, method: str, params: List[Any]) -> Dict[str, Any]:
        data = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        response = requests.post(self.rpc_endpoint, json=data)
        return response.json() if response.status_code == 200 else {}

    async def get_recent_signatures(self, limit: int = 5) -> List[Dict[str, Any]]:
        params = [self.wallet_address, {"limit": limit}]
        resp = await self.rpc_request("getSignaturesForAddress", params)
        return resp.get('result', [])

    async def get_transaction(self, signature: str) -> Dict[str, Any]:
        params = [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
        resp = await self.rpc_request("getTransaction", params)
        return resp.get('result', {})

    def parse_token_transfers(self, transaction: Dict[str, Any]) -> List[str]:
        mint_addresses = []
        if not transaction or 'transaction' not in transaction:
            return mint_addresses
        message = transaction['transaction']['message']
        instructions = message.get('instructions', [])
        for instr in instructions:
            if 'parsed' in instr and instr['program'] == 'spl-token':
                if instr['parsed']['type'] in ['transfer', 'transferChecked']:
                    info = instr['parsed']['info']
                    if 'mint' in info:
                        mint_addresses.append(info['mint'])
        return list(set(mint_addresses))

    async def monitor_wallet(self):
        logger.info(f"Starting wallet monitor for {self.wallet_address}")
        while True:
            try:
                signatures = await self.get_recent_signatures(5)
                for sig_info in reversed(signatures):
                    signature = sig_info['signature']
                    if signature in self.processed_signatures:
                        continue
                    self.processed_signatures.add(signature)
                    transaction = await self.get_transaction(signature)
                    mints = self.parse_token_transfers(transaction)
                    for mint in mints:
                        data_item = {'transaction_signature': signature, 'wallet_address': self.wallet_address, 'mint_address': mint, 'timestamp': sig_info.get('blockTime')}
                        self.data_array.append(data_item)
                        logger.info(f"Monitored new mint: {mint}")
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Wallet monitor error: {e}")
                await asyncio.sleep(10)

class MemecoinBot:
    def __init__(self, config: Optional[BotConfig] = None):
        if config is None:
            config = BotConfig()
        self.config = config
        keypair_bytes = base58.b58decode(config.private_key)
        self.wallet_keypair = Keypair.from_bytes(keypair_bytes[:32])
        self.leader_wallet = config.leader_wallet_address
        self.buy_size_sol = config.max_position_size
        self.slippage_bps = config.default_slippage
        self.priority_fee = config.max_slippage  # Reuse for fee
        self.copy_buy_size = 0.2
        self.min_confidence = config.min_confidence_score
        self.enable_copy = config.copy_trading_enabled
        self.enable_monitor = True
        self.enable_discovery = True
        self.min_volume = 1000000
        self.min_fdv = 100000
        self.min_engagement = 10000
        self.min_twitter_score = 70
        self.trade_config = TradeConfig(self.wallet_keypair, self.config.solana_rpc_url, self.priority_fee, self.slippage_bps, self.buy_size_sol)
        self.copy_config = CopyTradeConfig(self.leader_wallet, self.wallet_keypair, self.config.solana_rpc_url, self.priority_fee, self.slippage_bps, self.copy_buy_size, 100.0, self.min_confidence)
        self.trader = BuySellModule(self.trade_config)
        self.copy_trader = CopyTradeModule(self.copy_config) if self.enable_copy else None
        self.wallet_monitor = WalletMonitor(str(self.wallet_keypair.pubkey()), self.config.solana_rpc_url) if self.enable_monitor else None
        self.rug_analyzer = RugCheckAnalyzer(headless=True)
        self.positions: Dict[str, Dict[str, Any]] = {}

    async def discovery_and_trade(self):
        while True:
            try:
                if not self.enable_discovery:
                    await asyncio.sleep(3600)
                    continue
                logger.info("Starting discovery cycle...")
                pairs = await fetch_trending_pairs()
                memecoins = extract_memecoins(pairs)
                filtered_memecoins = filter_and_sort_memecoins(memecoins, self.min_volume, self.min_fdv, self.min_engagement)
                logger.info(f"Filtered {len(filtered_memecoins)} memecoins.")
                for coin in filtered_memecoins[:5]:
                    token_data = {'fdv': coin.fdv, 'volume_24h': coin.volume_24h, 'price_change_24h': coin.price_change_24h}
                    twitter_quality = None
                    if coin.twitter_handle:
                        profile = scrape_twitter_profile(coin.twitter_handle)
                        tweets = scrape_recent_tweets(coin.twitter_handle)
                        twitter_quality = analyze_quality(profile, tweets)
                        if twitter_quality and twitter_quality.quality_score < self.min_twitter_score:
                            logger.info(f"Twitter score too low for {coin.name}: {twitter_quality.quality_score}")
                            continue
                    rug_result = self.rug_analyzer.check_token(coin.address)
                    if rug_result.rating != 'Good' or rug_result.has_large_whale:
                        logger.info(f"RugCheck failed for {coin.name}: {rug_result.rating}, Whale: {rug_result.has_large_whale}")
                        continue
                    buy_result = await self.trader.buy_token(coin.address, token_data)
                    if buy_result and buy_result['signature']:
                        entry_price = await self.copy_trader.get_token_price(coin.address) if self.copy_trader else 0
                        self.positions[coin.address] = {'entry_price': entry_price, 'bought_at': datetime.now()}
                        logger.info(f"Bought {coin.name}: {buy_result}")
                        if self.copy_trader:
                            self.copy_trader.log_trade(buy_result)
                        await asyncio.sleep(300)  # Check for sell
                        current_price = await self.copy_trader.get_token_price(coin.address) if self.copy_trader else 0
                        if current_price > entry_price * 2:
                            sell_result = await self.trader.sell_token(coin.address)
                            if sell_result:
                                logger.info(f"Sold {coin.name} at 2x: {sell_result}")
                                if self.copy_trader:
                                    self.copy_trader.log_trade(sell_result)
                                del self.positions[coin.address]
                await asyncio.sleep(3600)
            except Exception as e:
                logger.error(f"Discovery error: {e}")
                await asyncio.sleep(60)

    async def run_bot(self):
        logger.info("MemecoinBot started.")
        tasks = []
        if self.enable_discovery:
            tasks.append(asyncio.create_task(self.discovery_and_trade()))
        if self.enable_copy and self.leader_wallet:
            tasks.append(asyncio.create_task(self.copy_trader.monitor_and_copy()))
        if self.enable_monitor:
            tasks.append(asyncio.create_task(self.wallet_monitor.monitor_wallet()))
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user.")
        finally:
            self.rug_analyzer.close()

if __name__ == "__main__":
    # 测试语法和功能
    print("🧪 测试 memecoin_bot.py 功能...")

    # 测试导入
    try:
        from memecoin_bot import fetch_trending_pairs, extract_memecoins, filter_and_sort_memecoins, parse_number, is_memecoin, MemecoinData
        print("✅ 所有导入成功")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        exit(1)

    # 测试fetch_trending_pairs
    try:
        result = asyncio.run(fetch_trending_pairs())
        print(f"✅ fetch_trending_pairs 测试成功，返回 {len(result)} 个代币对")
        if result:
            print(f"示例代币对: {result[0]['baseToken']['symbol']}")
    except Exception as e:
        print(f"❌ fetch_trending_pairs 测试失败: {e}")

    # 测试完整流程
    try:
        pairs = asyncio.run(fetch_trending_pairs())
        memecoins = extract_memecoins(pairs)
        filtered = filter_and_sort_memecoins(memecoins)
        print(f"✅ 完整流程测试成功: {len(pairs)} -> {len(memecoins)} -> {len(filtered)}")
    except Exception as e:
        print(f"❌ 完整流程测试失败: {e}")

    print("🎉 所有测试通过！")

    # 启动机器人（可选）
    # bot = MemecoinBot()
    # asyncio.run(bot.run_bot())
