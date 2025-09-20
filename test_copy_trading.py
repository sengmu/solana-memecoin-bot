#!/usr/bin/env python3
"""
跟单功能测试脚本
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from copy_trader import CopyTrader
from models import BotConfig

async def test_copy_trading():
    """测试跟单功能"""
    print("🤖 跟单功能测试")
    print("=" * 50)

    # 加载环境变量
    load_dotenv()

    # 检查配置
    required_vars = [
        'PRIVATE_KEY',
        'SOLANA_RPC_URL',
        'LEADER_WALLET_ADDRESS',
        'COPY_TRADING_ENABLED'
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var) == f'your_{var.lower()}_here':
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请先配置 .env 文件")
        return False

    try:
        # 创建配置
        config = BotConfig.from_env()

        # 创建跟单交易器
        trader = CopyTrader(
            config=config,
            private_key=os.getenv('PRIVATE_KEY'),
            rpc_url=os.getenv('SOLANA_RPC_URL')
        )

        print("✅ 跟单交易器初始化成功")
        print(f"📊 钱包地址: {trader.wallet_address}")
        print(f"🎯 跟单钱包: {trader.leader_wallets}")
        print(f"📈 跟单比例: {trader.copy_ratio}")
        print(f"🔍 最小置信度: {trader.min_confidence_score}%")

        # 测试跟单功能（不实际执行交易）
        print("\n🔍 测试跟单监控...")

        # 模拟检查跟单钱包
        if trader.leader_wallets:
            print(f"✅ 发现 {len(trader.leader_wallets)} 个跟单钱包")
            for i, wallet in enumerate(trader.leader_wallets, 1):
                print(f"  {i}. {wallet[:8]}...{wallet[-8:]}")
        else:
            print("⚠️ 未配置跟单钱包")

        print("\n🎉 跟单功能测试完成！")
        print("💡 提示：要启动实际跟单，请运行 python3 run_enhanced_bot.py")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("启动跟单功能测试...")

    # 检查依赖
    try:
        import aiohttp
        import solana
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return

    # 运行测试
    success = asyncio.run(test_copy_trading())

    if success:
        print("\n🚀 跟单功能已准备就绪！")
        print("📖 查看详细使用指南: COPY_TRADING_GUIDE.md")
    else:
        print("\n❌ 跟单功能配置有问题，请检查配置")

if __name__ == "__main__":
    main()
