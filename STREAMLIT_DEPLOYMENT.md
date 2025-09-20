# 🚀 Streamlit Community Cloud 部署指南

## 📋 部署步骤

### 1. 准备 GitHub 仓库
确保您的代码已经推送到 GitHub 仓库：
```bash
git add .
git commit -m "Prepare for Streamlit deployment"
git push origin main
```

### 2. 访问 Streamlit Community Cloud
1. 访问 [Streamlit Community Cloud](https://share.streamlit.io/)
2. 使用 GitHub 账号登录
3. 点击 "New app" 创建新应用

### 3. 配置应用
- **Repository**: `sengmu/solana-memecoin-bot`
- **Branch**: `main`
- **Main file path**: `streamlit_app.py`

### 4. 环境变量配置
在 Streamlit Community Cloud 中设置以下环境变量：

#### 必需配置
```
PRIVATE_KEY=your_wallet_private_key_here
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WS_URL=wss://api.mainnet-beta.solana.com
```

#### 可选配置
```
# API 配置
HELIUS_API_KEY=your_helius_api_key_here
SHYFT_API_KEY=your_shyft_api_key_here
JUPITER_API_KEY=your_jupiter_api_key_here
RAYDIUM_API_KEY=your_raydium_api_key_here

# Telegram 配置
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# 跟单配置
COPY_TRADING_ENABLED=true
LEADER_WALLET_ADDRESS=your_leader_wallet_address_here
COPY_RATIO=1.0
MIN_CONFIDENCE_SCORE=70

# 交易配置
MAX_POSITION_SIZE=0.1
MIN_VOLUME_24H=1000000
MIN_FDV=100000
MAX_SLIPPAGE=0.05
DEFAULT_SLIPPAGE=0.01

# 日志配置
LOG_LEVEL=INFO
LOG_TO_FILE=true
```

### 5. 部署应用
点击 "Deploy!" 按钮开始部署

## 🔧 故障排除

### 问题 1: 代码未连接到 GitHub 仓库
**解决方案:**
```bash
# 检查远程仓库
git remote -v

# 如果没有远程仓库，添加一个
git remote add origin https://github.com/yourusername/your-repo.git

# 推送代码
git push -u origin main
```

### 问题 2: 部署失败
**可能原因:**
- 依赖包安装失败
- 环境变量配置错误
- 代码语法错误

**解决方案:**
1. 检查 `requirements.txt` 文件
2. 验证环境变量配置
3. 查看部署日志

### 问题 3: 应用无法访问
**解决方案:**
1. 检查应用是否成功部署
2. 验证 URL 是否正确
3. 检查应用日志

## 📊 部署后的功能

### 主仪表板功能
- 🔍 代币发现和筛选
- 📈 实时价格图表
- 💼 持仓管理
- 🤖 跟单监控
- 📊 交易历史

### 配置界面功能
- ⚙️ 参数配置
- 🔧 跟单设置
- 📊 状态监控
- 🛡️ 风险管理

## 🔄 更新部署

当您需要更新应用时：

1. **修改代码**
```bash
# 编辑代码
nano dashboard_visual.py

# 提交更改
git add .
git commit -m "Update dashboard features"
git push origin main
```

2. **自动部署**
Streamlit Community Cloud 会自动检测到代码更改并重新部署

3. **手动重新部署**
在 Streamlit Community Cloud 控制面板中点击 "Reboot app"

## 🎯 最佳实践

### 1. 环境变量管理
- 使用强密码和安全的 API 密钥
- 定期轮换敏感信息
- 不要在代码中硬编码敏感信息

### 2. 性能优化
- 使用缓存减少 API 调用
- 优化图片和资源加载
- 合理设置刷新间隔

### 3. 监控和维护
- 定期检查应用状态
- 监控错误日志
- 及时更新依赖包

## 📚 相关文档

- [Streamlit Community Cloud 文档](https://docs.streamlit.io/streamlit-community-cloud)
- [Streamlit 部署指南](https://docs.streamlit.io/deploy)
- [环境变量配置](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management)

---

**部署完成后，您就可以通过 Streamlit Community Cloud 访问您的 Solana 交易机器人了！** 🎉
