import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime, timedelta
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
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
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .chinese-text {
        font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .status-running {
        color: #00ff00;
        font-weight: bold;
    }
    .status-stopped {
        color: #ff0000;
        font-weight: bold;
    }
    .status-initializing {
        color: #ffa500;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

class CloudDashboardManager:
    def __init__(self):
        self.bot = None
        self.last_refresh = None
        
    def initialize_bot(self):
        """Initialize the bot with environment variables"""
        try:
            # For cloud deployment, we'll use a simplified initialization
            st.success("✅ 机器人初始化成功 (云部署模式)")
            return True
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")
            return False
    
    def get_discovered_tokens(self):
        """Get discovered tokens data (mock data for demo)"""
        # Mock data for demonstration
        mock_tokens = [
            {
                'Symbol': 'PEPE',
                'Name': 'Pepe Token',
                'Address': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
                'Price': 0.00000123,
                'Volume24h': 2500000,
                'FDV': 50000000,
                'Twitter Score': 85.5,
                'RugCheck Score': 78.2,
                'Status': 'approved',
                'Discovered At': '2024-01-20 14:30:00'
            },
            {
                'Symbol': 'DOGE',
                'Name': 'Dogecoin',
                'Address': '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
                'Price': 0.00004567,
                'Volume24h': 5000000,
                'FDV': 100000000,
                'Twitter Score': 92.3,
                'RugCheck Score': 88.7,
                'Status': 'trading',
                'Discovered At': '2024-01-20 15:45:00'
            },
            {
                'Symbol': 'BONK',
                'Name': 'Bonk Token',
                'Address': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
                'Price': 0.00001234,
                'Volume24h': 1800000,
                'FDV': 30000000,
                'Twitter Score': 76.8,
                'RugCheck Score': 72.1,
                'Status': 'approved',
                'Discovered At': '2024-01-20 16:15:00'
            }
        ]
        return pd.DataFrame(mock_tokens)
    
    def get_trades_data(self):
        """Get trades data (mock data for demo)"""
        # Mock data for demonstration
        mock_trades = [
            {
                'Timestamp': '2024-01-20 14:30:00',
                'Type': 'BUY',
                'Symbol': 'PEPE',
                'Amount': 0.5,
                'Price': 0.00000120,
                'Success': True,
                'Confidence': 85.5,
                'Reason': 'High Twitter score and volume'
            },
            {
                'Timestamp': '2024-01-20 15:45:00',
                'Type': 'BUY',
                'Symbol': 'DOGE',
                'Amount': 1.0,
                'Price': 0.00004500,
                'Success': True,
                'Confidence': 92.3,
                'Reason': 'Excellent RugCheck score'
            },
            {
                'Timestamp': '2024-01-20 16:15:00',
                'Type': 'SELL',
                'Symbol': 'PEPE',
                'Amount': 0.5,
                'Price': 0.00000125,
                'Success': True,
                'Confidence': 78.2,
                'Reason': 'Profit target reached'
            }
        ]
        return pd.DataFrame(mock_trades)
    
    def get_positions_data(self):
        """Get current positions data (mock data for demo)"""
        # Mock data for demonstration
        mock_positions = [
            {
                'Symbol': 'DOGE',
                'Address': '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM',
                'Amount': 1.0,
                'Entry Price': 0.00004500,
                'Current Price': 0.00004567,
                'P&L': 0.00067,
                'P&L %': 1.49,
                'Hold Time': 2.5,
                'Confidence': 92.3
            },
            {
                'Symbol': 'BONK',
                'Address': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
                'Amount': 0.8,
                'Entry Price': 0.00001200,
                'Current Price': 0.00001234,
                'P&L': 0.000272,
                'P&L %': 2.83,
                'Hold Time': 1.2,
                'Confidence': 76.8
            }
        ]
        return pd.DataFrame(mock_positions)
    
    def get_safety_data(self):
        """Get RugCheck safety analysis data (mock data for demo)"""
        # Mock data for demonstration
        mock_safety = [
            {'Symbol': 'PEPE', 'RugCheck Score': 78.2, 'Status': 'approved'},
            {'Symbol': 'DOGE', 'RugCheck Score': 88.7, 'Status': 'trading'},
            {'Symbol': 'BONK', 'RugCheck Score': 72.1, 'Status': 'approved'}
        ]
        return pd.DataFrame(mock_safety)

def render_sidebar(dashboard_manager):
    """Render the sidebar with bot controls"""
    st.sidebar.title("🤖 机器人控制")
    
    # Bot status
    if dashboard_manager.bot:
        status = "🟢 运行中" if dashboard_manager.bot else "🔴 已停止"
        st.sidebar.markdown(f"**状态:** {status}")
    else:
        st.sidebar.markdown("**状态:** ⚪ 未初始化")
    
    st.sidebar.divider()
    
    # Discovery controls
    st.sidebar.subheader("🔍 发现")
    
    if st.sidebar.button("🚀 开始发现", type="primary"):
        if not dashboard_manager.bot:
            if dashboard_manager.initialize_bot():
                st.sidebar.success("机器人初始化成功!")
            else:
                st.sidebar.error("机器人初始化失败!")
        else:
            st.sidebar.success("开始发现代币...")
    
    if st.sidebar.button("⏹️ 停止发现"):
        st.sidebar.success("已停止发现...")
    
    st.sidebar.divider()
    
    # Manual trading
    st.sidebar.subheader("💰 手动交易")
    
    token_address = st.sidebar.text_input("代币地址", placeholder="输入代币地址...")
    trade_amount = st.sidebar.number_input("数量 (SOL)", min_value=0.001, value=0.1, step=0.01)
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🟢 买入", type="primary"):
            if token_address:
                st.success(f"买入订单已下达 {trade_amount} SOL!")
            else:
                st.error("请输入代币地址")
    
    with col2:
        if st.button("🔴 卖出"):
            if token_address:
                st.success(f"卖出订单已下达!")
            else:
                st.error("请输入代币地址")
    
    st.sidebar.divider()
    
    # Settings
    st.sidebar.subheader("⚙️ 设置")
    
    refresh_interval = st.sidebar.slider("刷新间隔 (秒)", 10, 300, 30)
    
    if st.sidebar.button("🔄 强制刷新"):
        st.rerun()

def render_discovery_tab(dashboard_manager):
    """Render the discovery tab"""
    st.header("🔍 代币发现")
    
    # Get discovered tokens
    tokens_df = dashboard_manager.get_discovered_tokens()
    
    if tokens_df.empty:
        st.info("尚未发现代币。请从侧边栏开始发现。")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_tokens = len(tokens_df)
        st.metric("总代币数", total_tokens)
    
    with col2:
        meme_tokens = len(tokens_df[tokens_df['Status'] == 'approved'])
        st.metric("Meme代币", meme_tokens)
    
    with col3:
        approved_tokens = len(tokens_df[tokens_df['Status'] == 'approved'])
        st.metric("已批准", approved_tokens)
    
    with col4:
        trading_tokens = len(tokens_df[tokens_df['Status'] == 'trading'])
        st.metric("交易中", trading_tokens)
    
    st.divider()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("按状态筛选", ["全部"] + list(tokens_df['Status'].unique()))
    
    with col2:
        type_filter = st.selectbox("按类型筛选", ["全部", "仅Meme代币", "非Meme代币"])
    
    with col3:
        min_volume = st.number_input("最小24小时交易量 ($)", min_value=0, value=1000000)
    
    # Apply filters
    filtered_df = tokens_df.copy()
    
    if status_filter != "全部":
        filtered_df = filtered_df[filtered_df['Status'] == status_filter]
    
    if type_filter == "仅Meme代币":
        filtered_df = filtered_df[filtered_df['Status'] == 'approved']
    elif type_filter == "非Meme代币":
        filtered_df = filtered_df[filtered_df['Status'] != 'approved']
    
    filtered_df = filtered_df[filtered_df['Volume24h'] >= min_volume]
    
    st.subheader(f"发现的代币 ({len(filtered_df)} 个)")
    
    # Display table
    if not filtered_df.empty:
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "Price": st.column_config.NumberColumn("价格", format="$%.6f"),
                "Volume24h": st.column_config.NumberColumn("24h交易量", format="$%.0f"),
                "FDV": st.column_config.NumberColumn("FDV", format="$%.0f"),
                "Twitter Score": st.column_config.NumberColumn("Twitter评分", format="%.1f"),
                "RugCheck Score": st.column_config.NumberColumn("RugCheck评分", format="%.1f"),
            }
        )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Volume chart
            fig_volume = px.bar(
                filtered_df.head(10),
                x='Symbol',
                y='Volume24h',
                title="前10个代币24小时交易量",
                color='Volume24h',
                color_continuous_scale='Viridis'
            )
            fig_volume.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_volume, use_container_width=True)
        
        with col2:
            # Status distribution
            status_counts = filtered_df['Status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="代币状态分布"
            )
            st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("没有符合条件的代币。")

def render_trades_tab(dashboard_manager):
    """Render the trades tab"""
    st.header("📈 交易历史")
    
    # Get trades data
    trades_df = dashboard_manager.get_trades_data()
    
    if trades_df.empty:
        st.info("未找到交易记录。交易执行后将在此显示。")
        return
    
    # Convert timestamp to datetime
    trades_df['Timestamp'] = pd.to_datetime(trades_df['Timestamp'])
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trades = len(trades_df)
        st.metric("总交易数", total_trades)
    
    with col2:
        successful_trades = len(trades_df[trades_df['Success'] == True])
        st.metric("成功交易", successful_trades)
    
    with col3:
        success_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0
        st.metric("成功率", f"{success_rate:.1f}%")
    
    with col4:
        total_volume = trades_df['Amount'].sum() if not trades_df.empty else 0
        st.metric("总交易量", f"{total_volume:.4f} SOL")
    
    st.divider()
    
    # Display table
    st.subheader(f"交易记录 ({len(trades_df)} 条)")
    
    if not trades_df.empty:
        st.dataframe(
            trades_df,
            use_container_width=True,
            column_config={
                "Amount": st.column_config.NumberColumn("数量", format="%.4f SOL"),
                "Price": st.column_config.NumberColumn("价格", format="$%.6f"),
                "Confidence": st.column_config.NumberColumn("置信度", format="%.1f%%"),
            }
        )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # P&L over time
            if len(trades_df) > 1:
                fig_pnl = px.line(
                    trades_df,
                    x='Timestamp',
                    y='Amount',
                    color='Type',
                    title="交易量趋势",
                    markers=True
                )
                st.plotly_chart(fig_pnl, use_container_width=True)
        
        with col2:
            # Success rate by type
            success_by_type = trades_df.groupby('Type')['Success'].mean() * 100
            fig_success = px.bar(
                x=success_by_type.index,
                y=success_by_type.values,
                title="各类型交易成功率",
                labels={'x': '交易类型', 'y': '成功率 (%)'}
            )
            st.plotly_chart(fig_success, use_container_width=True)
    else:
        st.info("没有符合条件的交易记录。")

def render_positions_tab(dashboard_manager):
    """Render the positions tab"""
    st.header("💼 活跃持仓")
    
    # Get positions data
    positions_df = dashboard_manager.get_positions_data()
    
    if positions_df.empty:
        st.info("无活跃持仓。交易执行后将在此显示持仓信息。")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        active_positions = len(positions_df)
        st.metric("活跃持仓", active_positions)
    
    with col2:
        total_value = positions_df['P&L'].sum() if not positions_df.empty else 0
        st.metric("总价值", f"${total_value:.2f}")
    
    with col3:
        avg_hold_time = positions_df['Hold Time'].mean() if not positions_df.empty else 0
        st.metric("平均持仓时间", f"{avg_hold_time:.1f} 小时")
    
    with col4:
        profitable_positions = len(positions_df[positions_df['P&L'] > 0]) if not positions_df.empty else 0
        st.metric("盈利", f"{profitable_positions}/{active_positions}")
    
    st.divider()
    
    # Display table
    st.subheader("持仓详情")
    if not positions_df.empty:
        st.dataframe(
            positions_df,
            use_container_width=True,
            column_config={
                "Entry Price": st.column_config.NumberColumn("入场价格", format="$%.6f"),
                "Current Price": st.column_config.NumberColumn("当前价格", format="$%.6f"),
                "P&L": st.column_config.NumberColumn("盈亏", format="$%.2f"),
                "P&L %": st.column_config.NumberColumn("盈亏%", format="%.2f%%"),
                "Hold Time": st.column_config.NumberColumn("持仓时间", format="%.1f 小时"),
                "Confidence": st.column_config.NumberColumn("置信度", format="%.1f%%"),
            }
        )
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # P&L distribution
            fig_pnl = px.histogram(
                positions_df,
                x='P&L',
                title="盈亏分布",
                nbins=20
            )
            st.plotly_chart(fig_pnl, use_container_width=True)
        
        with col2:
            # Confidence vs Hold Time
            fig_confidence = px.scatter(
                positions_df,
                x='Hold Time',
                y='Confidence',
                color='P&L',
                title="置信度 vs 持仓时间",
                color_continuous_scale='RdYlGn'
            )
            st.plotly_chart(fig_confidence, use_container_width=True)
    else:
        st.info("没有持仓数据。")

def render_safety_tab(dashboard_manager):
    """Render the safety tab"""
    st.header("🛡️ 安全分析")
    
    # Get safety data
    safety_df = dashboard_manager.get_safety_data()
    
    if safety_df.empty:
        st.info("暂无安全数据。开始发现以查看 RugCheck 分析。")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_analyzed = len(safety_df)
        st.metric("总分析数", total_analyzed)
    
    with col2:
        good_ratings = len(safety_df[safety_df['RugCheck Score'] >= 70])
        st.metric("良好/优秀", good_ratings)
    
    with col3:
        bad_ratings = len(safety_df[safety_df['RugCheck Score'] < 50])
        st.metric("不良/危险", bad_ratings)
    
    with col4:
        safety_rate = (good_ratings / total_analyzed * 100) if total_analyzed > 0 else 0
        st.metric("安全率", f"{safety_rate:.1f}%")
    
    st.divider()
    
    # Safety pie chart
    st.subheader("安全评级分布")
    
    # Categorize scores
    def categorize_score(score):
        if score >= 80:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 50:
            return "一般"
        else:
            return "危险"
    
    safety_df['Category'] = safety_df['RugCheck Score'].apply(categorize_score)
    category_counts = safety_df['Category'].value_counts()
    
    fig_safety = px.pie(
        values=category_counts.values,
        names=category_counts.index,
        title="RugCheck 安全评级分布",
        color_discrete_map={
            "优秀": "#00ff00",
            "良好": "#90ee90", 
            "一般": "#ffa500",
            "危险": "#ff0000"
        }
    )
    st.plotly_chart(fig_safety, use_container_width=True)
    
    # Safety tips
    st.subheader("安全提示")
    st.markdown("""
    - ✅ **良好/优秀**: 安全交易
    - ⚠️ **一般**: 谨慎交易
    - ❌ **较差/不良**: 避免交易
    - 🚨 **危险/跑路**: 高风险跑路
    """)
    
    # Recent warnings
    st.subheader("最近警告")
    bad_tokens = safety_df[safety_df['RugCheck Score'] < 50]
    if not bad_tokens.empty:
        for _, token in bad_tokens.iterrows():
            st.warning(f"⚠️ {token['Symbol']} - 评分: {token['RugCheck Score']:.1f}")
    else:
        st.success("✅ 无安全警告")

def main():
    """Main dashboard function"""
    # Initialize dashboard manager
    if 'dashboard_manager' not in st.session_state:
        st.session_state.dashboard_manager = CloudDashboardManager()
    
    dashboard_manager = st.session_state.dashboard_manager
    
    # Main header
    st.markdown('<h1 class="main-header chinese-text">🤖 Memecoin 交易机器人仪表板</h1>', unsafe_allow_html=True)
    
    # Render sidebar
    render_sidebar(dashboard_manager)
    
    # Auto-refresh logic
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    refresh_interval = 30  # seconds
    if time.time() - st.session_state.last_refresh > refresh_interval:
        st.session_state.last_refresh = time.time()
        st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 发现", "📈 交易", "💼 持仓", "🛡️ 安全"])
    
    with tab1:
        render_discovery_tab(dashboard_manager)
    
    with tab2:
        render_trades_tab(dashboard_manager)
    
    with tab3:
        render_positions_tab(dashboard_manager)
    
    with tab4:
        render_safety_tab(dashboard_manager)

if __name__ == "__main__":
    main()
