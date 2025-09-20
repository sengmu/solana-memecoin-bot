# Solana Memecoin Trading Bot Makefile
# 参考 OpenSolBot 的 Makefile 结构

.PHONY: help install dev test clean up down logs status restart

# 默认目标
help:
	@echo "Solana Memecoin Trading Bot - 可用命令:"
	@echo ""
	@echo "开发环境:"
	@echo "  install     - 安装依赖"
	@echo "  dev         - 启动开发环境"
	@echo "  test        - 运行测试"
	@echo "  clean       - 清理临时文件"
	@echo ""
	@echo "Docker 部署:"
	@echo "  up          - 启动所有服务"
	@echo "  down        - 停止所有服务"
	@echo "  restart     - 重启所有服务"
	@echo "  logs        - 查看日志"
	@echo "  status      - 查看服务状态"
	@echo ""
	@echo "配置管理:"
	@echo "  config      - 编辑配置文件"
	@echo "  check       - 检查配置"
	@echo "  init        - 初始化配置"

# 安装依赖
install:
	@echo "📦 安装 Python 依赖..."
	pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

# 开发环境
dev:
	@echo "🚀 启动开发环境..."
	python3 run_visual_dashboard.py

# 运行测试
test:
	@echo "🧪 运行测试..."
	python3 -m pytest tests/ -v

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/

# Docker 命令
up:
	@echo "🐳 启动 Docker 服务..."
	docker-compose up -d
	@echo "✅ 服务已启动"
	@echo "📊 仪表板: http://localhost:8501"
	@echo "⚙️  配置界面: http://localhost:8502"

down:
	@echo "🛑 停止 Docker 服务..."
	docker-compose down
	@echo "✅ 服务已停止"

restart:
	@echo "🔄 重启 Docker 服务..."
	docker-compose restart
	@echo "✅ 服务已重启"

logs:
	@echo "📋 查看服务日志..."
	docker-compose logs -f

status:
	@echo "📊 服务状态:"
	docker-compose ps

# 配置管理
config:
	@echo "⚙️  编辑配置文件..."
	@if [ -f config.toml ]; then \
		nano config.toml; \
	else \
		cp example.config.toml config.toml; \
		nano config.toml; \
	fi

check:
	@echo "🔍 检查配置..."
	python3 check_config.py

init:
	@echo "🚀 初始化配置..."
	@if [ ! -f config.toml ]; then \
		cp example.config.toml config.toml; \
		echo "✅ 配置文件已创建: config.toml"; \
	fi
	@if [ ! -f .env ]; then \
		cp env.example .env; \
		echo "✅ 环境变量文件已创建: .env"; \
	fi
	@echo "📝 请编辑 config.toml 和 .env 文件配置您的参数"

# 部署管理
deploy:
	@echo "🚀 部署到 Streamlit Community Cloud..."
	./deploy.sh

push:
	@echo "📤 推送代码到 GitHub..."
	git add .
	git commit -m "Auto-commit: $(date '+%Y-%m-%d %H:%M:%S')"
	git push origin main

git-status:
	@echo "📊 Git 状态:"
	git status

# 数据库管理
db-init:
	@echo "🗄️  初始化数据库..."
	docker-compose exec mysql mysql -u root -proot -e "CREATE DATABASE IF NOT EXISTS solana_trade_bot;"

db-reset:
	@echo "🔄 重置数据库..."
	docker-compose down -v
	docker-compose up -d mysql
	sleep 10
	docker-compose up -d

# 监控命令
monitor:
	@echo "📊 启动监控面板..."
	python3 run_visual_dashboard.py

config-ui:
	@echo "⚙️  启动配置界面..."
	python3 run_config_ui.py

# 跟单测试
test-copy:
	@echo "🤖 测试跟单功能..."
	python3 test_copy_trading.py

# 启动增强版机器人
start-enhanced:
	@echo "🚀 启动增强版机器人..."
	python3 run_enhanced_bot_v2.py

# 更新依赖
update:
	@echo "🔄 更新依赖..."
	pip install --upgrade -r requirements.txt

# 构建 Docker 镜像
build:
	@echo "🔨 构建 Docker 镜像..."
	docker-compose build

# 推送镜像
push:
	@echo "📤 推送 Docker 镜像..."
	docker-compose push

# 备份数据
backup:
	@echo "💾 备份数据..."
	docker-compose exec mysql mysqldump -u root -proot solana_trade_bot > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ 数据备份完成"

# 恢复数据
restore:
	@echo "📥 恢复数据..."
	@read -p "请输入备份文件名: " backup_file; \
	docker-compose exec -T mysql mysql -u root -proot solana_trade_bot < $$backup_file
	@echo "✅ 数据恢复完成"
