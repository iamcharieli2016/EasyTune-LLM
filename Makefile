# EasyTune-LLM Makefile
# 便捷的项目管理命令

.PHONY: help install dev start stop restart logs clean test format lint

# 默认目标
help:
	@echo "EasyTune-LLM 项目管理命令"
	@echo ""
	@echo "使用方法: make [命令]"
	@echo ""
	@echo "可用命令:"
	@echo "  install    - 安装所有依赖"
	@echo "  dev        - 启动开发环境"
	@echo "  start      - 启动生产环境 (Docker)"
	@echo "  stop       - 停止所有服务"
	@echo "  restart    - 重启所有服务"
	@echo "  logs       - 查看服务日志"
	@echo "  clean      - 清理临时文件和缓存"
	@echo "  test       - 运行测试"
	@echo "  format     - 格式化代码"
	@echo "  lint       - 代码检查"
	@echo "  init-db    - 初始化数据库"
	@echo "  backup     - 备份数据库"

# 安装依赖
install:
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装训练引擎依赖..."
	cd training-engine && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install
	@echo "依赖安装完成!"

# 开发环境
dev:
	@echo "启动开发环境..."
	@echo "请在不同终端运行以下命令:"
	@echo "1. 后端: cd backend/api-gateway && uvicorn main:app --reload"
	@echo "2. 前端: cd frontend && npm start"
	@echo "3. Redis: redis-server"

# 启动生产环境
start:
	@echo "启动Docker服务..."
	chmod +x deployment/scripts/start.sh
	./deployment/scripts/start.sh

# 停止服务
stop:
	@echo "停止所有服务..."
	docker-compose down

# 重启服务
restart:
	@echo "重启服务..."
	docker-compose restart

# 查看日志
logs:
	@echo "查看服务日志 (Ctrl+C退出)..."
	docker-compose logs -f

# 清理
clean:
	@echo "清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@echo "清理完成!"

# 运行测试
test:
	@echo "运行后端测试..."
	cd backend && pytest
	@echo "运行前端测试..."
	cd frontend && npm test

# 格式化代码
format:
	@echo "格式化Python代码..."
	black backend/ training-engine/
	@echo "格式化前端代码..."
	cd frontend && npm run format

# 代码检查
lint:
	@echo "检查Python代码..."
	cd backend && flake8 .
	@echo "检查前端代码..."
	cd frontend && npm run lint

# 初始化数据库
init-db:
	@echo "初始化数据库..."
	docker-compose exec api-gateway python deployment/scripts/init_db.py

# 备份数据库
backup:
	@echo "备份数据库..."
	mkdir -p backups
	docker-compose exec postgres pg_dump -U easytune easytune_db > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "备份完成: backups/backup_*.sql"

# 构建Docker镜像
build:
	@echo "构建Docker镜像..."
	docker-compose build

# 查看服务状态
status:
	@echo "服务状态:"
	docker-compose ps

# 进入容器
shell-backend:
	docker-compose exec api-gateway /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

shell-db:
	docker-compose exec postgres psql -U easytune easytune_db

