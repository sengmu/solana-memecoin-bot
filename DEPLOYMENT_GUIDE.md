# Streamlit Community Cloud 部署指南

## 🚀 快速部署步骤

### 1. 访问 Streamlit Community Cloud
1. 打开 [share.streamlit.io](https://share.streamlit.io)
2. 使用 GitHub 账户登录
3. 点击 "New app" 创建新应用

### 2. 配置应用
- **Repository**: `sengmu/solana-memecoin-bot`
- **Branch**: `main`
- **Main file path**: `streamlit_app.py`

### 3. 设置环境变量（可选）
在应用设置中添加以下环境变量：

```
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WS_URL=wss://api.mainnet-beta.solana.com
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
```

### 4. 部署
点击 "Deploy!" 开始部署过程。

## 📋 部署检查清单

- [x] ✅ 代码已推送到 GitHub 仓库
- [x] ✅ 创建了 `streamlit_app.py` 入口文件
- [x] ✅ 配置了 `.streamlit/config.toml`
- [x] ✅ 使用 `dashboard_cloud.py` 作为云部署版本
- [x] ✅ 包含演示数据，无需私钥即可运行

## 🔧 技术配置

### 文件结构
```
solana-memecoin-bot/
├── streamlit_app.py          # 云部署入口点
├── dashboard_cloud.py        # 云版本仪表板（演示数据）
├── dashboard.py              # 完整版本（需要私钥）
├── .streamlit/
│   └── config.toml          # Streamlit 配置
├── requirements.txt          # Python 依赖
└── README_STREAMLIT.md      # 部署说明
```

### 依赖管理
所有必要的依赖已在 `requirements.txt` 中定义，Streamlit Community Cloud 会自动安装。

## 🌐 访问应用

部署成功后，您将获得一个类似这样的 URL：
```
https://your-app-name.streamlit.app/
```

## 🔒 安全注意事项

- 云部署版本使用模拟数据，不会进行实际交易
- 不要在生产环境中暴露私钥
- 建议在本地环境测试完整功能后再部署

## 🐛 故障排除

### 常见问题

1. **导入错误**: 确保所有依赖都在 `requirements.txt` 中
2. **环境变量**: 检查是否正确设置了必要的环境变量
3. **文件路径**: 确保 `streamlit_app.py` 路径正确

### 日志查看
在 Streamlit Community Cloud 控制台中查看部署日志以诊断问题。

## 📞 支持

如有问题，请检查：
1. GitHub 仓库: https://github.com/sengmu/solana-memecoin-bot
2. Streamlit 文档: https://docs.streamlit.io/
3. 部署日志和错误信息
