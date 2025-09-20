#!/usr/bin/env python3
"""
配置检查脚本 - 验证交易环境是否正确配置
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """检查环境变量配置"""
    print("🔍 检查环境配置...")
    
    # 加载环境变量
    load_dotenv()
    
    # 必需的环境变量
    required_vars = {
        'PRIVATE_KEY': 'Solana 钱包私钥',
        'SOLANA_RPC_URL': 'Solana RPC 节点地址',
    }
    
    # 可选的环境变量
    optional_vars = {
        'TWITTER_BEARER_TOKEN': 'Twitter API Bearer Token',
        'MAX_POSITION_SIZE': '最大单笔交易金额',
        'MIN_VOLUME_24H': '最小24小时交易量',
        'MIN_FDV': '最小完全稀释估值',
    }
    
    print("\n📋 必需配置:")
    all_required_ok = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}_here':
            print(f"  ✅ {var}: 已配置 ({description})")
        else:
            print(f"  ❌ {var}: 未配置 ({description})")
            all_required_ok = False
    
    print("\n📋 可选配置:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value and value != f'your_{var.lower()}_here':
            print(f"  ✅ {var}: 已配置 ({description})")
        else:
            print(f"  ⚠️  {var}: 未配置 ({description})")
    
    return all_required_ok

def check_wallet_connection():
    """检查钱包连接"""
    print("\n🔑 检查钱包连接...")
    
    try:
        from solana.rpc.api import Client
        from solders.keypair import Keypair
        import base58
        
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key or private_key == 'your_wallet_private_key_here':
            print("  ❌ 私钥未配置")
            return False
        
        try:
            # 验证私钥格式
            keypair = Keypair.from_base58_string(private_key)
            print(f"  ✅ 钱包地址: {keypair.pubkey()}")
            
            # 测试 RPC 连接
            rpc_url = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
            client = Client(rpc_url)
            
            # 获取账户信息
            account_info = client.get_account_info(keypair.pubkey())
            if account_info.value:
                balance = client.get_balance(keypair.pubkey())
                print(f"  ✅ 账户余额: {balance.value / 1e9:.4f} SOL")
            else:
                print("  ⚠️  账户不存在或余额为0")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 钱包连接失败: {e}")
            return False
            
    except ImportError as e:
        print(f"  ❌ 缺少依赖: {e}")
        print("  请运行: pip install -r requirements.txt")
        return False

def check_trading_config():
    """检查交易配置"""
    print("\n💰 检查交易配置...")
    
    config_vars = {
        'MAX_POSITION_SIZE': '最大单笔交易金额 (SOL)',
        'MIN_VOLUME_24H': '最小24小时交易量 (USD)',
        'MIN_FDV': '最小完全稀释估值 (USD)',
        'MAX_SLIPPAGE': '最大滑点 (%)',
        'DEFAULT_SLIPPAGE': '默认滑点 (%)',
    }
    
    for var, description in config_vars.items():
        value = os.getenv(var)
        if value:
            try:
                float_value = float(value)
                print(f"  ✅ {var}: {float_value} ({description})")
            except ValueError:
                print(f"  ❌ {var}: 无效数值 '{value}' ({description})")
        else:
            print(f"  ⚠️  {var}: 使用默认值 ({description})")

def main():
    """主函数"""
    print("🤖 Solana Memecoin 交易机器人配置检查")
    print("=" * 50)
    
    # 检查环境变量
    env_ok = check_environment()
    
    # 检查钱包连接
    wallet_ok = check_wallet_connection()
    
    # 检查交易配置
    check_trading_config()
    
    print("\n" + "=" * 50)
    if env_ok and wallet_ok:
        print("🎉 配置检查通过！可以开始交易了。")
        print("\n📝 下一步:")
        print("  1. 调整交易参数（如需要）")
        print("  2. 运行: python3 run_dashboard.py")
        print("  3. 在仪表板中点击 '开始发现'")
    else:
        print("❌ 配置检查失败！请修复上述问题。")
        print("\n📝 需要修复:")
        if not env_ok:
            print("  - 配置必需的环境变量")
        if not wallet_ok:
            print("  - 检查私钥和 RPC 连接")
        print("\n📖 详细说明请查看: TRADING_SETUP.md")
    
    return env_ok and wallet_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
