#!/usr/bin/env python3
"""
Telegram Bot 集成
参考 OpenSolBot 实现
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
import json

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    from telegram.constants import ParseMode
except ImportError:
    print("请安装 python-telegram-bot: pip install python-telegram-bot")
    exit(1)

from models import TokenInfo, Trade, TradeType
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TelegramBotManager:
    def __init__(self, trading_bot=None):
        self.trading_bot = trading_bot
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.application = None
        self.is_running = False
        
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN 未配置，Telegram Bot 功能将不可用")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        keyboard = [
            [InlineKeyboardButton("📊 查看状态", callback_data="status")],
            [InlineKeyboardButton("🔍 发现代币", callback_data="discover")],
            [InlineKeyboardButton("💼 我的持仓", callback_data="positions")],
            [InlineKeyboardButton("📈 交易历史", callback_data="trades")],
            [InlineKeyboardButton("⚙️ 设置", callback_data="settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🤖 **Memecoin 交易机器人**

欢迎使用智能交易机器人！

**主要功能：**
• 🔍 自动发现热门代币
• 📊 实时监控市场动态
• 💰 智能交易执行
• 🛡️ 风险控制管理

选择下方按钮开始使用：
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令"""
        if not self.trading_bot:
            await update.message.reply_text("❌ 交易机器人未初始化")
            return
        
        status_text = self.get_bot_status()
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理按钮回调"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "status":
            status_text = self.get_bot_status()
            await query.edit_message_text(status_text, parse_mode=ParseMode.MARKDOWN)
        
        elif query.data == "discover":
            await self.handle_discover(query)
        
        elif query.data == "positions":
            await self.handle_positions(query)
        
        elif query.data == "trades":
            await self.handle_trades(query)
        
        elif query.data == "settings":
            await self.handle_settings(query)
    
    def get_bot_status(self) -> str:
        """获取机器人状态"""
        if not self.trading_bot:
            return "❌ 交易机器人未初始化"
        
        status = "🟢 运行中" if self.trading_bot.running else "🔴 已停止"
        
        # 获取统计数据
        total_tokens = len(self.trading_bot.discovered_tokens) if hasattr(self.trading_bot, 'discovered_tokens') else 0
        active_positions = len(self.trading_bot.positions) if hasattr(self.trading_bot, 'positions') else 0
        
        status_text = f"""
🤖 **机器人状态**

**运行状态:** {status}
**发现代币:** {total_tokens} 个
**活跃持仓:** {active_positions} 个
**最后更新:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

使用 /help 查看所有命令
        """
        
        return status_text
    
    async def handle_discover(self, query):
        """处理发现代币请求"""
        if not self.trading_bot:
            await query.edit_message_text("❌ 交易机器人未初始化")
            return
        
        # 获取发现的代币
        tokens = list(self.trading_bot.discovered_tokens.values())[:5] if hasattr(self.trading_bot, 'discovered_tokens') else []
        
        if not tokens:
            await query.edit_message_text("📭 暂无发现的代币")
            return
        
        text = "🔍 **发现的代币**\n\n"
        for i, token in enumerate(tokens, 1):
            text += f"{i}. **{token.symbol}** - ${token.price:.8f}\n"
            text += f"   24h交易量: ${token.volume_24h:,.0f}\n"
            text += f"   Twitter评分: {token.twitter_score:.1f}\n\n"
        
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_positions(self, query):
        """处理持仓查询"""
        if not self.trading_bot or not hasattr(self.trading_bot, 'positions'):
            await query.edit_message_text("❌ 无持仓数据")
            return
        
        positions = self.trading_bot.positions
        if not positions:
            await query.edit_message_text("📭 暂无持仓")
            return
        
        text = "💼 **当前持仓**\n\n"
        total_pnl = 0
        
        for token_address, position in positions.items():
            token = self.trading_bot.discovered_tokens.get(token_address)
            if token:
                pnl = (token.price - position['entry_price']) * position['amount']
                total_pnl += pnl
                pnl_pct = (token.price - position['entry_price']) / position['entry_price'] * 100
                
                text += f"**{token.symbol}**\n"
                text += f"数量: {position['amount']:.4f}\n"
                text += f"入场价: ${position['entry_price']:.8f}\n"
                text += f"当前价: ${token.price:.8f}\n"
                text += f"盈亏: ${pnl:.4f} ({pnl_pct:+.2f}%)\n\n"
        
        text += f"**总盈亏:** ${total_pnl:.4f}"
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_trades(self, query):
        """处理交易历史查询"""
        # 这里可以从 trades.json 文件读取交易历史
        try:
            if os.path.exists('trades.json'):
                with open('trades.json', 'r', encoding='utf-8') as f:
                    trades_data = json.load(f)
                
                recent_trades = trades_data[-5:]  # 最近5笔交易
                
                text = "📈 **最近交易**\n\n"
                for trade in recent_trades:
                    status = "✅" if trade['success'] else "❌"
                    text += f"{status} **{trade['type']}** {trade['symbol']}\n"
                    text += f"数量: {trade['amount']:.4f} SOL\n"
                    text += f"价格: ${trade['price']:.8f}\n"
                    text += f"时间: {trade['timestamp']}\n\n"
                
                await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
            else:
                await query.edit_message_text("📭 暂无交易记录")
        except Exception as e:
            logger.error(f"读取交易历史失败: {e}")
            await query.edit_message_text("❌ 读取交易历史失败")
    
    async def handle_settings(self, query):
        """处理设置请求"""
        keyboard = [
            [InlineKeyboardButton("🔍 开始发现", callback_data="start_discovery")],
            [InlineKeyboardButton("⏹️ 停止发现", callback_data="stop_discovery")],
            [InlineKeyboardButton("📊 查看状态", callback_data="status")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        settings_text = """
⚙️ **机器人设置**

选择操作：
        """
        
        await query.edit_message_text(
            settings_text,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def send_notification(self, message: str, parse_mode: str = ParseMode.MARKDOWN):
        """发送通知消息"""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram 配置不完整，无法发送通知")
            return
        
        try:
            if self.application:
                await self.application.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
        except Exception as e:
            logger.error(f"发送 Telegram 通知失败: {e}")
    
    async def send_trade_notification(self, trade: Trade):
        """发送交易通知"""
        status = "✅ 成功" if trade.success else "❌ 失败"
        emoji = "🟢" if trade.trade_type == TradeType.BUY else "🔴"
        
        message = f"""
{emoji} **交易通知**

**类型:** {trade.trade_type.value}
**代币:** {trade.symbol}
**数量:** {trade.amount:.4f} SOL
**价格:** ${trade.price:.8f}
**状态:** {status}
**时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await self.send_notification(message)
    
    async def send_token_discovered(self, token: TokenInfo):
        """发送代币发现通知"""
        message = f"""
🔍 **新代币发现**

**代币:** {token.symbol} ({token.name})
**价格:** ${token.price:.8f}
**24h交易量:** ${token.volume_24h:,.0f}
**FDV:** ${token.fdv:,.0f}
**Twitter评分:** {token.twitter_score:.1f}
**RugCheck评分:** {token.rugcheck_score:.1f}
**状态:** {token.status.value}
        """
        
        await self.send_notification(message)
    
    async def start_bot(self):
        """启动 Telegram Bot"""
        if not self.bot_token:
            logger.error("TELEGRAM_BOT_TOKEN 未配置")
            return False
        
        try:
            self.application = Application.builder().token(self.bot_token).build()
            
            # 添加命令处理器
            self.application.add_handler(CommandHandler("start", self.start_command))
            self.application.add_handler(CommandHandler("status", self.status_command))
            self.application.add_handler(CallbackQueryHandler(self.button_callback))
            
            # 启动机器人
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.is_running = True
            logger.info("Telegram Bot 启动成功")
            return True
            
        except Exception as e:
            logger.error(f"启动 Telegram Bot 失败: {e}")
            return False
    
    async def stop_bot(self):
        """停止 Telegram Bot"""
        if self.application and self.is_running:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            self.is_running = False
            logger.info("Telegram Bot 已停止")

# 全局 Telegram Bot 实例
telegram_bot = None

async def init_telegram_bot(trading_bot=None):
    """初始化 Telegram Bot"""
    global telegram_bot
    telegram_bot = TelegramBotManager(trading_bot)
    return await telegram_bot.start_bot()

async def cleanup_telegram_bot():
    """清理 Telegram Bot"""
    try:
        if 'telegram_bot' in globals() and telegram_bot:
            await telegram_bot.stop_bot()
    except NameError:
        pass  # telegram_bot not defined

def get_telegram_bot():
    """获取 Telegram Bot 实例"""
    return telegram_bot

if __name__ == "__main__":
    # 测试 Telegram Bot
    async def test():
        bot = TelegramBotManager()
        await bot.start_bot()
        
        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await bot.stop_bot()
    
    asyncio.run(test())
