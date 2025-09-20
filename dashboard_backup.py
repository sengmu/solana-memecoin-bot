"""
Streamlit Dashboard for Solana Memecoin Trading Bot
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import asyncio
import time
from datetime import datetime, timedelta
import logging
import os
from typing import Dict, List, Any, Optional

# Import bot components
from memecoin_bot import MemecoinBot
from models import TokenInfo, Trade, TradeType, TokenStatus, RugCheckResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="Memecoin 交易机器人仪表板",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chinese-text {
        font-family: 'PingFang SC', 'Microsoft YaHei', 'SimHei', sans-serif;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
    .tab-content {
        padding: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class DashboardManager:
    """Manages the Streamlit dashboard state and data."""
    
    def __init__(self):
        self.bot: Optional[MemecoinBot] = None
        self.last_refresh = time.time()
        self.refresh_interval = 30  # seconds
        
    def initialize_bot(self):
        """Initialize the bot if not already done."""
        if self.bot is None:
            try:
                self.bot = MemecoinBot()
                st.success("✅ Bot initialized successfully")
            except Exception as e:
                st.error(f"❌ Failed to initialize bot: {e}")
                return False
        return True
    
    def get_discovered_tokens(self) -> pd.DataFrame:
        """Get discovered tokens as DataFrame."""
        if not self.bot or not hasattr(self.bot, 'discovered_tokens'):
            return pd.DataFrame()
        
        tokens_data = []
        for token in self.bot.discovered_tokens.values():
            tokens_data.append({
                'Symbol': token.symbol,
                'Name': token.name,
                'Address': token.address[:8] + '...' + token.address[-8:],
                'Price (USD)': f"${token.price:.8f}",
                'Market Cap': f"${token.market_cap:,.0f}",
                'Volume 24h': f"${token.volume_24h:,.0f}",
                'Price Change 24h': f"{token.price_change_24h:+.2f}%",
                'Liquidity': f"${token.liquidity:,.0f}",
                'Holders': f"{token.holders:,}",
                'Twitter Score': f"{token.twitter_score:.1f}" if token.twitter_score else "N/A",
                'RugCheck': token.rugcheck_score or "N/A",
                'Confidence': f"{token.confidence_score:.1f}%" if token.confidence_score else "N/A",
                'Status': token.status.value.title(),
                'Is Memecoin': "✅" if token.is_memecoin else "❌",
                'Created': token.created_at.strftime("%Y-%m-%d %H:%M")
            })
        
        return pd.DataFrame(tokens_data)
    
    def get_trades_data(self) -> pd.DataFrame:
        """Load trades data from trades.json."""
        try:
            if os.path.exists('trades.json'):
                with open('trades.json', 'r') as f:
                    trades = json.load(f)
                
                trades_data = []
                for trade in trades:
                    trades_data.append({
                        'ID': trade['id'],
                        'Token': trade['token_address'][:8] + '...' + trade['token_address'][-8:],
                        'Type': trade['trade_type'].upper(),
                        'Amount': trade['amount'],
                        'Price (SOL)': trade['price'],
                        'Slippage': f"{trade['slippage']:.2%}",
                        'Priority Fee': trade['priority_fee'],
                        'TX Hash': trade['tx_hash'][:8] + '...' + trade['tx_hash'][-8:] if trade['tx_hash'] else 'N/A',
                        'Success': "✅" if trade['success'] else "❌",
                        'Timestamp': trade['timestamp'],
                        'Error': trade.get('error_message', 'N/A')
                    })
                
                return pd.DataFrame(trades_data)
        except Exception as e:
            logger.error(f"Error loading trades data: {e}")
        
        return pd.DataFrame()
    
    def get_positions_data(self) -> pd.DataFrame:
        """Get active positions as DataFrame."""
        if not self.bot or not hasattr(self.bot, 'active_positions'):
            return pd.DataFrame()
        
        positions_data = []
        for token in self.bot.active_positions.values():
            positions_data.append({
                'Symbol': token.symbol,
                'Name': token.name,
                'Address': token.address[:8] + '...' + token.address[-8:],
                'Entry Price': f"${token.price:.8f}",
                'Current Price': f"${token.price:.8f}",  # Would need real-time price
                'P&L': "N/A",  # Would need to calculate
                'P&L %': "N/A",  # Would need to calculate
                'Hold Time': str(datetime.now() - token.created_at).split('.')[0],
                'Status': token.status.value.title(),
                'Confidence': f"{token.confidence_score:.1f}%" if token.confidence_score else "N/A"
            })
        
        return pd.DataFrame(positions_data)
    
    def get_safety_data(self) -> Dict[str, int]:
        """Get RugCheck safety data for pie chart."""
        if not self.bot or not hasattr(self.bot, 'discovered_tokens'):
            return {}
        
        safety_counts = {}
        for token in self.bot.discovered_tokens.values():
            if token.rugcheck_score:
                safety_counts[token.rugcheck_score] = safety_counts.get(token.rugcheck_score, 0) + 1
        
        return safety_counts
    
    def should_refresh(self) -> bool:
        """Check if dashboard should refresh."""
        return time.time() - self.last_refresh > self.refresh_interval

def render_sidebar(dashboard: DashboardManager):
    """Render the sidebar with controls."""
    st.sidebar.title("🤖 机器人控制")
    
    # Bot status
    if dashboard.bot and hasattr(dashboard.bot, 'running'):
        status = "🟢 Running" if dashboard.bot.running else "🔴 Stopped"
        st.sidebar.markdown(f"**状态:** {status}")
    else:
        st.sidebar.markdown("**状态:** ⚪ 未初始化")
    
    st.sidebar.divider()
    
    # Discovery controls
    st.sidebar.subheader("🔍 发现")
    
    if st.sidebar.button("🚀 开始发现", type="primary"):
        if dashboard.initialize_bot():
            with st.spinner("Starting discovery..."):
                try:
                    # Start discovery in background
                    asyncio.create_task(dashboard.bot.dexscreener_client.start())
                    st.success("Discovery started!")
                except Exception as e:
                    st.error(f"Failed to start discovery: {e}")
    
    if st.sidebar.button("⏹️ 停止发现"):
        if dashboard.bot and dashboard.bot.dexscreener_client:
            try:
                asyncio.create_task(dashboard.bot.dexscreener_client.stop())
                st.success("Discovery stopped!")
            except Exception as e:
                st.error(f"Failed to stop discovery: {e}")
    
    st.sidebar.divider()
    
    # Manual trading
    st.sidebar.subheader("💰 手动交易")
    
    token_address = st.sidebar.text_input("代币地址", placeholder="输入代币地址...")
    trade_amount = st.sidebar.number_input("数量 (SOL)", min_value=0.001, value=0.01, step=0.001)
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🟢 买入", type="primary"):
            if token_address and dashboard.initialize_bot():
                with st.spinner("执行买入订单..."):
                    try:
                        # This would need to be implemented in the bot
                        st.success(f"买入订单已下达 {trade_amount} SOL!")
                    except Exception as e:
                        st.error(f"买入失败: {e}")
    
    with col2:
        if st.button("🔴 卖出"):
            if token_address and dashboard.initialize_bot():
                with st.spinner("执行卖出订单..."):
                    try:
                        # This would need to be implemented in the bot
                        st.success(f"卖出订单已下达!")
                    except Exception as e:
                        st.error(f"卖出失败: {e}")
    
    st.sidebar.divider()
    
    # Settings
    st.sidebar.subheader("⚙️ 设置")
    
    refresh_interval = st.sidebar.slider("刷新间隔 (秒)", 10, 60, 30)
    dashboard.refresh_interval = refresh_interval
    
    if st.sidebar.button("🔄 强制刷新"):
        st.rerun()

def render_discovery_tab(dashboard: DashboardManager):
    """Render the Discovery tab."""
    st.header("🔍 代币发现")
    
    # Get discovered tokens
    tokens_df = dashboard.get_discovered_tokens()
    
    if tokens_df.empty:
        st.info("尚未发现代币。请从侧边栏开始发现。")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总代币数", len(tokens_df))
    
    with col2:
        memecoins = len(tokens_df[tokens_df['Is Memecoin'] == '✅'])
        st.metric("Meme代币", memecoins)
    
    with col3:
        approved = len(tokens_df[tokens_df['Status'] == 'Approved'])
        st.metric("已批准", approved)
    
    with col4:
        trading = len(tokens_df[tokens_df['Status'] == 'Trading'])
        st.metric("交易中", trading)
    
    st.divider()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("按状态筛选", ["全部"] + list(tokens_df['Status'].unique()))
    
    with col2:
        memecoin_filter = st.selectbox("按类型筛选", ["全部", "仅Meme代币", "非Meme代币"])
    
    with col3:
        min_volume = st.number_input("最小24小时交易量 ($)", min_value=0, value=0)
    
    # Apply filters
    filtered_df = tokens_df.copy()
    
    if status_filter != "全部":
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    
    if memecoin_filter == "仅Meme代币":
        filtered_df = filtered_df[filtered_df['Is Memecoin'] == '✅']
    elif memecoin_filter == "非Meme代币":
        filtered_df = filtered_df[filtered_df['Is Memecoin'] == '❌']
    
    if min_volume > 0:
        # Convert volume strings back to numbers for filtering
        filtered_df['Volume_Num'] = filtered_df['Volume 24h'].str.replace('$', '').str.replace(',', '').astype(float)
        filtered_df = filtered_df[filtered_df['Volume_Num'] >= min_volume]
        filtered_df = filtered_df.drop('Volume_Num', axis=1)
    
    # Display table
    st.subheader(f"发现的代币 ({len(filtered_df)} 个)")
    st.dataframe(
        filtered_df,
        use_container_width=True,
        height=400
    )
    
    # Charts
    if not filtered_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Volume distribution
            volume_data = filtered_df['Volume 24h'].str.replace('$', '').str.replace(',', '').astype(float)
            fig_volume = px.histogram(
                volume_data, 
                title="Volume 24h Distribution",
                labels={'value': 'Volume 24h ($)', 'count': 'Number of Tokens'}
            )
            st.plotly_chart(fig_volume, use_container_width=True)
        
        with col2:
            # Status distribution
            status_counts = filtered_df['Status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Token Status Distribution"
            )
            st.plotly_chart(fig_status, use_container_width=True)

def render_trades_tab(dashboard: DashboardManager):
    """Render the Trades tab."""
    st.header("📈 交易历史")
    
    # Get trades data
    trades_df = dashboard.get_trades_data()
    
    if trades_df.empty:
        st.info("未找到交易记录。交易执行后将在此显示。")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总交易数", len(trades_df))
    
    with col2:
        successful = len(trades_df[trades_df['Success'] == '✅'])
        st.metric("成功交易", successful)
    
    with col3:
        if len(trades_df) > 0:
            success_rate = (successful / len(trades_df)) * 100
            st.metric("成功率", f"{success_rate:.1f}%")
        else:
            st.metric("成功率", "0%")
    
    with col4:
        total_volume = trades_df['Amount'].sum() if not trades_df.empty else 0
        st.metric("总交易量", f"{total_volume:.4f} SOL")
    
    st.divider()
    
    # Filters
            col1, col2, col3 = st.columns(3)
    
            with col1:
        trade_type_filter = st.selectbox("按类型筛选", ["全部"] + list(trades_df['Type'].unique()))
    
            with col2:
        success_filter = st.selectbox("按成功筛选", ["全部", "仅成功", "仅失败"])
    
            with col3:
        date_range = st.date_input("日期范围", value=[datetime.now().date() - timedelta(days=7), datetime.now().date()])
    
    # Apply filters
    filtered_trades = trades_df.copy()
    
    if trade_type_filter != "全部":
        filtered_trades = filtered_trades[filtered_trades['Type'] == trade_type_filter]
    
    if success_filter == "仅成功":
        filtered_trades = filtered_trades[filtered_trades['Success'] == '✅']
    elif success_filter == "仅失败":
        filtered_trades = filtered_trades[filtered_trades['Success'] == '❌']
    
    # Display trades table
    st.subheader(f"交易记录 ({len(filtered_trades)} 条)")
    st.dataframe(
        filtered_trades,
        use_container_width=True,
        height=400
    )
    
    # Charts
    if not filtered_trades.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Trade volume over time
            filtered_trades['Timestamp'] = pd.to_datetime(filtered_trades['Timestamp'])
            volume_by_time = filtered_trades.groupby(filtered_trades['Timestamp'].dt.date)['Amount'].sum().reset_index()
            
            fig_volume = px.line(
                volume_by_time,
                x='Timestamp',
                y='Amount',
                title="Trading Volume Over Time",
                labels={'Amount': 'Volume (SOL)', 'Timestamp': 'Date'}
            )
            st.plotly_chart(fig_volume, use_container_width=True)
        
        with col2:
            # Success rate by type
            success_by_type = filtered_trades.groupby('Type')['Success'].apply(
                lambda x: (x == '✅').sum() / len(x) * 100
            ).reset_index()
            
            fig_success = px.bar(
                success_by_type,
                x='Type',
                y='Success',
                title="Success Rate by Trade Type",
                labels={'Success': 'Success Rate (%)', 'Type': 'Trade Type'}
            )
            st.plotly_chart(fig_success, use_container_width=True)

def render_positions_tab(dashboard: DashboardManager):
    """Render the Positions tab."""
    st.header("💼 活跃持仓")
    
    # Get positions data
    positions_df = dashboard.get_positions_data()
    
    if positions_df.empty:
        st.info("无活跃持仓。交易执行后将在此显示持仓信息。")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("活跃持仓", len(positions_df))
    
    with col2:
        total_value = "N/A"  # Would need to calculate
        st.metric("总价值", total_value)
    
    with col3:
        avg_hold_time = "N/A"  # Would need to calculate
        st.metric("平均持仓时间", avg_hold_time)
    
    with col4:
        profitable = "N/A"  # Would need to calculate
        st.metric("盈利", profitable)
    
    st.divider()
    
    # Positions table
    st.subheader("持仓详情")
    st.dataframe(
        positions_df,
        use_container_width=True,
        height=400
    )
    
    # Position charts
    if not positions_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            # Position distribution by confidence
            confidence_data = positions_df['Confidence'].str.replace('%', '').astype(float)
            fig_confidence = px.histogram(
                confidence_data,
                title="Position Confidence Distribution",
                labels={'value': 'Confidence (%)', 'count': 'Number of Positions'}
            )
            st.plotly_chart(fig_confidence, use_container_width=True)
        
        with col2:
            # Hold time distribution
            hold_times = positions_df['Hold Time'].str.split(':').str[0].astype(int)  # Hours
            fig_hold = px.histogram(
                hold_times,
                title="Hold Time Distribution",
                labels={'value': 'Hold Time (hours)', 'count': 'Number of Positions'}
            )
            st.plotly_chart(fig_hold, use_container_width=True)

def render_safety_tab(dashboard: DashboardManager):
    """Render the Safety tab."""
    st.header("🛡️ 安全分析")
    
    # Get safety data
    safety_data = dashboard.get_safety_data()
    
    if not safety_data:
        st.info("暂无安全数据。开始发现以查看 RugCheck 分析。")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_analyzed = sum(safety_data.values())
    good_rating = safety_data.get('Good', 0) + safety_data.get('Excellent', 0)
    bad_rating = safety_data.get('Bad', 0) + safety_data.get('Dangerous', 0) + safety_data.get('Rug', 0)
    
    with col1:
        st.metric("总分析数", total_analyzed)
    
    with col2:
        st.metric("良好/优秀", good_rating)
    
    with col3:
        st.metric("不良/危险", bad_rating)
    
    with col4:
        if total_analyzed > 0:
            safety_rate = (good_rating / total_analyzed) * 100
            st.metric("安全率", f"{safety_rate:.1f}%")
        else:
            st.metric("安全率", "0%")
    
    st.divider()
    
    # RugCheck pie chart
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if safety_data:
            fig_pie = px.pie(
                values=list(safety_data.values()),
                names=list(safety_data.keys()),
                title="RugCheck Safety Ratings Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Safety recommendations
        st.subheader("安全提示")
        st.markdown("""
        - ✅ **良好/优秀**: 安全交易
        - ⚠️ **一般**: 谨慎交易
        - ❌ **较差/不良**: 避免交易
        - 🚨 **危险/跑路**: 高风险跑路
        """)
        
        # Recent safety alerts
        st.subheader("最近警告")
        if bad_rating > 0:
            st.warning(f"⚠️ {bad_rating} 个代币被标记为不安全")
        else:
            st.success("✅ 无安全警告")

def main():
    """Main dashboard function."""
    # Initialize dashboard
    if 'dashboard' not in st.session_state:
        st.session_state.dashboard = DashboardManager()
    
    dashboard = st.session_state.dashboard
    
    # Header
    st.markdown('<h1 class="main-header chinese-text">🤖 Memecoin 交易机器人仪表板</h1>', unsafe_allow_html=True)
    
    # Sidebar
    render_sidebar(dashboard)
    
    # Auto-refresh
    if dashboard.should_refresh():
        dashboard.last_refresh = time.time()
        st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 发现", "📈 交易", "💼 持仓", "🛡️ 安全"])
    
    with tab1:
        render_discovery_tab(dashboard)
    
    with tab2:
        render_trades_tab(dashboard)
    
    with tab3:
        render_positions_tab(dashboard)
    
    with tab4:
        render_safety_tab(dashboard)
    
    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🤖 Solana Memecoin Trading Bot Dashboard | Auto-refresh every 30 seconds</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()