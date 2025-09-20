#!/bin/bash
# Streamlit Community Cloud 自动部署脚本

echo "🚀 开始部署到 Streamlit Community Cloud..."

# 检查 Git 状态
echo "📋 检查 Git 状态..."
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  发现未提交的更改，正在提交..."
    git add .
    git commit -m "Auto-deploy: $(date '+%Y-%m-%d %H:%M:%S')"
fi

# 推送到远程仓库
echo "📤 推送到远程仓库..."
git push origin main

# 检查推送结果
if [ $? -eq 0 ]; then
    echo "✅ 代码推送成功！"
    echo ""
    echo "📊 部署信息:"
    echo "  - 仓库: $(git remote get-url origin)"
    echo "  - 分支: main"
    echo "  - 入口文件: streamlit_app.py"
    echo ""
    echo "🌐 请在 Streamlit Community Cloud 中:"
    echo "  1. 访问 https://share.streamlit.io/"
    echo "  2. 选择仓库: $(git remote get-url origin | sed 's/.*\///' | sed 's/\.git$//')"
    echo "  3. 设置入口文件: streamlit_app.py"
    echo "  4. 配置环境变量"
    echo "  5. 点击 Deploy!"
    echo ""
    echo "📖 详细说明请查看: STREAMLIT_DEPLOYMENT.md"
else
    echo "❌ 代码推送失败，请检查网络连接和权限"
    exit 1
fi
