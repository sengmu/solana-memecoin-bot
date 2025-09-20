# 🚀 实际交易配置指南

## ⚠️ 重要警告
- **风险提示**: 加密货币交易存在高风险，可能导致资金损失
- **测试建议**: 建议先在测试网或小额资金上测试
- **私钥安全**: 永远不要分享您的私钥给任何人

## 🔑 必需配置

### 1. Solana 钱包私钥
```bash
# 在 .env 文件中设置
PRIVATE_KEY=your_actual_private_key_here
```

**获取私钥方法：**
- **Phantom 钱包**: 设置 → 显示私钥
- **Solflare 钱包**: 设置 → 导出私钥
- **命令行**: `solana-keygen new` 生成新钱包

### 2. RPC 节点配置
```bash
# 免费公共节点（可能有限制）
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# 推荐使用付费节点（更稳定）
SOLANA_RPC_URL=https://solana-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```

**推荐 RPC 提供商：**
- [Alchemy](https://www.alchemy.com/solana) - 免费额度 + 付费选项
- [QuickNode](https://www.quicknode.com/solana) - 专业级服务
- [Helius](https://helius.xyz/) - 高性能节点

### 3. Twitter API 配置（可选）
```bash
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
```

**获取 Twitter Bearer Token：**
1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建应用
3. 获取 Bearer Token

## 💰 交易参数配置

### 风险控制设置
```bash
# 最大单笔交易金额（SOL）
MAX_POSITION_SIZE=0.01  # 建议从小额开始

# 最小24小时交易量（美元）
MIN_VOLUME_24H=1000000  # $1M

# 最小完全稀释估值（美元）
MIN_FDV=100000  # $100K

# 滑点控制
MAX_SLIPPAGE=0.05      # 最大5%滑点
DEFAULT_SLIPPAGE=0.01  # 默认1%滑点
```

### 止损止盈设置
```bash
# 最大日损失（总资金的百分比）
MAX_DAILY_LOSS=0.1     # 10%

# 止损百分比
STOP_LOSS_PERCENTAGE=0.2  # 20%

# 止盈百分比
TAKE_PROFIT_PERCENTAGE=0.5  # 50%
```

## 🔧 配置步骤

### 步骤 1: 编辑环境变量
```bash
nano .env
# 或使用任何文本编辑器
```

### 步骤 2: 设置您的私钥
```bash
# 替换为您的实际私钥
PRIVATE_KEY=your_actual_private_key_here
```

### 步骤 3: 配置 RPC 节点
```bash
# 使用付费节点（推荐）
SOLANA_RPC_URL=https://solana-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```

### 步骤 4: 调整交易参数
```bash
# 从小额开始测试
MAX_POSITION_SIZE=0.01
MIN_VOLUME_24H=500000
```

## 🧪 测试配置

### 1. 验证钱包连接
```bash
python3 -c "
from solana.rpc.api import Client
from solders.keypair import Keypair
import base58

# 测试私钥格式
try:
    private_key = 'YOUR_PRIVATE_KEY_HERE'
    keypair = Keypair.from_base58_string(private_key)
    print(f'✅ 钱包地址: {keypair.pubkey()}')
except Exception as e:
    print(f'❌ 私钥格式错误: {e}')
"
```

### 2. 测试 RPC 连接
```bash
python3 -c "
from solana.rpc.api import Client

# 测试 RPC 连接
try:
    client = Client('YOUR_RPC_URL_HERE')
    balance = client.get_balance(client.get_latest_blockhash().value.blockhash)
    print(f'✅ RPC 连接成功')
except Exception as e:
    print(f'❌ RPC 连接失败: {e}')
"
```

## 🚀 启动实际交易

### 1. 确保配置正确
```bash
# 检查环境变量
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

required_vars = ['PRIVATE_KEY', 'SOLANA_RPC_URL']
for var in required_vars:
    value = os.getenv(var)
    if value and value != f'your_{var.lower()}_here':
        print(f'✅ {var}: 已配置')
    else:
        print(f'❌ {var}: 未配置')
"
```

### 2. 启动交易机器人
```bash
# 使用实际交易模式
python3 run_dashboard.py
```

### 3. 在仪表板中
1. 点击 "🚀 开始发现"
2. 机器人将开始扫描代币
3. 满足条件的代币将自动交易

## 🛡️ 安全建议

### 私钥安全
- ✅ 使用硬件钱包（推荐）
- ✅ 私钥存储在安全位置
- ❌ 不要在代码中硬编码私钥
- ❌ 不要分享私钥给任何人

### 风险控制
- ✅ 从小额资金开始
- ✅ 设置合理的止损
- ✅ 定期检查交易记录
- ❌ 不要投入超过承受能力的资金

### 监控建议
- 📊 定期查看交易历史
- 📈 监控持仓表现
- 🚨 设置价格警报
- 📝 记录交易日志

## 🔍 故障排除

### 常见问题

1. **"PRIVATE_KEY environment variable is required"**
   - 检查 `.env` 文件是否存在
   - 确认私钥格式正确

2. **"RPC connection failed"**
   - 检查 RPC URL 是否正确
   - 尝试使用不同的 RPC 提供商

3. **"Insufficient funds"**
   - 检查钱包余额
   - 减少 `MAX_POSITION_SIZE`

4. **"Transaction failed"**
   - 检查滑点设置
   - 确认代币地址有效

## 📞 支持

如有问题，请检查：
1. 日志文件中的错误信息
2. 钱包余额是否充足
3. RPC 连接是否正常
4. 交易参数是否合理
