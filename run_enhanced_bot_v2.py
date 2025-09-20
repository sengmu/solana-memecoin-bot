#!/usr/bin/env python3
"""
增强版 Solana 交易机器人启动脚本
参考 OpenSolBot 的架构和功能
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from config_manager import config_manager
from models import BotConfig
from copy_trader import CopyTrader
from geyser_client_enhanced import GeyserClientEnhanced
from telegram_bot import TelegramBot
from memecoin_bot import MemecoinBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedTradingBot:
    """增强版交易机器人"""

    def __init__(self):
        self.config_manager = config_manager
        self.bot_config = None
        self.memecoin_bot = None
        self.copy_trader = None
        self.geyser_client = None
        self.telegram_bot = None
        self.running = False

        # 从环境变量更新配置
        self.config_manager.update_from_env()

    async def initialize(self):
        """初始化机器人"""
        try:
            logger.info("🚀 初始化增强版交易机器人...")

            # 验证配置
            errors, warnings = self.config_manager.validate_config()
            if errors:
                logger.error(f"配置验证失败: {errors}")
                return False

            if warnings:
                logger.warning(f"配置警告: {warnings}")

            # 创建 BotConfig
            self.bot_config = self._create_bot_config()

            # 初始化各个组件
            await self._initialize_components()

            logger.info("✅ 机器人初始化完成")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False

    def _create_bot_config(self) -> BotConfig:
        """创建 BotConfig"""
        return BotConfig(
            # 基础配置
            solana_rpc_url=self.config_manager.get('rpc.endpoints', ['https://api.mainnet-beta.solana.com'])[0],
            solana_ws_url=self.config_manager.get('rpc.websocket_endpoints', ['wss://api.mainnet-beta.solana.com'])[0],
            private_key=self.config_manager.get('wallet.private_key'),

            # 交易配置
            max_position_size=self.config_manager.get('trading.max_position_size', 0.1),
            min_volume_24h=self.config_manager.get('trading.min_volume_24h', 1000000),
            min_fdv=self.config_manager.get('trading.min_fdv', 100000),
            max_slippage=self.config_manager.get('trading.max_slippage', 0.05),
            default_slippage=self.config_manager.get('trading.default_slippage', 0.01),

            # 跟单配置
            leader_wallets=self.config_manager.get('copy_trading.leader_wallets', []),
            copy_ratio=self.config_manager.get('copy_trading.copy_ratio', 1.0),
            copy_trading_enabled=self.config_manager.get('copy_trading.enabled', False),
            min_confidence_score=self.config_manager.get('copy_trading.min_confidence_score', 70),

            # API 配置
            helius_api_key=self.config_manager.get('api.helius_api_key'),
            shyft_api_key=self.config_manager.get('api.shyft_api_key'),
            jupiter_api_key=self.config_manager.get('api.jupiter_api_key'),
            raydium_api_key=self.config_manager.get('api.raydium_api_key'),

            # Telegram 配置
            telegram_bot_token=self.config_manager.get('telegram.bot_token'),
            telegram_chat_id=self.config_manager.get('telegram.chat_id'),

            # Geyser 配置
            geyser_endpoint=self.config_manager.get('geyser.endpoint'),
            geyser_token=self.config_manager.get('geyser.token'),

            # 其他配置
            twitter_bearer_token=self.config_manager.get('twitter.bearer_token'),
            log_level=self.config_manager.get('bot.log_level', 'INFO'),
            log_to_file=self.config_manager.get('logging.log_to_file', True),
            max_daily_loss=self.config_manager.get('trading.max_daily_loss', 0.1),
            stop_loss_percentage=self.config_manager.get('trading.stop_loss_percentage', 0.2),
            take_profit_percentage=self.config_manager.get('trading.take_profit_percentage', 0.5)
        )

    async def _initialize_components(self):
        """初始化各个组件"""
        # 初始化主交易机器人
        if self.bot_config.private_key and self.bot_config.private_key != 'your_wallet_private_key_here':
            self.memecoin_bot = MemecoinBot(self.bot_config)
            logger.info("✅ 主交易机器人初始化完成")

        # 初始化跟单交易器
        if self.bot_config.copy_trading_enabled and self.bot_config.leader_wallets:
            self.copy_trader = CopyTrader(
                config=self.bot_config,
                private_key=self.bot_config.private_key,
                rpc_url=self.bot_config.solana_rpc_url
            )
            logger.info("✅ 跟单交易器初始化完成")

        # 初始化 Geyser 客户端
        if self.bot_config.geyser_endpoint and self.bot_config.geyser_token:
            programs = self.config_manager.get('geyser.programs', [])
            self.geyser_client = GeyserClientEnhanced(
                endpoint=self.bot_config.geyser_endpoint,
                token=self.bot_config.geyser_token,
                programs=programs
            )
            logger.info("✅ Geyser 客户端初始化完成")

        # 初始化 Telegram Bot
        if self.bot_config.telegram_bot_token and self.bot_config.telegram_chat_id:
            self.telegram_bot = TelegramBot(
                token=self.bot_config.telegram_bot_token,
                chat_id=self.bot_config.telegram_chat_id
            )
            logger.info("✅ Telegram Bot 初始化完成")

    async def start(self):
        """启动机器人"""
        try:
            self.running = True
            logger.info("🚀 启动增强版交易机器人...")

            # 启动各个组件
            tasks = []

            # 启动主交易机器人
            if self.memecoin_bot:
                tasks.append(self._run_memecoin_bot())

            # 启动跟单交易
            if self.copy_trader:
                tasks.append(self._run_copy_trading())

            # 启动 Geyser 监控
            if self.geyser_client:
                tasks.append(self._run_geyser_monitoring())

            # 启动 Telegram Bot
            if self.telegram_bot:
                tasks.append(self._run_telegram_bot())

            # 启动监控任务
            tasks.append(self._run_monitoring())

            # 等待所有任务
            await asyncio.gather(*tasks)

        except Exception as e:
            logger.error(f"启动失败: {e}")
        finally:
            await self.stop()

    async def _run_memecoin_bot(self):
        """运行主交易机器人"""
        try:
            if self.memecoin_bot:
                await self.memecoin_bot.start_discovery()
        except Exception as e:
            logger.error(f"主交易机器人运行失败: {e}")

    async def _run_copy_trading(self):
        """运行跟单交易"""
        try:
            if self.copy_trader:
                await self.copy_trader.start_copy_trading()
        except Exception as e:
            logger.error(f"跟单交易运行失败: {e}")

    async def _run_geyser_monitoring(self):
        """运行 Geyser 监控"""
        try:
            if self.geyser_client:
                async with self.geyser_client:
                    await self.geyser_client.start_listening(self._handle_geyser_event)
        except Exception as e:
            logger.error(f"Geyser 监控运行失败: {e}")

    async def _run_telegram_bot(self):
        """运行 Telegram Bot"""
        try:
            if self.telegram_bot:
                await self.telegram_bot.start()
        except Exception as e:
            logger.error(f"Telegram Bot 运行失败: {e}")

    async def _run_monitoring(self):
        """运行监控任务"""
        while self.running:
            try:
                # 监控系统状态
                await self._monitor_system_status()
                await asyncio.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"监控任务失败: {e}")
                await asyncio.sleep(5)

    async def _handle_geyser_event(self, event_data):
        """处理 Geyser 事件"""
        try:
            logger.info(f"收到 Geyser 事件: {event_data.get('signature', 'unknown')}")

            # 这里可以添加事件处理逻辑
            # 例如：分析交易、触发跟单等

        except Exception as e:
            logger.error(f"处理 Geyser 事件失败: {e}")

    async def _monitor_system_status(self):
        """监控系统状态"""
        try:
            # 检查各个组件状态
            status = {
                'memecoin_bot': self.memecoin_bot is not None,
                'copy_trader': self.copy_trader is not None,
                'geyser_client': self.geyser_client is not None,
                'telegram_bot': self.telegram_bot is not None
            }

            logger.debug(f"系统状态: {status}")

            # 发送状态报告到 Telegram
            if self.telegram_bot:
                await self.telegram_bot.send_status_report(status)

        except Exception as e:
            logger.error(f"监控系统状态失败: {e}")

    async def stop(self):
        """停止机器人"""
        try:
            logger.info("🛑 停止增强版交易机器人...")
            self.running = False

            # 停止各个组件
            if self.memecoin_bot:
                self.memecoin_bot.stop_discovery()

            if self.copy_trader:
                self.copy_trader.stop_copy_trading()

            if self.geyser_client:
                await self.geyser_client.stop()

            if self.telegram_bot:
                await self.telegram_bot.stop()

            logger.info("✅ 机器人已停止")

        except Exception as e:
            logger.error(f"停止机器人失败: {e}")

async def main():
    """主函数"""
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)

    # 创建机器人实例
    bot = EnhancedTradingBot()

    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，正在停止机器人...")
        asyncio.create_task(bot.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 初始化机器人
        if await bot.initialize():
            # 启动机器人
            await bot.start()
        else:
            logger.error("机器人初始化失败")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
    except Exception as e:
        logger.error(f"运行失败: {e}")
        sys.exit(1)
    finally:
        await bot.stop()

if __name__ == "__main__":
    asyncio.run(main())
