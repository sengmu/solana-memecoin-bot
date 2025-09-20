#!/usr/bin/env python3
"""
增强版可视化仪表板
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import time
import asyncio
import logging
import numpy as np

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="Memecoin 交易机器人 - 可视化仪表板",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .status-running {
        color: #00ff88;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .status-stopped {
        color: #ff4757;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .status-initializing {
        color: #ffa502;
        font-weight: bold;
        font-size: 1.2rem;
    }
    .config-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .trading-card {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

class VisualDashboardManager:
    def __init__(self):
        self.bot = None
        self.last_refresh = None
        self.mock_data = self.generate_mock_data()

    def generate_mock_data(self):
        """生成模拟数据用于演示"""
        return {
            'tokens': [
                {
                    'symbol': 'PEPE',
                    'name': 'Pepe Token',
                    'price': 0.00000123,
                    'volume_24h': 2500000,
                    'fdv': 50000000,
                    'twitter_score': 85.5,
                    'rugcheck_score': 78.2,
                    'status': 'approved',
                    'change_24h': 12.5,
                    'market_cap': 45000000
                },
                {
                    'symbol': 'DOGE',
                    'name': 'Dogecoin',
                    'price': 0.00004567,
                    'volume_24h': 5000000,
                    'fdv': 100000000,
                    'twitter_score': 92.3,
                    'rugcheck_score': 88.7,
                    'status': 'trading',
                    'change_24h': -3.2,
                    'market_cap': 95000000
                },
                {
                    'symbol': 'BONK',
                    'name': 'Bonk Token',
                    'price': 0.00001234,
                    'volume_24h': 1800000,
                    'fdv': 30000000,
                    'twitter_score': 76.8,
                    'rugcheck_score': 72.1,
                    'status': 'approved',
                    'change_24h': 8.7,
                    'market_cap': 28000000
                },
                {
                    'symbol': 'SHIB',
                    'name': 'Shiba Inu',
                    'price': 0.00000089,
                    'volume_24h': 3200000,
                    'fdv': 80000000,
                    'twitter_score': 88.9,
                    'rugcheck_score': 85.3,
                    'status': 'trading',
                    'change_24h': 5.2,
                    'market_cap': 75000000
                },
                {
                    'symbol': 'FLOKI',
                    'name': 'Floki Inu',
                    'price': 0.00000234,
                    'volume_24h': 1500000,
                    'fdv': 25000000,
                    'twitter_score': 82.1,
                    'rugcheck_score': 79.6,
                    'status': 'approved',
                    'change_24h': -2.1,
                    'market_cap': 22000000
                },
                {
                    'symbol': 'WOJAK',
                    'name': 'Wojak Token',
                    'price': 0.00000045,
                    'volume_24h': 800000,
                    'fdv': 15000000,
                    'twitter_score': 74.3,
                    'rugcheck_score': 68.9,
                    'status': 'pending',
                    'change_24h': 15.8,
                    'market_cap': 12000000
                },
                {
                    'symbol': 'CHAD',
                    'name': 'Chad Token',
                    'price': 0.00000156,
                    'volume_24h': 1200000,
                    'fdv': 20000000,
                    'twitter_score': 79.7,
                    'rugcheck_score': 75.4,
                    'status': 'approved',
                    'change_24h': 7.3,
                    'market_cap': 18000000
                },
                {
                    'symbol': 'KEKW',
                    'name': 'Kekw Token',
                    'price': 0.00000078,
                    'volume_24h': 600000,
                    'fdv': 12000000,
                    'twitter_score': 71.2,
                    'rugcheck_score': 66.8,
                    'status': 'pending',
                    'change_24h': -4.5,
                    'market_cap': 10000000
                },
                {
                    'symbol': 'MOON',
                    'name': 'Moon Token',
                    'price': 0.00000321,
                    'volume_24h': 2000000,
                    'fdv': 40000000,
                    'twitter_score': 86.4,
                    'rugcheck_score': 81.7,
                    'status': 'trading',
                    'change_24h': 11.2,
                    'market_cap': 38000000
                },
                {
                    'symbol': 'DEGEN',
                    'name': 'Degen Token',
                    'price': 0.00000067,
                    'volume_24h': 900000,
                    'fdv': 18000000,
                    'twitter_score': 77.8,
                    'rugcheck_score': 73.5,
                    'status': 'approved',
                    'change_24h': 3.7,
                    'market_cap': 16000000
                },
                {
                    'symbol': 'APE',
                    'name': 'Ape Token',
                    'price': 0.00000456,
                    'volume_24h': 1800000,
                    'fdv': 35000000,
                    'twitter_score': 83.6,
                    'rugcheck_score': 80.2,
                    'status': 'trading',
                    'change_24h': -1.8,
                    'market_cap': 32000000
                },
                {
                    'symbol': 'MONKE',
                    'name': 'Monke Token',
                    'price': 0.00000023,
                    'volume_24h': 500000,
                    'fdv': 8000000,
                    'twitter_score': 69.4,
                    'rugcheck_score': 64.1,
                    'status': 'pending',
                    'change_24h': 22.6,
                    'market_cap': 7000000
                },
                {
                    'symbol': 'FROG',
                    'name': 'Frog Token',
                    'price': 0.00000189,
                    'volume_24h': 1100000,
                    'fdv': 22000000,
                    'twitter_score': 78.9,
                    'rugcheck_score': 76.3,
                    'status': 'approved',
                    'change_24h': 6.4,
                    'market_cap': 20000000
                },
                {
                    'symbol': 'CAT',
                    'name': 'Cat Token',
                    'price': 0.00000034,
                    'volume_24h': 700000,
                    'fdv': 10000000,
                    'twitter_score': 72.5,
                    'rugcheck_score': 69.8,
                    'status': 'pending',
                    'change_24h': -8.2,
                    'market_cap': 9000000
                },
                {
                    'symbol': 'DOG',
                    'name': 'Dog Token',
                    'price': 0.00000012,
                    'volume_24h': 400000,
                    'fdv': 6000000,
                    'twitter_score': 65.7,
                    'rugcheck_score': 61.4,
                    'status': 'pending',
                    'change_24h': 18.9,
                    'market_cap': 5500000
                }
            ],
            'trades': [
                {'timestamp': '2024-01-20 14:30:00', 'type': 'BUY', 'symbol': 'PEPE', 'amount': 0.5, 'price': 0.00000120, 'success': True, 'pnl': 0.00015},
                {'timestamp': '2024-01-20 15:45:00', 'type': 'BUY', 'symbol': 'DOGE', 'amount': 1.0, 'price': 0.00004500, 'success': True, 'pnl': 0.00067},
                {'timestamp': '2024-01-20 16:15:00', 'type': 'SELL', 'symbol': 'PEPE', 'amount': 0.5, 'price': 0.00000125, 'success': True, 'pnl': 0.00025},
            ],
            'positions': [
                {'symbol': 'DOGE', 'amount': 1.0, 'entry_price': 0.00004500, 'current_price': 0.00004567, 'pnl': 0.00067, 'pnl_pct': 1.49},
                {'symbol': 'BONK', 'amount': 0.8, 'entry_price': 0.00001200, 'current_price': 0.00001234, 'pnl': 0.000272, 'pnl_pct': 2.83},
            ]
        }

    def initialize_bot(self):
        """初始化机器人"""
        try:
            # Use the new BotConfig with default values
            self.bot = type('MockBot', (), {
                'running': True,
                'discovered_tokens': {},
                'positions': {}
            })()
            return True
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")
            return False

def render_header():
    """渲染页面头部"""
    st.markdown("""
    <div class="main-header">
        <h1>🤖 Memecoin 交易机器人</h1>
        <p>智能代币发现与自动化交易平台</p>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar(dashboard_manager):
    """渲染侧边栏"""
    st.sidebar.markdown("## 🤖 机器人控制")

    # 机器人状态
    if dashboard_manager.bot:
        status = "🟢 运行中" if dashboard_manager.bot.running else "🔴 已停止"
        st.sidebar.markdown(f"**状态:** <span class='status-running'>{status}</span>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("**状态:** <span class='status-initializing'>⚪ 未初始化</span>", unsafe_allow_html=True)

    st.sidebar.divider()

    # 控制按钮
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("🚀 启动", type="primary"):
            if not dashboard_manager.bot:
                if dashboard_manager.initialize_bot():
                    st.sidebar.success("机器人启动成功!")
                    st.rerun()
                else:
                    st.sidebar.error("机器人启动失败!")
            else:
                st.sidebar.success("机器人已在运行!")

    with col2:
        if st.button("⏹️ 停止"):
            if dashboard_manager.bot:
                dashboard_manager.bot.running = False
                st.sidebar.success("机器人已停止!")
                st.rerun()
            else:
                st.sidebar.warning("机器人未运行!")

    st.sidebar.divider()

    # 快速配置
    st.sidebar.markdown("## ⚙️ 快速配置")

    # 配置界面链接
    st.sidebar.markdown("### 🔧 配置界面")

    # 使用 st.link_button 如果可用，否则使用普通链接
    try:
        st.sidebar.link_button("🔧 打开配置界面", "http://localhost:8502")
    except AttributeError:
        # 如果 st.link_button 不可用，使用普通链接
        st.sidebar.markdown("[🔧 点击打开配置界面](http://localhost:8502)")

    # 显示配置界面状态
    if st.sidebar.button("📊 检查配置界面状态"):
        try:
            import requests
            response = requests.get("http://localhost:8502", timeout=2)
            if response.status_code == 200:
                st.sidebar.success("✅ 配置界面运行正常")
            else:
                st.sidebar.warning("⚠️ 配置界面可能未启动")
        except:
            st.sidebar.error("❌ 配置界面未启动")

    # 设置
    st.sidebar.markdown("## ⚙️ 设置")

    refresh_interval = st.sidebar.slider("刷新间隔 (秒)", 10, 300, 30)

    if st.sidebar.button("🔄 强制刷新"):
        st.rerun()

def render_overview_metrics(dashboard_manager):
    """渲染概览指标"""
    st.subheader("📊 概览指标")

    # 计算指标
    total_tokens = len(dashboard_manager.mock_data['tokens'])
    active_trades = len([t for t in dashboard_manager.mock_data['trades'] if t['success']])
    total_pnl = sum([p['pnl'] for p in dashboard_manager.mock_data['positions']])
    success_rate = (active_trades / len(dashboard_manager.mock_data['trades']) * 100) if dashboard_manager.mock_data['trades'] else 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{total_tokens}</h3>
            <p>发现代币</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{active_trades}</h3>
            <p>成功交易</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>{success_rate:.1f}%</h3>
            <p>成功率</p>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>${total_pnl:.4f}</h3>
            <p>总盈亏</p>
        </div>
        """, unsafe_allow_html=True)

def render_token_discovery(dashboard_manager):
    """渲染代币发现"""
    st.subheader("🔍 代币发现")

    tokens_df = pd.DataFrame(dashboard_manager.mock_data['tokens'])

    # 代币表格
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)

    # 筛选器
    col1, col2, col3 = st.columns(3)

    with col1:
        status_filter = st.selectbox("状态筛选", ["全部", "approved", "trading", "pending"])

    with col2:
        min_volume = st.number_input("最小交易量 ($)", min_value=0, value=1000000)

    with col3:
        min_score = st.slider("最小评分", min_value=0, max_value=100, value=70)

    # 应用筛选
    filtered_df = tokens_df.copy()
    if status_filter != "全部":
        filtered_df = filtered_df[filtered_df['status'] == status_filter]
    filtered_df = filtered_df[filtered_df['volume_24h'] >= min_volume]
    filtered_df = filtered_df[filtered_df['twitter_score'] >= min_score]

    # 显示表格
    st.dataframe(
        filtered_df,
        width='stretch',
        column_config={
            "price": st.column_config.NumberColumn("价格", format="$%.8f"),
            "volume_24h": st.column_config.NumberColumn("24h交易量", format="$%.0f"),
            "fdv": st.column_config.NumberColumn("FDV", format="$%.0f"),
            "twitter_score": st.column_config.NumberColumn("Twitter评分", format="%.1f"),
            "rugcheck_score": st.column_config.NumberColumn("RugCheck评分", format="%.1f"),
            "change_24h": st.column_config.NumberColumn("24h变化", format="%.2f%%"),
        }
    )

    st.markdown('</div>', unsafe_allow_html=True)

def render_trading_charts(dashboard_manager):
    """渲染交易图表"""
    st.subheader("📈 交易分析")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        # 代币价格变化
        tokens_df = pd.DataFrame(dashboard_manager.mock_data['tokens'])

        fig = px.bar(
            tokens_df,
            x='symbol',
            y='change_24h',
            title="代币24小时价格变化",
            color='change_24h',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig.update_layout(
            xaxis_title="代币",
            yaxis_title="价格变化 (%)",
            height=400
        )
        st.plotly_chart(fig, width='stretch')

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        # 交易量分布
        fig = px.pie(
            tokens_df,
            values='volume_24h',
            names='symbol',
            title="代币交易量分布"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, width='stretch')

        st.markdown('</div>', unsafe_allow_html=True)

def render_positions(dashboard_manager):
    """渲染持仓信息"""
    st.subheader("💼 当前持仓")

    positions_df = pd.DataFrame(dashboard_manager.mock_data['positions'])

    if not positions_df.empty:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)

        # 持仓表格
        st.dataframe(
            positions_df,
            width='stretch',
            column_config={
                "amount": st.column_config.NumberColumn("数量", format="%.4f"),
                "entry_price": st.column_config.NumberColumn("入场价格", format="$%.8f"),
                "current_price": st.column_config.NumberColumn("当前价格", format="$%.8f"),
                "pnl": st.column_config.NumberColumn("盈亏", format="$%.4f"),
                "pnl_pct": st.column_config.NumberColumn("盈亏%", format="%.2f%%"),
            }
        )

        # 盈亏图表
        fig = px.bar(
            positions_df,
            x='symbol',
            y='pnl_pct',
            title="持仓盈亏百分比",
            color='pnl_pct',
            color_continuous_scale=['red', 'yellow', 'green']
        )
        fig.update_layout(
            xaxis_title="代币",
            yaxis_title="盈亏 (%)",
            height=300
        )
        st.plotly_chart(fig, width='stretch')

        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("暂无持仓")

def render_trading_history(dashboard_manager):
    """渲染交易历史"""
    st.subheader("📊 交易历史")

    trades_df = pd.DataFrame(dashboard_manager.mock_data['trades'])
    trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])

    st.markdown('<div class="chart-container">', unsafe_allow_html=True)

    # 交易历史表格
    st.dataframe(
        trades_df,
        width='stretch',
        column_config={
            "amount": st.column_config.NumberColumn("数量", format="%.4f"),
            "price": st.column_config.NumberColumn("价格", format="$%.8f"),
            "pnl": st.column_config.NumberColumn("盈亏", format="$%.4f"),
        }
    )

    # 交易趋势图
    fig = px.line(
        trades_df,
        x='timestamp',
        y='pnl',
        color='symbol',
        title="交易盈亏趋势",
        markers=True
    )
    fig.update_layout(
        xaxis_title="时间",
        yaxis_title="盈亏 ($)",
        height=400
    )
    st.plotly_chart(fig, width='stretch')

    st.markdown('</div>', unsafe_allow_html=True)

def render_copy_trading_panel(dashboard_manager):
    """渲染跟单交易面板"""
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.subheader("🤖 跟单交易监控")

    # 检查跟单配置
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()

        copy_enabled = os.getenv('COPY_TRADING_ENABLED', 'false').lower() == 'true'
        leader_wallet = os.getenv('LEADER_WALLET_ADDRESS', '')
        copy_ratio = float(os.getenv('COPY_RATIO', '1.0'))
        min_confidence = int(os.getenv('MIN_CONFIDENCE_SCORE', '70'))

        if copy_enabled and leader_wallet:
            # 跟单状态
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("跟单状态", "🟢 已启用", "运行中")

            with col2:
                st.metric("跟单比例", f"{copy_ratio*100:.0f}%", "当前设置")

            with col3:
                st.metric("最小置信度", f"{min_confidence}%", "过滤阈值")

            with col4:
                st.metric("跟单钱包", "1个", "已配置")

            # 跟单钱包信息
            st.markdown("### 📍 跟单钱包信息")
            st.code(f"主要钱包: {leader_wallet[:8]}...{leader_wallet[-8:]}")

            # 模拟跟单交易记录
            st.markdown("### 📊 最近跟单交易")

            copy_trades = [
                {
                    'time': '2024-01-20 14:30:25',
                    'token': 'PEPE',
                    'action': '买入',
                    'amount': '0.5 SOL',
                    'confidence': 85,
                    'status': '成功'
                },
                {
                    'time': '2024-01-20 14:25:10',
                    'token': 'DOGE',
                    'action': '卖出',
                    'amount': '1.2 SOL',
                    'confidence': 92,
                    'status': '成功'
                },
                {
                    'time': '2024-01-20 14:15:45',
                    'token': 'BONK',
                    'action': '买入',
                    'amount': '0.8 SOL',
                    'confidence': 78,
                    'status': '成功'
                }
            ]

            for trade in copy_trades:
                col1, col2, col3, col4, col5, col6 = st.columns(6)
                with col1:
                    st.text(trade['time'])
                with col2:
                    st.text(trade['token'])
                with col3:
                    color = "🟢" if trade['action'] == '买入' else "🔴"
                    st.text(f"{color} {trade['action']}")
                with col4:
                    st.text(trade['amount'])
                with col5:
                    st.text(f"{trade['confidence']}%")
                with col6:
                    status_color = "🟢" if trade['status'] == '成功' else "🔴"
                    st.text(f"{status_color} {trade['status']}")

            # 跟单统计
            st.markdown("### 📈 跟单统计")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("今日跟单次数", "12", "3")

            with col2:
                st.metric("成功率", "91.7%", "2.3%")

            with col3:
                st.metric("总收益", "+2.4 SOL", "+15.2%")

        else:
            st.warning("⚠️ 跟单功能未配置或未启用")
            st.info("请在配置界面中设置跟单参数")

            if st.button("🔧 前往配置界面"):
                st.markdown("[点击打开配置界面](http://localhost:8502)")

    except Exception as e:
        st.error(f"❌ 跟单监控加载失败: {e}")

    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """主函数"""
    # 初始化仪表板管理器
    if 'dashboard_manager' not in st.session_state:
        st.session_state.dashboard_manager = VisualDashboardManager()

    dashboard_manager = st.session_state.dashboard_manager

    # 渲染页面
    render_header()
    render_sidebar(dashboard_manager)

    # 自动刷新
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()

    refresh_interval = 30
    if time.time() - st.session_state.last_refresh > refresh_interval:
        st.session_state.last_refresh = time.time()
        st.rerun()

    # 主要内容
    render_overview_metrics(dashboard_manager)

    # 标签页
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 代币发现", "📈 交易分析", "💼 持仓管理", "🤖 跟单监控", "📊 交易历史"])

    with tab1:
        render_token_discovery(dashboard_manager)

    with tab2:
        render_trading_charts(dashboard_manager)

    with tab3:
        render_positions(dashboard_manager)

    with tab4:
        render_copy_trading_panel(dashboard_manager)

    with tab5:
        render_trading_history(dashboard_manager)

if __name__ == "__main__":
    main()
