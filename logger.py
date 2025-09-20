"""
Logging and error handling utilities for the memecoin trading bot.
"""

import logging
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from models import Trade, TokenInfo, TradingStats, BotConfig


class TradeLogger:
    """Specialized logger for trading activities."""
    
    def __init__(self, config: BotConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.trades_file = "trades.json"
        self.stats_file = "trading_stats.json"
        
        # Setup logging
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler
        if self.config.log_to_file:
            file_handler = logging.FileHandler(
                log_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler.setLevel(log_level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            
        # Configure all loggers
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        root_logger.handlers.clear()
        root_logger.addHandler(console_handler)
        
        if self.config.log_to_file:
            root_logger.addHandler(file_handler)
            
    def log_trade(self, trade: Trade):
        """Log a trade to both console and file."""
        try:
            # Console logging
            status = "SUCCESS" if trade.success else "FAILED"
            self.logger.info(
                f"TRADE {status}: {trade.trade_type.value.upper()} {trade.amount:.6f} "
                f"tokens at {trade.price:.8f} SOL (TX: {trade.tx_hash})"
            )
            
            if not trade.success and trade.error_message:
                self.logger.error(f"Trade error: {trade.error_message}")
                
            # File logging
            self._append_to_trades_file(trade)
            
        except Exception as e:
            self.logger.error(f"Error logging trade: {e}")
            
    def log_token_discovery(self, token: TokenInfo):
        """Log token discovery."""
        try:
            self.logger.info(
                f"TOKEN DISCOVERED: {token.symbol} ({token.address}) - "
                f"Price: ${token.price:.8f}, Volume: ${token.volume_24h:,.0f}, "
                f"FDV: ${token.fdv:,.0f}"
            )
        except Exception as e:
            self.logger.error(f"Error logging token discovery: {e}")
            
    def log_analysis_result(self, token: TokenInfo, twitter_score: float, rugcheck_score: str, confidence: float):
        """Log analysis results for a token."""
        try:
            self.logger.info(
                f"ANALYSIS COMPLETE: {token.symbol} - "
                f"Twitter: {twitter_score:.1f}/100, RugCheck: {rugcheck_score}, "
                f"Confidence: {confidence:.1f}%"
            )
        except Exception as e:
            self.logger.error(f"Error logging analysis result: {e}")
            
    def log_portfolio_change(self, snapshot: Dict[str, Any]):
        """Log portfolio changes."""
        try:
            new_count = len(snapshot.get('new_tokens', []))
            removed_count = len(snapshot.get('removed_tokens', []))
            total_value = snapshot.get('total_value_usd', 0)
            
            self.logger.info(
                f"PORTFOLIO UPDATE: Value: ${total_value:,.2f}, "
                f"New tokens: {new_count}, Removed: {removed_count}"
            )
        except Exception as e:
            self.logger.error(f"Error logging portfolio change: {e}")
            
    def log_error(self, error: Exception, context: str = ""):
        """Log errors with context."""
        try:
            error_msg = f"ERROR in {context}: {str(error)}" if context else f"ERROR: {str(error)}"
            self.logger.error(error_msg, exc_info=True)
        except Exception as e:
            print(f"Failed to log error: {e}")
            
    def log_warning(self, message: str, context: str = ""):
        """Log warnings with context."""
        try:
            warning_msg = f"WARNING in {context}: {message}" if context else f"WARNING: {message}"
            self.logger.warning(warning_msg)
        except Exception as e:
            print(f"Failed to log warning: {e}")
            
    def log_info(self, message: str, context: str = ""):
        """Log info messages with context."""
        try:
            info_msg = f"INFO in {context}: {message}" if context else f"INFO: {message}"
            self.logger.info(info_msg)
        except Exception as e:
            print(f"Failed to log info: {e}")
            
    def _append_to_trades_file(self, trade: Trade):
        """Append trade to trades.json file."""
        try:
            # Load existing trades
            trades = []
            if os.path.exists(self.trades_file):
                try:
                    with open(self.trades_file, 'r') as f:
                        trades = json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    trades = []
                    
            # Add new trade
            trades.append(trade.to_dict())
            
            # Save updated trades
            with open(self.trades_file, 'w') as f:
                json.dump(trades, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving trade to file: {e}")
            
    def save_trading_stats(self, stats: TradingStats):
        """Save trading statistics to file."""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats.to_dict(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving trading stats: {e}")
            
    def load_trading_stats(self) -> TradingStats:
        """Load trading statistics from file."""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    return TradingStats(**data)
        except Exception as e:
            self.logger.error(f"Error loading trading stats: {e}")
            
        return TradingStats()
        
    def get_trade_history(self, limit: Optional[int] = None) -> list[Dict[str, Any]]:
        """Get trade history from file."""
        try:
            if os.path.exists(self.trades_file):
                with open(self.trades_file, 'r') as f:
                    trades = json.load(f)
                    if limit:
                        return trades[-limit:]
                    return trades
        except Exception as e:
            self.logger.error(f"Error loading trade history: {e}")
            
        return []
        
    def cleanup_old_logs(self, days: int = 7):
        """Clean up old log files."""
        try:
            log_dir = Path("logs")
            if log_dir.exists():
                cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
                
                for log_file in log_dir.glob("*.log"):
                    if log_file.stat().st_mtime < cutoff_date:
                        log_file.unlink()
                        self.logger.info(f"Cleaned up old log file: {log_file}")
                        
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")


class ErrorHandler:
    """Centralized error handling for the bot."""
    
    def __init__(self, logger: TradeLogger):
        self.logger = logger
        
    def handle_network_error(self, error: Exception, context: str = "") -> bool:
        """Handle network-related errors."""
        try:
            error_str = str(error).lower()
            
            if any(keyword in error_str for keyword in ['timeout', 'connection', 'network', 'unreachable']):
                self.logger.log_warning(f"Network error: {error}", context)
                return True  # Retryable
            elif 'rate limit' in error_str or 'too many requests' in error_str:
                self.logger.log_warning(f"Rate limit error: {error}", context)
                return True  # Retryable with delay
            else:
                self.logger.log_error(error, context)
                return False  # Not retryable
                
        except Exception as e:
            self.logger.log_error(e, "ErrorHandler.handle_network_error")
            return False
            
    def handle_trading_error(self, error: Exception, context: str = "") -> bool:
        """Handle trading-related errors."""
        try:
            error_str = str(error).lower()
            
            if any(keyword in error_str for keyword in ['insufficient', 'balance', 'funds']):
                self.logger.log_warning(f"Insufficient funds: {error}", context)
                return False  # Not retryable
            elif any(keyword in error_str for keyword in ['slippage', 'price', 'quote']):
                self.logger.log_warning(f"Price/slippage error: {error}", context)
                return True  # Retryable
            elif any(keyword in error_str for keyword in ['transaction', 'failed', 'rejected']):
                self.logger.log_warning(f"Transaction error: {error}", context)
                return True  # Retryable
            else:
                self.logger.log_error(error, context)
                return False  # Not retryable
                
        except Exception as e:
            self.logger.log_error(e, "ErrorHandler.handle_trading_error")
            return False
            
    def handle_analysis_error(self, error: Exception, context: str = "") -> bool:
        """Handle analysis-related errors."""
        try:
            error_str = str(error).lower()
            
            if any(keyword in error_str for keyword in ['timeout', 'connection', 'network']):
                self.logger.log_warning(f"Analysis network error: {error}", context)
                return True  # Retryable
            elif any(keyword in error_str for keyword in ['not found', '404', 'invalid']):
                self.logger.log_warning(f"Analysis data not found: {error}", context)
                return False  # Not retryable
            else:
                self.logger.log_error(error, context)
                return False  # Not retryable
                
        except Exception as e:
            self.logger.log_error(e, "ErrorHandler.handle_analysis_error")
            return False
            
    def should_retry(self, error: Exception, context: str = "", max_retries: int = 3) -> bool:
        """Determine if an operation should be retried."""
        try:
            if 'network' in context.lower():
                return self.handle_network_error(error, context)
            elif 'trading' in context.lower():
                return self.handle_trading_error(error, context)
            elif 'analysis' in context.lower():
                return self.handle_analysis_error(error, context)
            else:
                # Generic error handling
                error_str = str(error).lower()
                if any(keyword in error_str for keyword in ['timeout', 'connection', 'temporary']):
                    return True
                return False
                
        except Exception as e:
            self.logger.log_error(e, "ErrorHandler.should_retry")
            return False


def setup_bot_logging(config: BotConfig) -> tuple[TradeLogger, ErrorHandler]:
    """Setup logging and error handling for the bot."""
    logger = TradeLogger(config)
    error_handler = ErrorHandler(logger)
    
    return logger, error_handler
