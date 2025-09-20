"""
Main Solana memecoin trading bot class.
"""

import asyncio
import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path

from dotenv import load_dotenv

from models import (
    BotConfig, TokenInfo, Trade, TradeType, TokenStatus, 
    TradingStats, WalletToken, PortfolioSnapshot
)
from dexscreener_client import DexScreenerClient
from twitter_analyzer import TwitterAnalyzer
from rugcheck_analyzer import RugCheckAnalyzer
from jupiter_trader import JupiterTrader
from copy_trader import CopyTrader, LeaderTrade
from wallet_monitor import WalletMonitor
from logger import setup_bot_logging, TradeLogger, ErrorHandler


class MemecoinBot:
    """Main memecoin trading bot class."""
    
    def __init__(self, config_path: str = ".env"):
        """Initialize the memecoin trading bot."""
        # Load configuration
        load_dotenv(config_path)
        self.config = BotConfig.from_env()
        
        # Setup logging and error handling
        self.logger, self.error_handler = setup_bot_logging(self.config)
        
        # Initialize components
        self.jupiter_trader: Optional[JupiterTrader] = None
        self.dexscreener_client: Optional[DexScreenerClient] = None
        self.twitter_analyzer: Optional[TwitterAnalyzer] = None
        self.rugcheck_analyzer: Optional[RugCheckAnalyzer] = None
        self.copy_trader: Optional[CopyTrader] = None
        self.wallet_monitor: Optional[WalletMonitor] = None
        
        # Bot state
        self.running = False
        self.trading_stats = TradingStats()
        self.discovered_tokens: Dict[str, TokenInfo] = {}
        self.active_positions: Dict[str, TokenInfo] = {}
        
        # Load existing stats
        self.trading_stats = self.logger.load_trading_stats()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()
        
    async def initialize(self):
        """Initialize all bot components."""
        try:
            self.logger.log_info("Initializing memecoin trading bot...")
            
            # Initialize Jupiter trader
            self.jupiter_trader = JupiterTrader(self.config)
            await self.jupiter_trader.__aenter__()
            
            # Initialize DexScreener client
            self.dexscreener_client = DexScreenerClient(
                self.config, 
                self._on_token_discovered
            )
            
            # Initialize analyzers
            self.twitter_analyzer = TwitterAnalyzer(self.config)
            self.rugcheck_analyzer = RugCheckAnalyzer(self.config)
            
            # Initialize copy trader
            self.copy_trader = CopyTrader(
                self.config,
                self.jupiter_trader,
                self._on_leader_trade_detected
            )
            await self.copy_trader.__aenter__()
            
            # Initialize wallet monitor
            self.wallet_monitor = WalletMonitor(
                self.config,
                self._on_new_token_in_wallet,
                self._on_portfolio_change
            )
            
            self.logger.log_info("Bot initialization complete")
            
        except Exception as e:
            self.logger.log_error(e, "Bot initialization")
            raise
            
    async def shutdown(self):
        """Shutdown all bot components."""
        try:
            self.logger.log_info("Shutting down memecoin trading bot...")
            
            self.running = False
            
            # Stop all components
            if self.dexscreener_client:
                await self.dexscreener_client.stop()
                
            if self.copy_trader:
                await self.copy_trader.stop_monitoring()
                
            if self.wallet_monitor:
                await self.wallet_monitor.stop_monitoring()
                
            # Close connections
            if self.jupiter_trader:
                await self.jupiter_trader.__aexit__(None, None, None)
                
            if self.copy_trader:
                await self.copy_trader.__aexit__(None, None, None)
                
            # Save final stats
            self.logger.save_trading_stats(self.trading_stats)
            
            self.logger.log_info("Bot shutdown complete")
            
        except Exception as e:
            self.logger.log_error(e, "Bot shutdown")
            
    async def run_bot(self):
        """Main bot execution loop."""
        try:
            self.running = True
            self.logger.log_info("Starting memecoin trading bot...")
            
            # Start all monitoring tasks
            tasks = []
            
            # DexScreener monitoring
            if self.dexscreener_client:
                tasks.append(asyncio.create_task(self.dexscreener_client.start()))
                
            # Copy trading monitoring
            if self.copy_trader and self.config.copy_trading_enabled:
                tasks.append(asyncio.create_task(self.copy_trader.start_monitoring()))
                
            # Wallet monitoring
            if self.wallet_monitor:
                tasks.append(asyncio.create_task(self.wallet_monitor.start_monitoring()))
                
            # Token analysis task
            tasks.append(asyncio.create_task(self._token_analysis_loop()))
            
            # Position management task
            tasks.append(asyncio.create_task(self._position_management_loop()))
            
            # Stats reporting task
            tasks.append(asyncio.create_task(self._stats_reporting_loop()))
            
            # Wait for all tasks
            await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.log_error(e, "Bot main loop")
        finally:
            await self.shutdown()
            
    async def _on_token_discovered(self, token: TokenInfo):
        """Handle newly discovered token."""
        try:
            self.logger.log_token_discovery(token)
            self.discovered_tokens[token.address] = token
            asyncio.create_task(self._analyze_token(token))
        except Exception as e:
            self.logger.log_error(e, "Token discovery handler")
            
    async def _analyze_token(self, token: TokenInfo):
        """Analyze a discovered token."""
        try:
            token.status = TokenStatus.ANALYZING
            self.logger.log_info(f"Starting analysis for {token.symbol}")
            
            # Twitter analysis
            twitter_score = 0.0
            if self.twitter_analyzer:
                try:
                    async with self.twitter_analyzer as analyzer:
                        twitter_score = await analyzer.analyze_token(token)
                        token.twitter_score = twitter_score
                except Exception as e:
                    self.logger.log_error(e, f"Twitter analysis for {token.symbol}")
                    
            # RugCheck analysis
            rugcheck_score = "Unknown"
            if self.rugcheck_analyzer:
                try:
                    rugcheck_result = await self.rugcheck_analyzer.analyze_token(token)
                    if rugcheck_result:
                        rugcheck_score = rugcheck_result.rating
                        token.rugcheck_score = rugcheck_score
                        
                        if not self.rugcheck_analyzer.is_safe_token(rugcheck_result):
                            token.status = TokenStatus.REJECTED
                            self.logger.log_info(f"Token {token.symbol} rejected by RugCheck")
                            return
                except Exception as e:
                    self.logger.log_error(e, f"RugCheck analysis for {token.symbol}")
                    
            # Calculate confidence score
            confidence = self._calculate_confidence_score(token, twitter_score, rugcheck_score)
            token.confidence_score = confidence
            
            # Log analysis results
            self.logger.log_analysis_result(token, twitter_score, rugcheck_score, confidence)
            
            # Decide whether to trade
            if confidence >= self.config.min_confidence_score:
                token.status = TokenStatus.APPROVED
                await self._consider_trading(token)
            else:
                token.status = TokenStatus.REJECTED
                self.logger.log_info(f"Token {token.symbol} rejected due to low confidence: {confidence:.1f}%")
                
        except Exception as e:
            self.logger.log_error(e, f"Token analysis for {token.symbol}")
            token.status = TokenStatus.REJECTED
            
    def _calculate_confidence_score(self, token: TokenInfo, twitter_score: float, rugcheck_score: str) -> float:
        """Calculate overall confidence score for a token."""
        try:
            score = 0.0
            
            # Twitter score (40% weight)
            score += (twitter_score / 100) * 40
            
            # RugCheck score (30% weight)
            rugcheck_scores = {
                "Good": 100, "Excellent": 100, "Safe": 80, "Fair": 60,
                "Poor": 20, "Bad": 0, "Dangerous": 0, "Rug": 0
            }
            rugcheck_value = rugcheck_scores.get(rugcheck_score, 50)
            score += (rugcheck_value / 100) * 30
            
            # Token metrics (30% weight)
            metrics_score = 0
            
            # Volume score
            if token.volume_24h > 10_000_000:
                metrics_score += 30
            elif token.volume_24h > 1_000_000:
                metrics_score += 20
            elif token.volume_24h > 100_000:
                metrics_score += 10
                
            # Liquidity score
            if token.liquidity > 1_000_000:
                metrics_score += 20
            elif token.liquidity > 100_000:
                metrics_score += 15
            elif token.liquidity > 10_000:
                metrics_score += 10
                
            # Holder count score
            if token.holders > 10000:
                metrics_score += 20
            elif token.holders > 1000:
                metrics_score += 15
            elif token.holders > 100:
                metrics_score += 10
                
            # Price stability score
            if abs(token.price_change_24h) < 10:
                metrics_score += 15
            elif abs(token.price_change_24h) < 30:
                metrics_score += 10
            elif abs(token.price_change_24h) < 50:
                metrics_score += 5
                
            score += (metrics_score / 100) * 30
            
            return min(score, 100.0)
            
        except Exception as e:
            self.logger.log_error(e, "Confidence score calculation")
            return 0.0
            
    async def _consider_trading(self, token: TokenInfo):
        """Consider trading a token based on analysis."""
        try:
            if not self.jupiter_trader:
                return
                
            # Check if we already have a position
            if token.address in self.active_positions:
                self.logger.log_info(f"Already have position in {token.symbol}")
                return
                
            # Check available SOL balance
            sol_balance = await self.jupiter_trader.get_sol_balance()
            if sol_balance < 0.01:  # Minimum 0.01 SOL
                self.logger.log_warning("Insufficient SOL balance for trading")
                return
                
            # Calculate position size
            position_size = min(sol_balance * self.config.max_position_size, 1.0)  # Max 1 SOL
            
            # Execute buy order
            self.logger.log_info(f"Executing buy order for {token.symbol}: {position_size:.4f} SOL")
            
            trade = await self.jupiter_trader.buy_token(token, position_size)
            
            if trade and trade.success:
                # Update stats
                self.trading_stats.total_trades += 1
                self.trading_stats.successful_trades += 1
                self.trading_stats.total_volume += trade.amount * trade.price
                
                # Add to active positions
                self.active_positions[token.address] = token
                token.status = TokenStatus.TRADING
                
                self.logger.log_trade(trade)
            else:
                self.logger.log_warning(f"Failed to buy {token.symbol}")
                
        except Exception as e:
            self.logger.log_error(e, f"Trading consideration for {token.symbol}")
            
    async def _on_leader_trade_detected(self, leader_trade: LeaderTrade):
        """Handle detected leader trade for copy trading."""
        try:
            self.logger.log_info(
                f"Leader trade detected: {leader_trade.trade_type.value} "
                f"{leader_trade.token_address} (confidence: {leader_trade.confidence_score:.1f}%)"
            )
            
            # Copy the trade
            if self.copy_trader:
                trade = await self.copy_trader.copy_trade(leader_trade)
                if trade:
                    self.logger.log_trade(trade)
                    
        except Exception as e:
            self.logger.log_error(e, "Leader trade handler")
            
    async def _on_new_token_in_wallet(self, token: WalletToken):
        """Handle new token detected in wallet."""
        try:
            self.logger.log_info(f"New token in wallet: {token.symbol} ({token.address})")
            
            # Add to known tokens if we have the analyzers
            if self.copy_trader:
                # Create TokenInfo from WalletToken
                token_info = TokenInfo(
                    address=token.address,
                    symbol=token.symbol,
                    name=token.name,
                    decimals=9,  # Default
                    price=token.price,
                    market_cap=0,  # Will be updated
                    fdv=0,
                    volume_24h=0,
                    price_change_24h=0,
                    liquidity=0,
                    holders=0,
                    created_at=token.last_updated
                )
                self.copy_trader.add_known_token(token_info)
                
        except Exception as e:
            self.logger.log_error(e, "New token in wallet handler")
            
    async def _on_portfolio_change(self, snapshot: PortfolioSnapshot):
        """Handle portfolio changes."""
        try:
            self.logger.log_portfolio_change(snapshot.to_dict())
            
        except Exception as e:
            self.logger.log_error(e, "Portfolio change handler")
            
    async def _token_analysis_loop(self):
        """Background loop for token analysis."""
        while self.running:
            try:
                # Process pending tokens
                pending_tokens = [
                    token for token in self.discovered_tokens.values()
                    if token.status == TokenStatus.PENDING
                ]
                
                for token in pending_tokens[:5]:  # Process up to 5 at a time
                    await self._analyze_token(token)
                    
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.log_error(e, "Token analysis loop")
                await asyncio.sleep(60)
                
    async def _position_management_loop(self):
        """Background loop for position management."""
        while self.running:
            try:
                # Check stop loss and take profit
                for address, token in list(self.active_positions.items()):
                    await self._check_position_exit(token)
                    
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.log_error(e, "Position management loop")
                await asyncio.sleep(60)
                
    async def _check_position_exit(self, token: TokenInfo):
        """Check if a position should be exited."""
        try:
            if not self.jupiter_trader:
                return
                
            # Get current price (simplified - in practice you'd get real-time price)
            # For now, we'll use a simple time-based exit
            position_age = datetime.now() - token.created_at
            
            # Exit after 1 hour for demo purposes
            if position_age > timedelta(hours=1):
                self.logger.log_info(f"Exiting position in {token.symbol} (time-based)")
                await self._exit_position(token)
                
        except Exception as e:
            self.logger.log_error(e, f"Position exit check for {token.symbol}")
            
    async def _exit_position(self, token: TokenInfo):
        """Exit a position by selling the token."""
        try:
            if not self.jupiter_trader:
                return
                
            # Get token balance
            balance = await self.jupiter_trader._get_token_balance(token.address)
            if balance <= 0:
                self.logger.log_warning(f"No balance to sell for {token.symbol}")
                return
                
            # Execute sell order
            trade = await self.jupiter_trader.sell_token(token, balance)
            
            if trade and trade.success:
                # Update stats
                self.trading_stats.total_trades += 1
                if trade.amount * trade.price > 0:
                    self.trading_stats.successful_trades += 1
                    
                # Remove from active positions
                if token.address in self.active_positions:
                    del self.active_positions[token.address]
                    
                token.status = TokenStatus.SOLD
                self.logger.log_trade(trade)
            else:
                self.logger.log_warning(f"Failed to sell {token.symbol}")
                
        except Exception as e:
            self.logger.log_error(e, f"Position exit for {token.symbol}")
            
    async def _stats_reporting_loop(self):
        """Background loop for stats reporting."""
        while self.running:
            try:
                # Update win rate
                self.trading_stats.update_win_rate()
                
                # Log stats every 10 minutes
                self.logger.log_info(
                    f"STATS: Trades: {self.trading_stats.total_trades}, "
                    f"Success: {self.trading_stats.successful_trades}, "
                    f"Win Rate: {self.trading_stats.win_rate:.1f}%, "
                    f"Active Positions: {len(self.active_positions)}"
                )
                
                # Save stats
                self.logger.save_trading_stats(self.trading_stats)
                
                await asyncio.sleep(600)  # Every 10 minutes
                
            except Exception as e:
                self.logger.log_error(e, "Stats reporting loop")
                await asyncio.sleep(60)
                
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status."""
        return {
            "running": self.running,
            "discovered_tokens": len(self.discovered_tokens),
            "active_positions": len(self.active_positions),
            "trading_stats": self.trading_stats.to_dict(),
            "config": {
                "max_position_size": self.config.max_position_size,
                "min_confidence_score": self.config.min_confidence_score,
                "copy_trading_enabled": self.config.copy_trading_enabled
            }
        }


async def main():
    """Main entry point for the bot."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        async with MemecoinBot() as bot:
            await bot.run_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}")


if __name__ == "__main__":
    asyncio.run(main())