# Solana Memecoin Trading Bot Dashboard

这是一个用于 Solana memecoin 交易的智能机器人仪表板，部署在 Streamlit Community Cloud 上。

## 功能特性

- 🔍 **代币发现**: 自动发现和筛选热门 memecoin
- 📈 **交易历史**: 查看所有交易记录和统计信息
- 💼 **持仓管理**: 监控当前持仓和盈亏情况
- 🛡️ **安全分析**: RugCheck 安全评分分析
- 🤖 **机器人控制**: 启动/停止发现和交易功能

## 部署说明

此应用已配置为在 Streamlit Community Cloud 上运行，使用 `dashboard_cloud.py` 作为主入口点。

### 环境变量

在 Streamlit Community Cloud 中，您需要设置以下环境变量：

```
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WS_URL=wss://api.mainnet-beta.solana.com
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
```

### 本地运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行云版本（演示模式）
streamlit run dashboard_cloud.py

# 运行完整版本（需要私钥）
streamlit run dashboard.py
```

## 注意事项

- 云部署版本使用模拟数据进行演示
- 实际交易功能需要配置私钥和 API 密钥
- 建议在本地环境进行完整功能测试

## 技术栈

- **前端**: Streamlit
- **数据处理**: Pandas, Plotly
- **区块链**: Solana Python SDK
- **数据源**: DexScreener, Twitter API, RugCheck
