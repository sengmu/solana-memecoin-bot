#!/usr/bin/env python3
"""
增强版交易机器人启动脚本
集成 OpenSolBot 功能
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from models import BotConfig
from memecoin_bot import MemecoinBot
from telegram_bot import init_telegram_bot, cleanup_telegram_bot
from copy_trader import CopyTradingManager
from geyser_client import GeyserManager
from dexscreener_client import DexScreenerClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedTradingBot:
    """增强版交易机器人，集成 OpenSolBot 功能"""

    def __init__(self):
        self.config: Optional[BotConfig] = None
        self.memecoin_bot: Optional[MemecoinBot] = None
        self.telegram_bot = None
        self.copy_trading_manager: Optional[CopyTradingManager] = None
        self.geyser_manager: Optional[GeyserManager] = None
        self.dexscreener_client: Optional[DexScreenerClient] = None

        self.is_running = False
        self.tasks = []

        # 设置信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在停止机器人...")
        asyncio.create_task(self.stop())

    async def initialize(self):
        """初始化所有组件"""
        try:
            logger.info("🚀 初始化增强版交易机器人...")

            # 加载配置
            self.config = BotConfig.from_env()
            logger.info("✅ 配置加载完成")

            # 初始化 DexScreener 客户端
            self.dexscreener_client = DexScreenerClient(self.config, self.on_token_discovered)
            logger.info("✅ DexScreener 客户端初始化完成")

            # 初始化 Memecoin 机器人
            self.memecoin_bot = MemecoinBot(self.config)
            logger.info("✅ Memecoin 机器人初始化完成")

            # 初始化 Telegram Bot
            if self.config.telegram_bot_token:
                self.telegram_bot = await init_telegram_bot(self.memecoin_bot)
                if self.telegram_bot:
                    logger.info("✅ Telegram Bot 初始化完成")
                else:
                    logger.warning("⚠️ Telegram Bot 初始化失败")
            else:
                logger.warning("⚠️ Telegram Bot Token 未配置")

            # 初始化跟单交易管理器
            if self.config.copy_trading_enabled:
                self.copy_trading_manager = CopyTradingManager(self.config)
                if self.config.private_key and self.config.solana_rpc_url:
                    self.copy_trading_manager.add_copy_trader(
                        'main_trader',
                        self.config.private_key,
                        self.config.solana_rpc_url
                    )
                    logger.info("✅ 跟单交易管理器初始化完成")
                else:
                    logger.warning("⚠️ 跟单交易配置不完整")

            # 初始化 Geyser 管理器
            if self.config.geyser_endpoint:
                self.geyser_manager = GeyserManager(self.config)
                if self.config.solana_rpc_url:
                    self.geyser_manager.add_geyser_client(
                        'main_geyser',
                        self.config.solana_rpc_url
                    )
                    logger.info("✅ Geyser 管理器初始化完成")
                else:
                    logger.warning("⚠️ Geyser 配置不完整")

            logger.info("🎉 所有组件初始化完成！")
            return True

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            return False

    async def start(self):
        """启动机器人"""
        if not await self.initialize():
            return False

        try:
            logger.info("🚀 启动增强版交易机器人...")
            self.is_running = True

            # 启动 Memecoin 机器人
            if self.memecoin_bot:
                task = asyncio.create_task(self.memecoin_bot.start_discovery())
                self.tasks.append(task)
                logger.info("✅ Memecoin 机器人已启动")

            # 启动跟单交易
            if self.copy_trading_manager:
                task = asyncio.create_task(self.copy_trading_manager.start_all_copy_traders())
                self.tasks.append(task)
                logger.info("✅ 跟单交易已启动")

            # 启动 Geyser 监控
            if self.geyser_manager:
                task = asyncio.create_task(self.geyser_manager.start_all_clients())
                self.tasks.append(task)
                logger.info("✅ Geyser 监控已启动")

            # 启动状态监控
            task = asyncio.create_task(self.status_monitor())
            self.tasks.append(task)

            logger.info("🎉 增强版交易机器人启动完成！")

            # 等待所有任务完成
            await asyncio.gather(*self.tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"❌ 启动失败: {e}")
            await self.stop()
            return False

    async def stop(self):
        """停止机器人"""
        if not self.is_running:
            return

        logger.info("⏹️ 正在停止增强版交易机器人...")
        self.is_running = False

        # 停止 Memecoin 机器人
        if self.memecoin_bot:
            self.memecoin_bot.stop_discovery()
            logger.info("✅ Memecoin 机器人已停止")

        # 停止跟单交易
        if self.copy_trading_manager:
            await self.copy_trading_manager.stop_all_copy_traders()
            logger.info("✅ 跟单交易已停止")

        # 停止 Geyser 监控
        if self.geyser_manager:
            await self.geyser_manager.stop_all_clients()
            logger.info("✅ Geyser 监控已停止")

        # 停止 Telegram Bot
        if self.telegram_bot:
            await cleanup_telegram_bot()
            logger.info("✅ Telegram Bot 已停止")

        # 取消所有任务
        for task in self.tasks:
            task.cancel()

        self.tasks.clear()
        logger.info("🎉 增强版交易机器人已完全停止")

    async def status_monitor(self):
        """状态监控"""
        while self.is_running:
            try:
                # 获取状态信息
                status = self.get_status()

                # 发送状态通知（如果需要）
                if self.telegram_bot and self.config.telegram_chat_id:
                    # 每小时发送一次状态报告
                    if datetime.now().minute == 0:
                        await self.telegram_bot.send_notification(status)

                # 等待1分钟
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"状态监控错误: {e}")
                await asyncio.sleep(60)

    def get_status(self) -> str:
        """获取机器人状态"""
        if not self.memecoin_bot:
            return "❌ 机器人未初始化"

        status = "🟢 运行中" if self.is_running else "🔴 已停止"

        # 获取统计数据
        total_tokens = len(self.memecoin_bot.discovered_tokens) if hasattr(self.memecoin_bot, 'discovered_tokens') else 0
        active_positions = len(self.memecoin_bot.positions) if hasattr(self.memecoin_bot, 'positions') else 0

        # 获取跟单统计
        copy_stats = ""
        if self.copy_trading_manager:
            all_stats = self.copy_trading_manager.get_all_statistics()
            for name, stats in all_stats.items():
                copy_stats += f"\n**{name}:** {stats['total_trades']} 笔交易, 成功率 {stats['success_rate']:.1f}%"

        # 获取 Geyser 统计
        geyser_stats = ""
        if self.geyser_manager:
            all_stats = self.geyser_manager.get_all_stats()
            for name, stats in all_stats.items():
                geyser_stats += f"\n**{name}:** 缓存 {stats['token_cache_size']} 个代币"

        status_text = f"""
🤖 **增强版交易机器人状态**

**运行状态:** {status}
**发现代币:** {total_tokens} 个
**活跃持仓:** {active_positions} 个
**最后更新:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**跟单交易:**{copy_stats if copy_stats else "\n未启用"}

**Geyser 监控:**{geyser_stats if geyser_stats else "\n未启用"}

**功能状态:**
• 🔍 代币发现: {'✅' if self.memecoin_bot else '❌'}
• 📱 Telegram: {'✅' if self.telegram_bot else '❌'}
• 👥 跟单交易: {'✅' if self.copy_trading_manager else '❌'}
• ⚡ Geyser: {'✅' if self.geyser_manager else '❌'}
        """

        return status_text

    def on_token_discovered(self, token):
        """代币发现回调"""
        logger.info(f"🔍 发现新代币: {token.symbol} - {token.name}")

        # 发送 Telegram 通知
        if self.telegram_bot:
            asyncio.create_task(self.telegram_bot.send_token_discovered(token))

async def main():
    """主函数"""
    print("🤖 增强版 Solana Memecoin 交易机器人")
    print("=" * 50)
    print("基于 OpenSolBot 功能增强")
    print("支持 Telegram Bot、跟单交易、Geyser 监控")
    print("=" * 50)

    bot = EnhancedTradingBot()

    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\n⏹️ 收到中断信号，正在停止...")
        await bot.stop()
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        await bot.stop()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
