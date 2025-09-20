#!/usr/bin/env python3
"""
交易模式启动脚本
"""

import os
import sys
from dotenv import load_dotenv

def main():
    """启动交易模式"""
    print("🚀 启动 Solana Memecoin 交易机器人")
    print("=" * 50)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查配置
    print("🔍 检查配置...")
    
    private_key = os.getenv('PRIVATE_KEY')
    if not private_key or private_key == 'your_wallet_private_key_here':
        print("❌ 错误: 未配置私钥")
        print("\n📝 请先配置 .env 文件:")
        print("  1. 复制 env.example 到 .env")
        print("  2. 编辑 .env 文件，设置您的私钥")
        print("  3. 运行: python3 check_config.py 验证配置")
        return False
    
    rpc_url = os.getenv('SOLANA_RPC_URL', 'https://api.mainnet-beta.solana.com')
    print(f"✅ RPC 节点: {rpc_url}")
    
    # 显示交易参数
    print("\n💰 交易参数:")
    max_position = os.getenv('MAX_POSITION_SIZE', '0.01')
    min_volume = os.getenv('MIN_VOLUME_24H', '1000000')
    min_fdv = os.getenv('MIN_FDV', '100000')
    
    print(f"  📊 最大单笔交易: {max_position} SOL")
    print(f"  📈 最小24h交易量: ${min_volume:,}")
    print(f"  💎 最小FDV: ${min_fdv:,}")
    
    # 风险提示
    print("\n⚠️  风险提示:")
    print("  - 加密货币交易存在高风险")
    print("  - 建议从小额资金开始测试")
    print("  - 设置合理的止损和止盈")
    print("  - 定期监控交易表现")
    
    # 确认启动
    print("\n🤖 启动交易机器人...")
    print("📊 仪表板将在 http://localhost:8501 打开")
    print("⏹️  按 Ctrl+C 停止机器人")
    print("-" * 50)
    
    # 启动仪表板
    try:
        import subprocess
        subprocess.run([sys.executable, "run_dashboard.py"])
    except KeyboardInterrupt:
        print("\n⏹️  交易机器人已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
