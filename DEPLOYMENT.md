# Streamlit Community Cloud 部署指南

## 部署步骤

### 1. 创建 GitHub 仓库

1. 在 GitHub 上创建一个新的仓库
2. 将本地代码推送到 GitHub：

```bash
# 添加远程仓库（替换为您的仓库URL）
git remote add origin https://github.com/yourusername/solana-memecoin-bot.git

# 推送到 GitHub
git push -u origin main
```

### 2. 在 Streamlit Community Cloud 部署

1. 访问 [Streamlit Community Cloud](https://share.streamlit.io/)
2. 点击 "New app"
3. 选择您的 GitHub 仓库
4. 设置以下配置：
   - **Main file path**: `dashboard.py`
   - **Branch**: `main`

### 3. 配置环境变量

在 Streamlit Community Cloud 的 Secrets 管理中添加以下环境变量：

```toml
[secrets]
# 必需配置
PRIVATE_KEY = "your_actual_private_key"
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"

# 可选配置
TWITTER_API_KEY = "your_twitter_api_key"
LEADER_WALLET_ADDRESS = "your_leader_wallet_address"
```

### 4. 部署后配置

部署完成后，您需要：

1. **设置环境变量**：在 Streamlit Community Cloud 的 Secrets 管理中添加您的实际配置
2. **测试功能**：确保所有功能正常工作
3. **监控日志**：检查是否有任何错误

## 重要注意事项

### 安全配置
- ⚠️ **永远不要**将真实的私钥提交到 GitHub
- 使用 Streamlit Secrets 管理敏感信息
- 定期轮换 API 密钥

### 环境变量说明
- `PRIVATE_KEY`: 您的 Solana 钱包私钥（必需）
- `SOLANA_RPC_URL`: Solana RPC 端点（必需）
- `TWITTER_API_KEY`: Twitter API 密钥（可选，用于 Twitter 分析）
- `LEADER_WALLET_ADDRESS`: 跟单交易的目标钱包地址（可选）

### 故障排除

如果部署失败，请检查：

1. **依赖问题**：确保 `requirements.txt` 包含所有必需的包
2. **导入错误**：检查所有 Python 文件是否正确导入
3. **环境变量**：确保所有必需的环境变量都已设置
4. **文件路径**：确保所有文件路径正确

## 本地开发

要在本地运行：

```bash
# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp env.example .env
# 编辑 .env 文件添加您的配置

# 运行仪表板
streamlit run dashboard.py
```

## 支持

如果遇到问题，请检查：
- [Streamlit Community Cloud 文档](https://docs.streamlit.io/streamlit-community-cloud)
- [GitHub Issues](https://github.com/yourusername/solana-memecoin-bot/issues)
