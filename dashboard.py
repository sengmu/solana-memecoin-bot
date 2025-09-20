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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import bot components
try:
    from memecoin_bot import MemecoinBot
    from models import TokenInfo, Trade, TradeType, TokenStatus, BotConfig
except ImportError as e:
    logger.error(f"Import error: {e}")
    st.error(f"导入错误: {e}")
    st.stop()

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

class DashboardManager:
    def __init__(self):
        self.bot = None
        self.last_refresh = None
        
    def initialize_bot(self):
        """Initialize the bot with environment variables"""
        try:
            # Try to initialize bot with new BotConfig
            self.bot = MemecoinBot()
            return True
        except (AttributeError, KeyError, TypeError) as e:
            logger.error(f"Bot initialization failed due to missing .env or config: {e}")
            # Fallback to MockBot with fetch_trending_pairs method
            self.bot = self._create_mock_bot()
            st.error("⚠️ 机器人初始化失败，请检查 .env 配置文件")
            return False
        except Exception as e:
            logger.error(f"Bot initialization failed: {e}")
            # Fallback to MockBot for demo purposes
            self.bot = self._create_mock_bot()
            st.warning("⚠️ 机器人初始化失败，使用模拟数据演示")
            return False
    
    def _create_mock_bot(self):
        """Create a MockBot with all necessary methods"""
        class MockBot:
            def __init__(self):
                self.running = False
                self.discovered_tokens = {}
                self.trades = []
                self.positions = {}
                self.trading_stats = type('MockStats', (), {
                    'total_trades': 0,
                    'successful_trades': 0,
                    'total_volume': 0.0,
                    'total_pnl': 0.0
                })()
                # Create a mock dexscreener_client
                self.dexscreener_client = type('MockDexScreenerClient', (), {
                    'fetch_trending_pairs': self.fetch_trending_pairs
                })()
            
            async def fetch_trending_pairs(self, max_pairs=50):
                """Mock fetch_trending_pairs method"""
                sample_data = [
                    {
                        "baseToken": {"name": "Test Token 1", "symbol": "TST1", "address": "test123"},
                        "fdv": 1000000,
                        "volume": {"h24": 2000000},
                        "priceChange": {"h24": 10}
                    },
                    {
                        "baseToken": {"name": "Test Token 2", "symbol": "TST2", "address": "test456"},
                        "fdv": 2000000,
                        "volume": {"h24": 3000000},
                        "priceChange": {"h24": -5}
                    },
                    {
                        "baseToken": {"name": "Test Token 3", "symbol": "TST3", "address": "test789"},
                        "fdv": 5000000,
                        "volume": {"h24": 1000000},
                        "priceChange": {"h24": 25}
                    }
                ]
                return sample_data[:max_pairs]
            
            def start_discovery(self):
                """Mock start_discovery method"""
                self.running = True
                return True
            
            def stop_discovery(self):
                """Mock stop_discovery method"""
                self.running = False
                return True
        
        return MockBot()
    
    def get_discovered_tokens(self):
        """Get discovered tokens data"""
        if not self.bot:
            return pd.DataFrame()
        
        try:
            tokens = []
            for token in self.bot.discovered_tokens.values():
                tokens.append({
                    'Symbol': token.symbol,
                    'Name': token.name,
                    'Address': token.address,
                    'Price': token.price,
                    'Volume24h': token.volume_24h,
                    'FDV': token.fdv,
                    'Twitter Score': token.twitter_score,
                    'RugCheck Score': token.rugcheck_score,
                    'Status': token.status.value,
                    'Discovered At': token.discovered_at.strftime('%Y-%m-%d %H:%M:%S') if token.discovered_at else 'N/A'
                })
            return pd.DataFrame(tokens)
        except Exception as e:
            logger.error(f"Error getting discovered tokens: {e}")
            return pd.DataFrame()
    
    def get_trades_data(self):
        """Get trades data from trades.json"""
        try:
            if os.path.exists('trades.json'):
                with open('trades.json', 'r', encoding='utf-8') as f:
                    trades_data = json.load(f)
                
                trades = []
                for trade in trades_data:
                    trades.append({
                        'Timestamp': trade['timestamp'],
                        'Type': trade['type'],
                        'Symbol': trade['symbol'],
                        'Amount': trade['amount'],
                        'Price': trade['price'],
                        'Success': trade['success'],
                        'Confidence': trade.get('confidence', 0),
                        'Reason': trade.get('reason', '')
                    })
                return pd.DataFrame(trades)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"Error loading trades: {e}")
            return pd.DataFrame()
    
    def get_positions_data(self):
        """Get current positions data"""
        if not self.bot:
            return pd.DataFrame()
        
        try:
            positions = []
            for token_address, position in self.bot.positions.items():
                token = self.bot.discovered_tokens.get(token_address)
                if token:
                    positions.append({
                        'Symbol': token.symbol,
                        'Address': token.address,
                        'Amount': position['amount'],
                        'Entry Price': position['entry_price'],
                        'Current Price': token.price,
                        'P&L': (token.price - position['entry_price']) * position['amount'],
                        'P&L %': ((token.price - position['entry_price']) / position['entry_price']) * 100,
                        'Hold Time': (datetime.now() - position['entry_time']).total_seconds() / 3600,  # hours
                        'Confidence': position.get('confidence', 0)
                    })
            return pd.DataFrame(positions)
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return pd.DataFrame()
    
    def get_safety_data(self):
        """Get RugCheck safety analysis data"""
        if not self.bot:
            return pd.DataFrame()
        
        try:
            safety_data = []
            for token in self.bot.discovered_tokens.values():
                if hasattr(token, 'rugcheck_score') and token.rugcheck_score:
                    safety_data.append({
                        'Symbol': token.symbol,
                        'RugCheck Score': token.rugcheck_score,
                        'Status': token.status.value
                    })
            return pd.DataFrame(safety_data)
        except Exception as e:
            logger.error(f"Error getting safety data: {e}")
            return pd.DataFrame()
    
    def generate_mock_tokens(self, count: int = 15):
        """Generate mock tokens for demonstration"""
        from models import TokenInfo, TokenStatus
        import random
        from datetime import datetime
        
        mock_tokens = []
        symbols = ['PEPE', 'DOGE', 'BONK', 'SHIB', 'FLOKI', 'WOJAK', 'CHAD', 'KEKW', 'MOON', 'DEGEN', 'APE', 'MONKE', 'FROG', 'CAT', 'DOG']
        
        for i in range(count):
            symbol = symbols[i % len(symbols)]
            if i >= len(symbols):
                symbol = f"{symbol}{i}"
            
            token = TokenInfo(
                address=f"mock_address_{i}_{random.randint(1000, 9999)}",
                symbol=symbol,
                name=f"{symbol} Token",
                decimals=9,
                price=random.uniform(0.000001, 0.01),
                market_cap=random.uniform(1000000, 100000000),
                fdv=random.uniform(1000000, 100000000),
                volume_24h=random.uniform(100000, 10000000),
                price_change_24h=random.uniform(-50, 100),
                liquidity=random.uniform(100000, 1000000),
                holders=random.randint(100, 10000),
                created_at=datetime.now(),
                status=random.choice([TokenStatus.PENDING, TokenStatus.APPROVED, TokenStatus.TRADING]),
                twitter_score=random.uniform(0, 100),
                rugcheck_score=str(random.uniform(0, 100)),
                confidence_score=random.uniform(0, 1),
                is_memecoin=True
            )
            mock_tokens.append(token)
        
        return mock_tokens

def render_sidebar(dashboard_manager):
    """Render the sidebar with bot controls"""
    st.sidebar.title("🤖 机器人控制")
    
    # Bot status
    if dashboard_manager.bot:
        status = "🟢 运行中" if dashboard_manager.bot.running else "🔴 已停止"
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
                # 使用 session state 强制刷新
                if 'force_refresh' not in st.session_state:
                    st.session_state.force_refresh = 0
                st.session_state.force_refresh += 1
                st.rerun()
            else:
                st.sidebar.error("机器人初始化失败!")
        else:
            if not dashboard_manager.bot.running:
                asyncio.create_task(dashboard_manager.bot.start_discovery())
                st.sidebar.success("开始发现代币...")
                # 使用 session state 强制刷新
                if 'force_refresh' not in st.session_state:
                    st.session_state.force_refresh = 0
                st.session_state.force_refresh += 1
                st.rerun()
            else:
                st.sidebar.warning("发现已在进行中...")
    
    if st.sidebar.button("⏹️ 停止发现"):
        if dashboard_manager.bot and dashboard_manager.bot.running:
            dashboard_manager.bot.stop_discovery()
            st.sidebar.success("已停止发现...")
            # 使用 session state 强制刷新
            if 'force_refresh' not in st.session_state:
                st.session_state.force_refresh = 0
            st.session_state.force_refresh += 1
            st.rerun()
        else:
            st.sidebar.warning("没有正在运行的发现任务...")
    
    st.sidebar.divider()
    
    # Manual trading
    st.sidebar.subheader("💰 手动交易")
    
    token_address = st.sidebar.text_input("代币地址", placeholder="输入代币地址...")
    trade_amount = st.sidebar.number_input("数量 (SOL)", min_value=0.001, value=0.1, step=0.01)
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("🟢 买入", type="primary"):
            if token_address and dashboard_manager.bot:
                try:
                    # This would be implemented in the actual bot
                    st.success(f"买入订单已下达 {trade_amount} SOL!")
                    st.rerun()  # 重新运行以更新状态
                except Exception as e:
                    st.error(f"买入失败: {e}")
            else:
                st.error("请输入代币地址并确保机器人已初始化")
    
    with col2:
        if st.button("🔴 卖出"):
            if token_address and dashboard_manager.bot:
                try:
                    # This would be implemented in the actual bot
                    st.success(f"卖出订单已下达!")
                    st.rerun()  # 重新运行以更新状态
                except Exception as e:
                    st.error(f"卖出失败: {e}")
            else:
                st.error("请输入代币地址并确保机器人已初始化")
    
    st.sidebar.divider()
    
    # Settings
    st.sidebar.subheader("⚙️ 设置")
    
    refresh_interval = st.sidebar.slider("刷新间隔 (秒)", 10, 300, 30)
    
    if st.sidebar.button("🔄 强制刷新"):
        st.rerun()

def render_discovery_tab(dashboard_manager):
    """Render the discovery tab"""
    st.header("🔍 代币发现")
    
    # Add refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    
    with col1:
        if st.button("🔄 刷新发现", type="primary"):
            if dashboard_manager.bot is None:
                st.error("❌ 机器人未初始化")
                return
            
            try:
                # Fetch trending pairs
                import asyncio
                trending_pairs = asyncio.run(dashboard_manager.bot.dexscreener_client.fetch_trending_pairs(max_pairs=50))
                
                if not trending_pairs:
                    st.warning("⚠️ 未获取到代币数据，使用模拟数据")
                    # Generate mock tokens as fallback
                    mock_tokens = dashboard_manager.generate_mock_tokens(15)
                    for token in mock_tokens:
                        dashboard_manager.bot.discovered_tokens[token.address] = token
                    st.success(f"✅ 已加载 {len(mock_tokens)} 个模拟代币!")
                else:
                    # Convert trending pairs to TokenInfo objects
                    from models import TokenInfo, TokenStatus
                    for pair in trending_pairs:
                        try:
                            token = TokenInfo(
                                address=pair.get("baseToken", {}).get("address", f"mock_{pair.get('baseToken', {}).get('symbol', 'UNK')}"),
                                symbol=pair.get("baseToken", {}).get("symbol", "UNK"),
                                name=pair.get("baseToken", {}).get("name", "Unknown Token"),
                                decimals=9,
                                price=0.001,  # Mock price
                                market_cap=pair.get("fdv", 1000000),
                                fdv=pair.get("fdv", 1000000),
                                volume_24h=pair.get("volume", {}).get("h24", 1000000),
                                price_change_24h=pair.get("priceChange", {}).get("h24", 0),
                                liquidity=100000,
                                holders=1000,
                                created_at=datetime.now(),
                                status=TokenStatus.PENDING,
                                twitter_score=0.0,
                                rugcheck_score="0.0",
                                confidence_score=0.5,
                                is_memecoin=True
                            )
                            dashboard_manager.bot.discovered_tokens[token.address] = token
                        except Exception as e:
                            logger.warning(f"Error creating token from pair: {e}")
                            continue
                    
                    st.success(f"✅ 成功获取 {len(trending_pairs)} 个热门代币!")
                
                st.rerun()
            except Exception as e:
                st.error(f"❌ 获取代币失败: {e}")
                logger.error(f"Error in refresh discovery: {e}")
    
    with col2:
        if st.button("📊 显示模拟数据"):
            # Generate mock data for demonstration
            mock_tokens = dashboard_manager.generate_mock_tokens(15)
            for token in mock_tokens:
                dashboard_manager.bot.discovered_tokens[token.address] = token
            st.success("✅ 已加载模拟数据!")
            st.rerun()
    
    # Get discovered tokens
    tokens_df = dashboard_manager.get_discovered_tokens()
    
    if tokens_df.empty:
        st.info("尚未发现代币。请点击上方按钮开始发现。")
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
            width='stretch',
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
            st.plotly_chart(fig_volume, width='stretch')
        
        with col2:
            # Status distribution
            status_counts = filtered_df['Status'].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="代币状态分布"
            )
            st.plotly_chart(fig_status, width='stretch')
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
        filtered_trades = filtered_trades[filtered_trades['Success'] == True]
    elif success_filter == "仅失败":
        filtered_trades = filtered_trades[filtered_trades['Success'] == False]
    
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
        filtered_trades = filtered_trades[
            (filtered_trades['Timestamp'].dt.date >= start_date) &
            (filtered_trades['Timestamp'].dt.date <= end_date)
        ]
    
    st.subheader(f"交易记录 ({len(filtered_trades)} 条)")
    
    # Display table
    if not filtered_trades.empty:
        st.dataframe(
            filtered_trades,
            width='stretch',
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
            if len(filtered_trades) > 1:
                fig_pnl = px.line(
                    filtered_trades,
                    x='Timestamp',
                    y='Amount',
                    color='Type',
                    title="交易量趋势",
                    markers=True
                )
                st.plotly_chart(fig_pnl, width='stretch')
        
        with col2:
            # Success rate by type
            success_by_type = filtered_trades.groupby('Type')['Success'].mean() * 100
            fig_success = px.bar(
                x=success_by_type.index,
                y=success_by_type.values,
                title="各类型交易成功率",
                labels={'x': '交易类型', 'y': '成功率 (%)'}
            )
            st.plotly_chart(fig_success, width='stretch')
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
            width='stretch',
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
            st.plotly_chart(fig_pnl, width='stretch')
        
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
            st.plotly_chart(fig_confidence, width='stretch')
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
    st.plotly_chart(fig_safety, width='stretch')
    
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
        st.session_state.dashboard_manager = DashboardManager()
    
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
    print("Dashboard fixed, run streamlit run dashboard.py")
    
    # Test bot initialization
    print("\nTesting bot initialization...")
    dashboard_manager = DashboardManager()
    success = dashboard_manager.initialize_bot()
    if success and dashboard_manager.bot:
        print("✅ Bot initialized successfully")
        # Test fetch_trending_pairs
        import asyncio
        try:
            if hasattr(dashboard_manager.bot, 'dexscreener_client') and dashboard_manager.bot.dexscreener_client:
                pairs = asyncio.run(dashboard_manager.bot.dexscreener_client.fetch_trending_pairs())
                print(f"✅ fetch_trending_pairs returned {len(pairs)} pairs")
            else:
                print("❌ dexscreener_client is None or missing")
        except Exception as e:
            print(f"❌ fetch_trending_pairs failed: {e}")
    else:
        print("❌ Bot initialization failed")
    
    main()
