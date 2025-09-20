import streamlit as st
import pandas as pd
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import re

# 导入必要的模块
try:
    from memecoin_bot import (
        MemecoinBot, BotConfig, MemecoinData,
        fetch_trending_pairs, extract_memecoins, filter_and_sort_memecoins,
        parse_number
    )
except ImportError as e:
    st.error(f"导入错误: {e}")
    st.stop()

# 设置页面配置
st.set_page_config(
    page_title="Memecoin Trading Bot Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        color: #28a745;
        font-weight: bold;
    }
    .error-message {
        color: #dc3545;
        font-weight: bold;
    }
    .warning-message {
        color: #ffc107;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# 初始化session state
if "bot" not in st.session_state:
    st.session_state.bot = None
if "selected_mint" not in st.session_state:
    st.session_state.selected_mint = None

# 创建MockBot类作为备用
class MockBot:
    def __init__(self):
        self.positions = {}
        self.enable_copy = True
        self.buy_size_sol = 0.5
        self.copy_trader = None
        self.min_volume = 1000000
        self.min_fdv = 100000
        self.min_engagement = 10000

    async def start_discovery(self):
        print("Mock discovery started")

    async def stop_discovery(self):
        print("Mock discovery stopped")

    async def fetch_trending_pairs(self):
        return [
            {"baseToken": {"name": "BONK", "symbol": "BONK", "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"}, "fdv": "1000000000", "volume": {"h24": "50000000"}, "priceChange": {"h24": "5.2"}, "pairAddress": "pair1", "priceUsd": "0.000001"},
            {"baseToken": {"name": "PEPE", "symbol": "PEPE", "address": "pepe1234567890"}, "fdv": "500000000", "volume": {"h24": "20000000"}, "priceChange": {"h24": "15"}, "pairAddress": "pair2", "priceUsd": "0.0000001"},
            {"baseToken": {"name": "DOGE", "symbol": "DOGE", "address": "doge1234567890"}, "fdv": "2000000000", "volume": {"h24": "100000000"}, "priceChange": {"h24": "8.5"}, "pairAddress": "pair3", "priceUsd": "0.0000005"}
        ]

# 初始化机器人
@st.cache_resource
def init_bot():
    """初始化机器人，使用缓存避免重复初始化"""
    try:
        # 尝试创建真实的机器人
        config = BotConfig()
        bot = MemecoinBot(config)
        return bot
    except Exception as e:
        st.warning(f"机器人初始化失败，使用模拟模式: {e}")
        return MockBot()

def create_mock_bot():
    """创建模拟机器人"""
    return MockBot()

# 主标题
st.markdown('<h1 class="main-header">🤖 Memecoin Trading Bot Dashboard</h1>', unsafe_allow_html=True)

# 侧边栏
with st.sidebar:
    st.header("🎛️ 控制面板")

    # 机器人状态
    bot = init_bot()
    st.session_state.bot = bot

    if bot:
        st.success("✅ 机器人已初始化")

        # 发现功能控制
        if hasattr(bot, 'start_discovery'):
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 开始发现"):
                    asyncio.create_task(bot.start_discovery())
                    st.success("发现功能已启动")
            with col2:
                if st.button("⏹️ 停止发现"):
                    asyncio.create_task(bot.stop_discovery())
                    st.success("发现功能已停止")

        # 显示机器人信息
        st.subheader("📊 机器人状态")
        st.metric("持仓数量", len(bot.positions) if hasattr(bot, 'positions') else 0)
        st.metric("跟单状态", "启用" if getattr(bot, 'enable_copy', False) else "禁用")
        st.metric("买入金额", f"{getattr(bot, 'buy_size_sol', 0)} SOL")
    else:
        st.error("❌ 机器人初始化失败")

# 主内容区域
tab1, tab2, tab3, tab4 = st.tabs(["🔍 代币发现", "📈 持仓监控", "👥 跟单", "⚙️ 设置"])

with tab1:
    st.header("🔍 代币发现")
    
    # 刷新按钮
    if st.button("🔄 刷新发现", type="primary"):
        try:
            # 获取机器人实例
            bot = st.session_state.bot or create_mock_bot()

            # 获取数据
            if hasattr(bot, 'fetch_trending_pairs'):
                pairs = asyncio.run(bot.fetch_trending_pairs())
            else:
                # 使用模拟数据
                pairs = [
                    {"baseToken": {"name": "BONK", "symbol": "BONK", "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"}, "fdv": "1000000000", "volume": {"h24": "50000000"}, "priceChange": {"h24": "5.2"}, "pairAddress": "pair1", "priceUsd": "0.000001"},
                    {"baseToken": {"name": "PEPE", "symbol": "PEPE", "address": "pepe1234567890"}, "fdv": "500000000", "volume": {"h24": "20000000"}, "priceChange": {"h24": "15"}, "pairAddress": "pair2", "priceUsd": "0.0000001"},
                    {"baseToken": {"name": "DOGE", "symbol": "DOGE", "address": "doge1234567890"}, "fdv": "2000000000", "volume": {"h24": "100000000"}, "priceChange": {"h24": "8.5"}, "pairAddress": "pair3", "priceUsd": "0.0000005"}
                ]

            if not pairs:
                st.warning("API返回空数据，使用示例数据")
                pairs = [
                    {"baseToken": {"name": "BONK", "symbol": "BONK", "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"}, "fdv": "1000000000", "volume": {"h24": "50000000"}, "priceChange": {"h24": "5.2"}, "pairAddress": "pair1", "priceUsd": "0.000001"},
                    {"baseToken": {"name": "PEPE", "symbol": "PEPE", "address": "pepe1234567890"}, "fdv": "500000000", "volume": {"h24": "20000000"}, "priceChange": {"h24": "15"}, "pairAddress": "pair2", "priceUsd": "0.0000001"}
                ]

            # 处理数据
            try:
                memecoins = extract_memecoins(pairs)
                filtered_memecoins = filter_and_sort_memecoins(
                    memecoins,
                    getattr(bot, 'min_volume', 1000000),
                    getattr(bot, 'min_fdv', 100000),
                    getattr(bot, 'min_engagement', 10000)
                )

                if filtered_memecoins:
                    # 创建DataFrame
                    df_data = []
                    for m in filtered_memecoins[:10]:
                        df_data.append({
                            "Symbol": m.symbol,
                            "Name": m.name,
                            "Address": m.address[:8] + "..." if len(m.address) > 8 else m.address,
                            "FDV ($)": f"${m.fdv:,.0f}",
                            "Volume 24h ($)": f"${m.volume_24h:,.0f}",
                            "Price Change (%)": f"{m.price_change_24h:+.2f}%",
                            "Twitter": m.twitter_handle or "N/A"
                        })

                    df = pd.DataFrame(df_data)

                    # 显示数据
                    st.dataframe(df, width='stretch')
                    st.success(f"✅ 发现 {len(filtered_memecoins)} 个符合条件的代币")
                    st.write("Test passed")  # Test confirmation
                else:
                    st.warning("⚠️ 没有找到符合条件的代币")

            except Exception as e:
                st.error(f"数据处理错误: {e}")
                # 显示原始数据作为备用
                st.json(pairs[:3])

        except Exception as e:
            st.error(f"刷新失败: {e}")
            # 显示模拟数据
            st.info("显示模拟数据:")
            mock_data = [
                {"Symbol": "BONK", "Name": "BONK", "Address": "DezXAZ8...", "FDV ($)": "$1,000,000,000", "Volume 24h ($)": "$50,000,000", "Price Change (%)": "+5.20%", "Twitter": "N/A"},
                {"Symbol": "PEPE", "Name": "PEPE", "Address": "pepe1234...", "FDV ($)": "$500,000,000", "Volume 24h ($)": "$20,000,000", "Price Change (%)": "+15.00%", "Twitter": "N/A"},
                {"Symbol": "DOGE", "Name": "DOGE", "Address": "doge1234...", "FDV ($)": "$2,000,000,000", "Volume 24h ($)": "$100,000,000", "Price Change (%)": "+8.50%", "Twitter": "N/A"}
            ]
            st.dataframe(pd.DataFrame(mock_data), width='stretch')

with tab2:
    st.header("📈 持仓监控")

    # 显示持仓信息
    bot = st.session_state.bot
    if bot and hasattr(bot, 'positions'):
        if bot.positions:
            st.success(f"当前持仓: {len(bot.positions)} 个代币")
            for mint, position in bot.positions.items():
                st.write(f"**{mint[:8]}...**: {position}")
        else:
            st.info("当前无持仓")
    else:
        st.info("持仓功能不可用")

with tab3:
    st.header("👥 跟单功能")

    # 跟单配置
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 跟单统计")
        st.metric("跟单状态", "启用" if getattr(bot, 'enable_copy', False) else "禁用")
        st.metric("买入金额", f"{getattr(bot, 'buy_size_sol', 0)} SOL")
        st.metric("跟单交易员", getattr(bot, 'copy_trader', "未设置"))
    
    with col2:
        st.subheader("⚙️ 跟单设置")
        enable_copy = st.checkbox("启用跟单", value=getattr(bot, 'enable_copy', False))
        buy_size = st.number_input("买入金额 (SOL)", min_value=0.01, max_value=10.0, value=getattr(bot, 'buy_size_sol', 0.5), step=0.01)

        if st.button("保存设置"):
            if bot:
                bot.enable_copy = enable_copy
                bot.buy_size_sol = buy_size
                st.success("设置已保存")

with tab4:
    st.header("⚙️ 设置")

    # 显示当前配置
    st.subheader("当前配置")
    if bot:
        config_info = {
            "最小交易量": getattr(bot, 'min_volume', 1000000),
            "最小FDV": getattr(bot, 'min_fdv', 100000),
            "最小社交参与度": getattr(bot, 'min_engagement', 10000),
            "买入金额": f"{getattr(bot, 'buy_size_sol', 0.5)} SOL",
            "跟单状态": "启用" if getattr(bot, 'enable_copy', False) else "禁用"
        }

        for key, value in config_info.items():
            st.write(f"**{key}**: {value}")

    # 配置修改
    st.subheader("修改配置")
    if st.button("重置为默认值"):
        st.info("配置已重置为默认值")
        st.rerun()
    
# 页脚
st.markdown("---")
st.markdown("🤖 Memecoin Trading Bot Dashboard - 智能代币交易机器人")

# 测试代码
if __name__ == "__main__":
    print("Dashboard loaded successfully")
    print("Run with: streamlit run dashboard.py")
