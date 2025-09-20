# 🚀 快速部署指南

## 立即部署到 Streamlit Community Cloud

### 步骤 1: 创建 GitHub 仓库

1. 访问 [GitHub](https://github.com) 并登录
2. 点击 "New repository"
3. 仓库名称: `solana-memecoin-bot`
4. 设置为 Public（Streamlit Community Cloud 需要）
5. 点击 "Create repository"

### 步骤 2: 推送代码到 GitHub

在终端中运行以下命令（替换为您的 GitHub 用户名）：

```bash
# 添加远程仓库
git remote add origin https://github.com/YOUR_USERNAME/solana-memecoin-bot.git

# 推送到 GitHub
git push -u origin main
```

### 步骤 3: 部署到 Streamlit Community Cloud

1. 访问 [Streamlit Community Cloud](https://share.streamlit.io/)
2. 点击 "New app"
3. 选择您的 GitHub 仓库: `YOUR_USERNAME/solana-memecoin-bot`
4. 设置配置：
   - **Main file path**: `dashboard_cloud.py`
   - **Branch**: `main`
5. 点击 "Deploy!"

### 步骤 4: 配置环境变量

部署完成后，在 Streamlit Community Cloud 的 Secrets 管理中添加：

```toml
[secrets]
PRIVATE_KEY = "your_actual_private_key_here"
SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"
```

## 🎯 部署选项

### 选项 1: 简化版本（推荐）
- 使用 `dashboard_cloud.py` 作为主文件
- 包含演示数据，无需复杂配置
- 适合快速展示和测试

### 选项 2: 完整版本
- 使用 `dashboard.py` 作为主文件
- 需要完整的 Solana 配置
- 适合生产环境使用

## 🔧 故障排除

### 常见问题

1. **部署失败**
   - 检查 `requirements.txt` 是否包含所有依赖
   - 确保主文件路径正确

2. **导入错误**
   - 使用 `dashboard_cloud.py` 避免复杂依赖
   - 检查所有 Python 文件语法

3. **环境变量问题**
   - 在 Secrets 管理中添加必需的环境变量
   - 确保变量名称正确

### 获取帮助

- 查看 [DEPLOYMENT.md](DEPLOYMENT.md) 获取详细说明
- 检查 [Streamlit 文档](https://docs.streamlit.io/streamlit-community-cloud)

## ✅ 部署检查清单

- [ ] GitHub 仓库已创建
- [ ] 代码已推送到 GitHub
- [ ] Streamlit Community Cloud 应用已创建
- [ ] 主文件路径设置为 `dashboard_cloud.py`
- [ ] 环境变量已配置（如需要）
- [ ] 应用成功部署并运行

## 🎉 完成！

部署成功后，您将获得一个公开的 Streamlit 应用 URL，可以在任何地方访问您的 Memecoin 交易机器人仪表板！
