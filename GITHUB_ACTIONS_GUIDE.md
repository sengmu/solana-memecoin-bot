# 🚀 GitHub Actions 自动化指南

## 📋 概述

本项目已配置完整的 GitHub Actions 自动化工作流，实现：
- 🚀 自动部署到 Streamlit Community Cloud
- 🔍 代码质量检查
- 🧪 自动化测试
- 📦 依赖更新管理

## 🔧 工作流说明

### 1. 部署工作流 (`deploy.yml`)
**触发条件:**
- 推送到 `main` 分支
- 创建 Pull Request 到 `main` 分支
- 手动触发

**功能:**
- 运行测试套件
- 验证配置
- 检查 Streamlit 应用
- 自动部署到 Streamlit Community Cloud

### 2. 代码质量工作流 (`quality.yml`)
**触发条件:**
- 推送到 `main` 或 `develop` 分支
- 创建 Pull Request
- 每周一自动运行

**功能:**
- 代码格式化检查 (black)
- 导入排序检查 (isort)
- 代码规范检查 (flake8)
- 类型检查 (mypy)
- 安全扫描 (bandit)

### 3. 测试工作流 (`test.yml`)
**触发条件:**
- 推送到 `main` 或 `develop` 分支
- 创建 Pull Request
- 每天凌晨 2 点自动运行

**功能:**
- 多 Python 版本测试 (3.9, 3.10, 3.11)
- 单元测试
- 集成测试
- 覆盖率报告

### 4. 依赖更新工作流 (`dependencies.yml`)
**触发条件:**
- 每周日自动运行
- 手动触发

**功能:**
- 检查依赖更新
- 自动创建 Pull Request
- 测试更新后的兼容性

## 🚀 使用方法

### 自动部署
```bash
# 推送代码到 main 分支
git add .
git commit -m "Update features"
git push origin main

# GitHub Actions 会自动：
# 1. 运行测试
# 2. 检查代码质量
# 3. 部署到 Streamlit Community Cloud
```

### 手动触发
```bash
# 查看 Actions 状态
make actions-status

# 手动触发部署
make trigger-deploy

# 手动触发代码质量检查
make trigger-quality

# 手动触发测试
make trigger-test

# 手动触发依赖更新
make trigger-deps
```

### 使用 GitHub CLI
```bash
# 安装 GitHub CLI
brew install gh

# 登录 GitHub
gh auth login

# 查看工作流状态
gh run list

# 手动触发工作流
gh workflow run deploy.yml
gh workflow run quality.yml
gh workflow run test.yml
gh workflow run dependencies.yml
```

## 📊 监控和状态

### 状态徽章
在 README.md 中添加状态徽章：

```markdown
[![Deploy to Streamlit](https://github.com/sengmu/solana-memecoin-bot/actions/workflows/deploy.yml/badge.svg)](https://github.com/sengmu/solana-memecoin-bot/actions/workflows/deploy.yml)
[![Code Quality](https://github.com/sengmu/solana-memecoin-bot/actions/workflows/quality.yml/badge.svg)](https://github.com/sengmu/solana-memecoin-bot/actions/workflows/quality.yml)
[![Tests](https://github.com/sengmu/solana-memecoin-bot/actions/workflows/test.yml/badge.svg)](https://github.com/sengmu/solana-memecoin-bot/actions/workflows/test.yml)
[![Dependencies](https://github.com/sengmu/solana-memecoin-bot/actions/workflows/dependencies.yml/badge.svg)](https://github.com/sengmu/solana-memecoin-bot/actions/workflows/dependencies.yml)
```

### 查看详细状态
- 访问 GitHub Actions 页面：https://github.com/sengmu/solana-memecoin-bot/actions
- 查看具体工作流运行日志
- 监控部署状态和错误信息

## 🔧 配置说明

### 环境变量
在 GitHub 仓库设置中添加以下 Secrets：

```
STREAMLIT_CLOUD_TOKEN=your_streamlit_cloud_token
CODECOV_TOKEN=your_codecov_token
```

### 工作流权限
确保工作流有足够的权限：
- `actions: write` - 运行工作流
- `contents: read` - 读取代码
- `pull-requests: write` - 创建 PR

## 🚨 故障排除

### 常见问题

1. **部署失败**
   - 检查 Streamlit 应用语法
   - 验证环境变量配置
   - 查看部署日志

2. **测试失败**
   - 检查测试文件语法
   - 验证依赖安装
   - 查看测试输出

3. **代码质量检查失败**
   - 运行 `black` 格式化代码
   - 运行 `isort` 排序导入
   - 修复 flake8 警告

### 调试命令
```bash
# 本地运行测试
python -m pytest tests/ -v

# 本地代码质量检查
flake8 .
black --check .
isort --check-only .

# 本地类型检查
mypy .
```

## 📈 最佳实践

### 1. 提交规范
```bash
# 使用规范的提交信息
git commit -m "feat: add new trading feature"
git commit -m "fix: resolve configuration issue"
git commit -m "docs: update deployment guide"
```

### 2. 分支管理
```bash
# 创建功能分支
git checkout -b feature/new-feature

# 开发完成后创建 PR
gh pr create --title "Add new feature" --body "Description"

# 合并到 main 分支后自动部署
```

### 3. 监控和维护
- 定期检查 Actions 状态
- 及时修复失败的测试
- 保持依赖更新

## 🎯 自动化流程

### 完整开发流程
1. **开发功能** → 在功能分支开发
2. **创建 PR** → 自动运行测试和质量检查
3. **代码审查** → 通过后合并到 main
4. **自动部署** → 自动部署到 Streamlit Community Cloud
5. **监控状态** → 通过徽章和日志监控

### 日常维护
- 每周自动检查依赖更新
- 每天自动运行测试
- 实时监控部署状态

---

**现在您拥有了完全自动化的 CI/CD 流程！** 🎉
