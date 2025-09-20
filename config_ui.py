#!/usr/bin/env python3
"""
交易配置可视化界面
"""

import streamlit as st
import os
import json
from dotenv import load_dotenv
from datetime import datetime
import subprocess
import sys

# 页面配置
st.set_page_config(
    page_title="交易配置工具",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
        font-size: 2.5rem;
    }
    .config-section {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .status-success {
        color: #28a745;
        font-weight: bold;
    }
    .status-error {
        color: #dc3545;
        font-weight: bold;
    }
    .status-warning {
        color: #ffc107;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .config-item {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

class ConfigManager:
    def __init__(self):
        self.env_file = '.env'
        self.load_config()
    
    def load_config(self):
        """加载当前配置"""
        load_dotenv()
        self.config = {
            'PRIVATE_KEY': os.getenv('PRIVATE_KEY', ''),
            'SOLANA_RPC_URL': os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com'),
            'SOLANA_WS_URL': os.getenv('SOLANA_WS_URL', 'wss://api.mainnet-beta.solana.com'),
            'MAX_POSITION_SIZE': os.getenv('MAX_POSITION_SIZE', '0.01'),
            'MIN_VOLUME_24H': os.getenv('MIN_VOLUME_24H', '1000000'),
            'MIN_FDV': os.getenv('MIN_FDV', '100000'),
            'MAX_SLIPPAGE': os.getenv('MAX_SLIPPAGE', '0.05'),
            'DEFAULT_SLIPPAGE': os.getenv('DEFAULT_SLIPPAGE', '0.01'),
            'TWITTER_BEARER_TOKEN': os.getenv('TWITTER_BEARER_TOKEN', ''),
            'LEADER_WALLET_ADDRESS': os.getenv('LEADER_WALLET_ADDRESS', ''),
            'COPY_TRADING_ENABLED': os.getenv('COPY_TRADING_ENABLED', 'false'),
            'MIN_CONFIDENCE_SCORE': os.getenv('MIN_CONFIDENCE_SCORE', '70'),
            'MAX_DAILY_LOSS': os.getenv('MAX_DAILY_LOSS', '0.1'),
            'STOP_LOSS_PERCENTAGE': os.getenv('STOP_LOSS_PERCENTAGE', '0.2'),
            'TAKE_PROFIT_PERCENTAGE': os.getenv('TAKE_PROFIT_PERCENTAGE', '0.5'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'LOG_TO_FILE': os.getenv('LOG_TO_FILE', 'true'),
        }
    
    def save_config(self, new_config):
        """保存配置到.env文件"""
        try:
            with open(self.env_file, 'w') as f:
                for key, value in new_config.items():
                    f.write(f"{key}={value}\n")
            return True
        except Exception as e:
            st.error(f"保存配置失败: {e}")
            return False
    
    def validate_config(self):
        """验证配置"""
        errors = []
        warnings = []
        
        # 必需配置检查
        if not self.config['PRIVATE_KEY'] or self.config['PRIVATE_KEY'] == 'your_wallet_private_key_here':
            errors.append("PRIVATE_KEY 未配置")
        
        if not self.config['SOLANA_RPC_URL'] or self.config['SOLANA_RPC_URL'] == 'your_rpc_url_here':
            errors.append("SOLANA_RPC_URL 未配置")
        
        # 数值配置检查
        try:
            float(self.config['MAX_POSITION_SIZE'])
            float(self.config['MIN_VOLUME_24H'])
            float(self.config['MIN_FDV'])
            float(self.config['MAX_SLIPPAGE'])
            float(self.config['DEFAULT_SLIPPAGE'])
        except ValueError:
            errors.append("数值配置格式错误")
        
        # 警告检查
        if float(self.config['MAX_POSITION_SIZE']) > 1.0:
            warnings.append("最大单笔交易金额较大，请谨慎")
        
        if float(self.config['MIN_VOLUME_24H']) < 100000:
            warnings.append("最小交易量较低，可能增加风险")
        
        return errors, warnings

def render_header():
    """渲染页面头部"""
    # 添加导航链接
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        try:
            st.link_button("📊 返回主仪表板", "http://localhost:8501")
        except AttributeError:
            st.markdown("[📊 返回主仪表板](http://localhost:8501)")
    
    with col2:
        st.markdown('<h1 class="main-header">⚙️ 交易配置工具</h1>', unsafe_allow_html=True)
    
    with col3:
        if st.button("🔄 刷新页面"):
            st.rerun()
    
    st.markdown("---")

def render_config_status(config_manager):
    """渲染配置状态"""
    st.subheader("📊 配置状态")
    
    errors, warnings = config_manager.validate_config()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if not errors:
            st.markdown('<div class="metric-card"><h3>✅ 配置完整</h3><p>所有必需配置已设置</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card" style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);"><h3>❌ 配置不完整</h3><p>需要修复错误</p></div>', unsafe_allow_html=True)
    
    with col2:
        if warnings:
            st.markdown('<div class="metric-card" style="background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);"><h3>⚠️ 有警告</h3><p>建议检查配置</p></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="metric-card"><h3>✅ 无警告</h3><p>配置合理</p></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card"><h3>🔧 配置项</h3><p>17 个配置项</p></div>', unsafe_allow_html=True)
    
    # 显示错误和警告
    if errors:
        st.error("❌ 配置错误:")
        for error in errors:
            st.write(f"• {error}")
    
    if warnings:
        st.warning("⚠️ 配置警告:")
        for warning in warnings:
            st.write(f"• {warning}")

def render_wallet_config(config_manager):
    """渲染钱包配置"""
    st.subheader("🔑 钱包配置")
    
    with st.expander("钱包设置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            private_key = st.text_input(
                "私钥 (Private Key)",
                value=config_manager.config['PRIVATE_KEY'],
                type="password",
                help="您的 Solana 钱包私钥，用于签名交易"
            )
            
            rpc_url = st.text_input(
                "RPC 节点地址",
                value=config_manager.config['SOLANA_RPC_URL'],
                help="Solana RPC 节点地址，推荐使用付费节点"
            )
        
        with col2:
            ws_url = st.text_input(
                "WebSocket 地址",
                value=config_manager.config['SOLANA_WS_URL'],
                help="Solana WebSocket 地址"
            )
            
            # RPC 提供商选择
            rpc_provider = st.selectbox(
                "推荐 RPC 提供商",
                ["公共节点", "Alchemy", "QuickNode", "Helius", "自定义"],
                help="选择 RPC 提供商"
            )
            
            if rpc_provider == "Alchemy":
                st.info("Alchemy: https://www.alchemy.com/solana")
            elif rpc_provider == "QuickNode":
                st.info("QuickNode: https://www.quicknode.com/solana")
            elif rpc_provider == "Helius":
                st.info("Helius: https://helius.xyz/")
    
    # 更新配置
    config_manager.config['PRIVATE_KEY'] = private_key
    config_manager.config['SOLANA_RPC_URL'] = rpc_url
    config_manager.config['SOLANA_WS_URL'] = ws_url

def render_trading_config(config_manager):
    """渲染交易配置"""
    st.subheader("💰 交易配置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 基础参数")
        
        max_position = st.number_input(
            "最大单笔交易金额 (SOL)",
            min_value=0.001,
            max_value=10.0,
            value=float(config_manager.config['MAX_POSITION_SIZE']),
            step=0.001,
            help="单笔交易的最大金额，建议从小额开始"
        )
        
        min_volume = st.number_input(
            "最小24小时交易量 (USD)",
            min_value=1000,
            max_value=10000000,
            value=int(float(config_manager.config['MIN_VOLUME_24H'])),
            step=1000,
            help="代币的最小24小时交易量要求"
        )
        
        min_fdv = st.number_input(
            "最小完全稀释估值 (USD)",
            min_value=1000,
            max_value=10000000,
            value=int(float(config_manager.config['MIN_FDV'])),
            step=1000,
            help="代币的最小完全稀释估值要求"
        )
    
    with col2:
        st.markdown("#### 滑点控制")
        
        max_slippage = st.slider(
            "最大滑点 (%)",
            min_value=0.1,
            max_value=10.0,
            value=float(config_manager.config['MAX_SLIPPAGE']) * 100,
            step=0.1,
            help="交易允许的最大滑点"
        ) / 100
        
        default_slippage = st.slider(
            "默认滑点 (%)",
            min_value=0.1,
            max_value=5.0,
            value=float(config_manager.config['DEFAULT_SLIPPAGE']) * 100,
            step=0.1,
            help="默认使用的滑点"
        ) / 100
        
        st.markdown("#### 风险控制")
        
        max_daily_loss = st.slider(
            "最大日损失 (%)",
            min_value=1.0,
            max_value=50.0,
            value=float(config_manager.config['MAX_DAILY_LOSS']) * 100,
            step=1.0,
            help="每日最大损失百分比"
        ) / 100
    
    # 更新配置
    config_manager.config['MAX_POSITION_SIZE'] = str(max_position)
    config_manager.config['MIN_VOLUME_24H'] = str(min_volume)
    config_manager.config['MIN_FDV'] = str(min_fdv)
    config_manager.config['MAX_SLIPPAGE'] = str(max_slippage)
    config_manager.config['DEFAULT_SLIPPAGE'] = str(default_slippage)
    config_manager.config['MAX_DAILY_LOSS'] = str(max_daily_loss)

def render_advanced_config(config_manager):
    """渲染高级配置"""
    st.subheader("🔧 高级配置")
    
    tab1, tab2, tab3 = st.tabs(["API 配置", "复制交易", "日志设置"])
    
    with tab1:
        twitter_token = st.text_input(
            "Twitter Bearer Token",
            value=config_manager.config['TWITTER_BEARER_TOKEN'],
            type="password",
            help="Twitter API Bearer Token，用于情绪分析"
        )
        config_manager.config['TWITTER_BEARER_TOKEN'] = twitter_token
    
    with tab2:
        st.markdown("### 🤖 复制交易配置")
        
        copy_trading = st.checkbox(
            "启用复制交易",
            value=config_manager.config['COPY_TRADING_ENABLED'].lower() == 'true',
            help="复制其他钱包的交易"
        )
        
        if copy_trading:
            st.info("💡 复制交易功能已启用，机器人将自动跟随指定钱包的交易")
            
            # 主要跟单钱包
            leader_wallet = st.text_input(
                "主要跟单钱包地址",
                value=config_manager.config['LEADER_WALLET_ADDRESS'],
                help="要复制的主要钱包地址（必填）",
                placeholder="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            )
            
            # 多个跟单钱包
            leader_wallets = st.text_area(
                "多个跟单钱包地址（可选）",
                value=config_manager.config.get('LEADER_WALLETS', ''),
                help="多个钱包地址，用逗号分隔。例如：wallet1,wallet2,wallet3",
                placeholder="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM,7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU"
            )
            
            # 跟单比例
            copy_ratio = st.slider(
                "跟单比例",
                min_value=0.1,
                max_value=2.0,
                value=float(config_manager.config.get('COPY_RATIO', '1.0')),
                step=0.1,
                help="跟单比例：1.0 = 100%，0.5 = 50%，2.0 = 200%"
            )
            
            # 最小置信度
            min_confidence = st.slider(
                "最小置信度 (%)",
                min_value=0,
                max_value=100,
                value=int(float(config_manager.config['MIN_CONFIDENCE_SCORE'])),
                help="只有置信度超过此值的交易才会被复制"
            )
            
            # 跟单模式选择
            copy_mode = st.selectbox(
                "跟单模式",
                ["保守模式", "平衡模式", "激进模式"],
                help="选择跟单的激进程度"
            )
            
            # 根据模式调整参数
            if copy_mode == "保守模式":
                st.info("🛡️ 保守模式：只跟单高置信度、小仓位的交易")
                if min_confidence < 80:
                    min_confidence = 80
                if copy_ratio > 0.5:
                    copy_ratio = 0.5
            elif copy_mode == "激进模式":
                st.info("⚡ 激进模式：跟单更多交易，使用更大仓位")
                if min_confidence > 50:
                    min_confidence = 50
                if copy_ratio < 1.0:
                    copy_ratio = 1.0
            
            # 显示当前配置摘要
            st.markdown("### 📊 当前配置摘要")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("跟单比例", f"{copy_ratio*100:.0f}%")
            with col2:
                st.metric("最小置信度", f"{min_confidence}%")
            with col3:
                st.metric("跟单模式", copy_mode)
        
        # 更新配置
        config_manager.config['COPY_TRADING_ENABLED'] = str(copy_trading).lower()
        config_manager.config['LEADER_WALLET_ADDRESS'] = leader_wallet
        config_manager.config['LEADER_WALLETS'] = leader_wallets
        config_manager.config['COPY_RATIO'] = str(copy_ratio)
        config_manager.config['MIN_CONFIDENCE_SCORE'] = str(min_confidence)
    
    with tab3:
        log_level = st.selectbox(
            "日志级别",
            ["DEBUG", "INFO", "WARNING", "ERROR"],
            index=["DEBUG", "INFO", "WARNING", "ERROR"].index(config_manager.config['LOG_LEVEL'])
        )
        
        log_to_file = st.checkbox(
            "保存日志到文件",
            value=config_manager.config['LOG_TO_FILE'].lower() == 'true'
        )
        
        config_manager.config['LOG_LEVEL'] = log_level
        config_manager.config['LOG_TO_FILE'] = str(log_to_file).lower()

def render_risk_management(config_manager):
    """渲染风险管理配置"""
    st.subheader("🛡️ 风险管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        stop_loss = st.slider(
            "止损百分比 (%)",
            min_value=1.0,
            max_value=50.0,
            value=float(config_manager.config['STOP_LOSS_PERCENTAGE']) * 100,
            step=1.0,
            help="触发止损的价格下跌百分比"
        ) / 100
        
        config_manager.config['STOP_LOSS_PERCENTAGE'] = str(stop_loss)
    
    with col2:
        take_profit = st.slider(
            "止盈百分比 (%)",
            min_value=5.0,
            max_value=200.0,
            value=float(config_manager.config['TAKE_PROFIT_PERCENTAGE']) * 100,
            step=5.0,
            help="触发止盈的价格上涨百分比"
        ) / 100
        
        config_manager.config['TAKE_PROFIT_PERCENTAGE'] = str(take_profit)
    
    # 风险提示
    st.info("""
    **风险提示:**
    - 加密货币交易存在高风险，可能导致资金损失
    - 建议从小额资金开始测试
    - 设置合理的止损和止盈
    - 定期监控交易表现
    """)

def render_actions(config_manager):
    """渲染操作按钮"""
    st.subheader("🚀 操作")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 保存配置", type="primary"):
            if config_manager.save_config(config_manager.config):
                st.success("配置已保存！")
                st.rerun()
    
    with col2:
        if st.button("🔄 重新加载"):
            config_manager.load_config()
            st.success("配置已重新加载！")
            st.rerun()
    
    with col3:
        if st.button("✅ 验证配置"):
            errors, warnings = config_manager.validate_config()
            if not errors:
                st.success("配置验证通过！")
            else:
                st.error(f"配置验证失败: {', '.join(errors)}")
    
    with col4:
        if st.button("🚀 启动交易"):
            if not config_manager.validate_config()[0]:  # 没有错误
                st.success("正在启动交易机器人...")
                # 这里可以添加启动逻辑
            else:
                st.error("请先修复配置错误")

def render_config_preview(config_manager):
    """渲染配置预览"""
    st.subheader("📋 配置预览")
    
    with st.expander("查看完整配置", expanded=False):
        config_json = json.dumps(config_manager.config, indent=2, ensure_ascii=False)
        st.code(config_json, language="json")

def main():
    """主函数"""
    config_manager = ConfigManager()
    
    render_header()
    render_config_status(config_manager)
    
    st.markdown("---")
    
    # 配置表单
    render_wallet_config(config_manager)
    render_trading_config(config_manager)
    render_advanced_config(config_manager)
    render_risk_management(config_manager)
    
    st.markdown("---")
    
    # 操作按钮
    render_actions(config_manager)
    
    # 配置预览
    render_config_preview(config_manager)

if __name__ == "__main__":
    main()
