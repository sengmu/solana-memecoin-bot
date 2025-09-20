"""
Data models for the Solana memecoin trading bot.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum
import json
import os


class TradeType(Enum):
    BUY = "buy"
    SELL = "sell"


class TokenStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    APPROVED = "approved"
    REJECTED = "rejected"
    TRADING = "trading"
    SOLD = "sold"


@dataclass
class TokenInfo:
    """Information about a discovered token."""
    address: str
    symbol: str
    name: str
    decimals: int
    price: float
    market_cap: float
    fdv: float
    volume_24h: float
    price_change_24h: float
    liquidity: float
    holders: int
    created_at: datetime
    status: TokenStatus = TokenStatus.PENDING
    twitter_score: Optional[float] = None
    rugcheck_score: Optional[str] = None
    confidence_score: Optional[float] = None
    is_memecoin: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = {
            'address': self.address,
            'symbol': self.symbol,
            'name': self.name,
            'decimals': self.decimals,
            'price': self.price,
            'market_cap': self.market_cap,
            'fdv': self.fdv,
            'volume_24h': self.volume_24h,
            'price_change_24h': self.price_change_24h,
            'liquidity': self.liquidity,
            'holders': self.holders,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'twitter_score': self.twitter_score,
            'rugcheck_score': self.rugcheck_score,
            'confidence_score': self.confidence_score,
            'is_memecoin': self.is_memecoin
        }
        return data


@dataclass
class Trade:
    """Represents a trade transaction."""
    id: str
    token_address: str
    trade_type: TradeType
    amount: float
    price: float
    slippage: float
    priority_fee: float
    tx_hash: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    error_message: Optional[str] = None
    gas_used: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'token_address': self.token_address,
            'trade_type': self.trade_type.value,
            'amount': self.amount,
            'price': self.price,
            'slippage': self.slippage,
            'priority_fee': self.priority_fee,
            'tx_hash': self.tx_hash,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'error_message': self.error_message,
            'gas_used': self.gas_used
        }


@dataclass
class TwitterProfile:
    """Twitter profile information."""
    username: str
    display_name: str
    followers_count: int
    following_count: int
    tweet_count: int
    verified: bool
    created_at: datetime
    bio: str
    profile_score: float = 0.0


@dataclass
class TwitterTweet:
    """Individual tweet information."""
    id: str
    text: str
    created_at: datetime
    retweet_count: int
    like_count: int
    reply_count: int
    engagement_score: float = 0.0


@dataclass
class RugCheckResult:
    """RugCheck analysis result."""
    token_address: str
    rating: str
    liquidity_locked: bool
    ownership_renounced: bool
    whale_percentage: float
    holder_distribution: Dict[str, float]
    contract_verified: bool
    honeypot: bool
    mint_authority: bool
    freeze_authority: bool
    overall_score: float = 0.0


@dataclass
class BotConfig:
    """Bot configuration settings."""
    # Solana Configuration
    solana_rpc_url: str = field(default_factory=lambda: os.getenv('RPC_URL', 'https://api.mainnet-beta.solana.com'))
    solana_ws_url: str = field(default_factory=lambda: os.getenv('WS_URL', 'wss://api.mainnet-beta.solana.com'))
    private_key: str = field(default_factory=lambda: os.getenv('WALLET_KEY_BASE58', ''))
    
    # Trading Configuration
    max_position_size: float = field(default_factory=lambda: float(os.getenv('MAX_POSITION_SIZE', '1.0')))
    min_volume_24h: float = field(default_factory=lambda: float(os.getenv('MIN_VOLUME_24H', '1000000')))
    min_fdv: float = field(default_factory=lambda: float(os.getenv('MIN_FDV', '100000')))
    max_slippage: float = field(default_factory=lambda: float(os.getenv('MAX_SLIPPAGE', '1000')))
    default_slippage: float = field(default_factory=lambda: float(os.getenv('DEFAULT_SLIPPAGE', '500')))
    
    # Twitter Configuration
    twitter_bearer_token: str = field(default_factory=lambda: os.getenv('TWITTER_BEARER_TOKEN', ''))
    
    # Copy Trading
    leader_wallet_address: str = field(default_factory=lambda: os.getenv('LEADER_WALLET_ADDRESS', ''))
    copy_trading_enabled: bool = field(default_factory=lambda: os.getenv('COPY_TRADING_ENABLED', 'true').lower() == 'true')
    min_confidence_score: float = field(default_factory=lambda: float(os.getenv('MIN_CONFIDENCE_SCORE', '0.7')))
    
    # Logging
    log_level: str = field(default_factory=lambda: os.getenv('LOG_LEVEL', 'INFO'))
    log_to_file: bool = field(default_factory=lambda: os.getenv('LOG_TO_FILE', 'false').lower() == 'true')
    
    # Risk Management
    max_daily_loss: float = field(default_factory=lambda: float(os.getenv('MAX_DAILY_LOSS', '100.0')))
    stop_loss_percentage: float = field(default_factory=lambda: float(os.getenv('STOP_LOSS_PERCENTAGE', '20.0')))
    take_profit_percentage: float = field(default_factory=lambda: float(os.getenv('TAKE_PROFIT_PERCENTAGE', '100.0')))
    
    # OpenSolBot 增强配置
    leader_wallets: List[str] = field(default_factory=list)
    copy_ratio: float = 1.0
    geyser_endpoint: Optional[str] = None
    geyser_token: Optional[str] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    helius_api_key: Optional[str] = None
    shyft_api_key: Optional[str] = None
    jupiter_api_key: Optional[str] = None
    raydium_api_key: Optional[str] = None
    
    # Memecoin Keywords
    meme_keywords: List[str] = field(default_factory=lambda: [
        'meme', 'doge', 'shib', 'pepe', 'wojak', 'chad', 'based', 'gm', 'wagmi',
        'diamond', 'hands', 'moon', 'rocket', 'ape', 'monke', 'frog', 'cat',
        'dog', 'inu', 'inu', 'kishu', 'akita', 'floki', 'elon', 'musk'
    ])
    
    @classmethod
    def from_env(cls) -> 'BotConfig':
        """Create config from environment variables using os.getenv."""
        import os
        
        # Required environment variables
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable is required")
        
        return cls(
            solana_rpc_url=os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com'),
            solana_ws_url=os.getenv('SOLANA_WS_URL', 'wss://api.mainnet-beta.solana.com'),
            private_key=private_key,
            max_position_size=float(os.getenv('MAX_POSITION_SIZE', '0.1')),
            min_volume_24h=float(os.getenv('MIN_VOLUME_24H', '1000000')),
            min_fdv=float(os.getenv('MIN_FDV', '100000')),
            max_slippage=float(os.getenv('MAX_SLIPPAGE', '0.05')),
            default_slippage=float(os.getenv('DEFAULT_SLIPPAGE', '0.01')),
            twitter_bearer_token=os.getenv('TWITTER_BEARER_TOKEN', ''),
            leader_wallet_address=os.getenv('LEADER_WALLET_ADDRESS', ''),
            copy_trading_enabled=os.getenv('COPY_TRADING_ENABLED', 'true').lower() == 'true',
            min_confidence_score=float(os.getenv('MIN_CONFIDENCE_SCORE', '70')),
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            log_to_file=os.getenv('LOG_TO_FILE', 'true').lower() == 'true',
            max_daily_loss=float(os.getenv('MAX_DAILY_LOSS', '0.1')),
            stop_loss_percentage=float(os.getenv('STOP_LOSS_PERCENTAGE', '0.2')),
            take_profit_percentage=float(os.getenv('TAKE_PROFIT_PERCENTAGE', '0.5'))
        )


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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_value_usd': self.total_value_usd,
            'sol_balance': self.sol_balance,
            'tokens': {addr: {
                'address': token.address,
                'symbol': token.symbol,
                'name': token.name,
                'balance': token.balance,
                'value_usd': token.value_usd,
                'price': token.price,
                'last_updated': token.last_updated.isoformat()
            } for addr, token in self.tokens.items()},
            'new_tokens': self.new_tokens,
            'removed_tokens': self.removed_tokens
        }


@dataclass
class TradingStats:
    """Trading statistics tracking."""
    total_trades: int = 0
    successful_trades: int = 0
    total_volume: float = 0.0
    total_profit: float = 0.0
    daily_pnl: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    average_hold_time: float = 0.0
    
    def update_win_rate(self):
        """Update win rate based on current stats."""
        if self.total_trades > 0:
            self.win_rate = (self.successful_trades / self.total_trades) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'total_volume': self.total_volume,
            'total_profit': self.total_profit,
            'daily_pnl': self.daily_pnl,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'average_hold_time': self.average_hold_time
        }
