# 🤖 跟单交易功能使用指南

## 📋 功能概述

跟单交易功能允许您自动跟随其他成功交易者的操作，复制他们的买卖决策。这是一个强大的功能，特别适合初学者或想要跟随专业交易者的用户。

## 🚀 快速开始

### 1. 配置环境变量

首先，您需要在 `.env` 文件中配置跟单相关参数：

```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件
nano .env
```

### 2. 关键配置参数

```env
# 跟单交易配置
COPY_TRADING_ENABLED=true                    # 启用跟单功能
LEADER_WALLET_ADDRESS=leader_wallet_address  # 主要跟单钱包地址
LEADER_WALLETS=wallet1,wallet2,wallet3      # 多个跟单钱包（逗号分隔）
COPY_RATIO=1.0                              # 跟单比例（1.0 = 100%）
MIN_CONFIDENCE_SCORE=70                     # 最小置信度分数

# 基础配置
PRIVATE_KEY=your_wallet_private_key_here     # 您的钱包私钥
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
```

## 🎯 跟单模式详解

### 模式 1: 单钱包跟单
```env
LEADER_WALLET_ADDRESS=9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
COPY_TRADING_ENABLED=true
```

### 模式 2: 多钱包跟单
```env
LEADER_WALLETS=9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM,7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU,5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1
COPY_TRADING_ENABLED=true
```

### 模式 3: 智能跟单（推荐）
```env
COPY_TRADING_ENABLED=true
MIN_CONFIDENCE_SCORE=80
COPY_RATIO=0.5  # 只跟单50%的仓位
```

## ⚙️ 配置参数说明

| 参数 | 说明 | 推荐值 | 示例 |
|------|------|--------|------|
| `COPY_TRADING_ENABLED` | 是否启用跟单 | `true` | `true` |
| `LEADER_WALLET_ADDRESS` | 主要跟单钱包 | 成功交易者地址 | `9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM` |
| `LEADER_WALLETS` | 多个跟单钱包 | 逗号分隔的地址列表 | `wallet1,wallet2,wallet3` |
| `COPY_RATIO` | 跟单比例 | 0.1-2.0 | `1.0` (100%) |
| `MIN_CONFIDENCE_SCORE` | 最小置信度 | 50-90 | `70` |

## 🔍 如何找到优质跟单钱包

### 方法 1: 使用 DexScreener
1. 访问 [DexScreener](https://dexscreener.com/solana)
2. 查看热门代币的交易记录
3. 找到经常在低点买入、高点卖出的钱包
4. 复制钱包地址

### 方法 2: 使用 Solscan
1. 访问 [Solscan](https://solscan.io/)
2. 搜索代币地址
3. 查看大额交易记录
4. 分析交易者的历史表现

### 方法 3: 社区推荐
1. 加入 Solana 交易社区
2. 关注知名交易者的钱包
3. 验证其历史交易记录

## 🛠️ 启动跟单功能

### 方法 1: 使用可视化界面
```bash
# 启动可视化界面
python3 run_visual_dashboard.py

# 在浏览器中打开
# 主仪表板: http://localhost:8501
# 配置界面: http://localhost:8502
```

### 方法 2: 使用增强版机器人
```bash
# 安装依赖
pip install python-telegram-bot

# 启动增强版机器人
python3 run_enhanced_bot.py
```

### 方法 3: 直接启动跟单功能
```bash
# 启动跟单交易
python3 -c "
from copy_trader import CopyTrader
from models import BotConfig
import os
from dotenv import load_dotenv

load_dotenv()
config = BotConfig.from_env()
trader = CopyTrader(config, os.getenv('PRIVATE_KEY'), os.getenv('SOLANA_RPC_URL'))
asyncio.run(trader.start_copy_trading())
"
```

## 📊 跟单监控

### 实时监控
- 在配置界面查看跟单状态
- 监控交易执行情况
- 查看盈亏统计

### 日志监控
```bash
# 查看跟单日志
tail -f logs/copy_trading.log

# 查看所有日志
tail -f logs/bot.log
```

## ⚠️ 风险提示

### 1. 资金风险
- 只投入您能承受损失的资金
- 建议先用小金额测试
- 设置合理的止损点

### 2. 跟单风险
- 被跟单者可能亏损
- 网络延迟可能导致错过最佳时机
- 市场变化可能导致策略失效

### 3. 技术风险
- 确保私钥安全
- 定期备份配置
- 监控系统运行状态

## 🎛️ 高级配置

### 自定义跟单策略
```python
# 在 copy_trader.py 中自定义策略
class CustomCopyStrategy:
    def should_copy_trade(self, trade_info):
        # 自定义跟单条件
        if trade_info['amount'] > 1000:  # 只跟单大额交易
            return True
        return False
```

### 动态调整跟单比例
```python
# 根据市场情况调整跟单比例
def adjust_copy_ratio(market_volatility):
    if market_volatility > 0.8:
        return 0.5  # 高波动时减少跟单
    return 1.0  # 正常波动时100%跟单
```

## 🔧 故障排除

### 常见问题

1. **跟单不执行**
   - 检查钱包地址是否正确
   - 确认网络连接正常
   - 查看日志错误信息

2. **交易失败**
   - 检查账户余额
   - 确认滑点设置
   - 验证代币地址

3. **延迟过高**
   - 更换RPC节点
   - 检查网络连接
   - 优化配置参数

### 调试命令
```bash
# 检查配置
python3 check_config.py

# 测试跟单功能
python3 -c "
from copy_trader import CopyTrader
from models import BotConfig
import os
from dotenv import load_dotenv

load_dotenv()
config = BotConfig.from_env()
print('跟单配置:', {
    'enabled': config.copy_trading_enabled,
    'leader_wallets': config.leader_wallets,
    'copy_ratio': config.copy_ratio
})
"
```

## 📈 最佳实践

### 1. 选择策略
- 选择有长期盈利记录的交易者
- 避免跟随短期投机者
- 定期评估跟单效果

### 2. 风险管理
- 设置合理的仓位大小
- 使用止损和止盈
- 分散跟单多个交易者

### 3. 持续优化
- 定期分析跟单效果
- 调整跟单参数
- 学习交易策略

## 🆘 获取帮助

如果遇到问题，可以：
1. 查看日志文件
2. 检查配置参数
3. 参考故障排除部分
4. 在GitHub提交Issue

---

**记住：跟单交易有风险，投资需谨慎！** 🚨
