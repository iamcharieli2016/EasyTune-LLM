#!/bin/bash

# EasyTune-LLM 本地启动脚本
# 支持 MacOS 和 Linux

set -e

echo "=========================================="
echo "🚀 EasyTune-LLM 启动脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取项目根目录
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

# 环境变量
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 检测操作系统
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
    echo -e "${GREEN}✓${NC} 检测到 MacOS 系统"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
    echo -e "${GREEN}✓${NC} 检测到 Linux 系统"
else
    echo -e "${RED}✗${NC} 不支持的操作系统: $OSTYPE"
    exit 1
fi

# 检测 Apple Silicon
if [[ "$OS_TYPE" == "macos" ]] && [[ $(uname -m) == "arm64" ]]; then
    echo -e "${GREEN}✓${NC} 检测到 Apple Silicon (M1/M2/M3)"
fi

echo ""

# 步骤 1: 检查数据库
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 步骤 1/5: 检查数据库服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v psql &> /dev/null; then
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        echo -e "${GREEN}✓${NC} PostgreSQL 正在运行"
    else
        echo -e "${YELLOW}⚠${NC} PostgreSQL 未运行，尝试启动..."
        if [[ "$OS_TYPE" == "macos" ]]; then
            brew services start postgresql@14 || brew services start postgresql
        else
            sudo systemctl start postgresql
        fi
        sleep 2
        if pg_isready -h localhost -p 5432 &> /dev/null; then
            echo -e "${GREEN}✓${NC} PostgreSQL 已启动"
        else
            echo -e "${RED}✗${NC} PostgreSQL 启动失败，请手动启动"
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠${NC} 未检测到 PostgreSQL，使用 Docker 容器？"
    if command -v docker &> /dev/null; then
        if docker ps --format '{{.Names}}' | grep -q "easytune-postgres"; then
            echo -e "${GREEN}✓${NC} Docker PostgreSQL 容器正在运行"
        else
            echo -e "${YELLOW}⚠${NC} 启动 Docker PostgreSQL 容器..."
            docker start easytune-postgres 2>/dev/null || echo -e "${RED}✗${NC} 请先配置 Docker 容器"
        fi
    fi
fi

echo ""

# 步骤 2: 激活 Python 环境
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 步骤 2/5: 激活 Python 环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v conda &> /dev/null; then
    # 使用 Conda
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null
    if conda env list | grep -q "easytune"; then
        conda activate easytune
        echo -e "${GREEN}✓${NC} Conda 环境 'easytune' 已激活"
    else
        echo -e "${RED}✗${NC} Conda 环境 'easytune' 不存在"
        echo "   请运行: conda create -n easytune python=3.10"
        exit 1
    fi
elif [[ -d "$PROJECT_ROOT/venv" ]]; then
    # 使用 venv
    source "$PROJECT_ROOT/venv/bin/activate"
    echo -e "${GREEN}✓${NC} Python venv 已激活"
else
    echo -e "${RED}✗${NC} 未找到 Python 虚拟环境"
    echo "   请先创建环境: python3 -m venv venv"
    exit 1
fi

python_version=$(python --version)
echo "   Python 版本: $python_version"
echo ""

# 步骤 3: 检查端口占用
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 步骤 3/5: 检查端口占用"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查后端端口 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠${NC} 端口 8000 已被占用"
    read -p "是否停止占用进程？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✓${NC} 已停止端口 8000 的进程"
    fi
else
    echo -e "${GREEN}✓${NC} 端口 8000 可用"
fi

# 检查前端端口 5173
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠${NC} 端口 5173 已被占用"
    read -p "是否停止占用进程？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        lsof -ti:5173 | xargs kill -9 2>/dev/null || true
        echo -e "${GREEN}✓${NC} 已停止端口 5173 的进程"
    fi
else
    echo -e "${GREEN}✓${NC} 端口 5173 可用"
fi

echo ""

# 步骤 4: 启动后端
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 步骤 4/5: 启动后端服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_ROOT/backend/api-gateway"

echo "启动后端..."
# 使用 nohup 在后台启动
nohup uvicorn main:app --reload --port 8000 > "$PROJECT_ROOT/logs/backend.log" 2>&1 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓${NC} 后端已启动 (PID: $BACKEND_PID)"
    echo "   访问: http://localhost:8000"
    echo "   API文档: http://localhost:8000/docs"
else
    echo -e "${RED}✗${NC} 后端启动失败"
    echo "   请查看日志: tail -f $PROJECT_ROOT/logs/backend.log"
    exit 1
fi

cd "$PROJECT_ROOT"
echo ""

# 步骤 5: 启动前端
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 步骤 5/5: 启动前端服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$PROJECT_ROOT/frontend"

# 检查 node_modules
if [[ ! -d "node_modules" ]]; then
    echo -e "${YELLOW}⚠${NC} 未找到 node_modules，正在安装依赖..."
    npm install
fi

echo "启动前端..."
# 使用 nohup 在后台启动
nohup npm run dev > "$PROJECT_ROOT/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

# 等待前端启动
sleep 5

if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓${NC} 前端已启动 (PID: $FRONTEND_PID)"
    echo "   访问: http://localhost:5173"
else
    echo -e "${RED}✗${NC} 前端启动失败"
    echo "   请查看日志: tail -f $PROJECT_ROOT/logs/frontend.log"
    exit 1
fi

cd "$PROJECT_ROOT"
echo ""

# 完成
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 所有服务已启动！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 访问地址："
echo "   前端: http://localhost:5173"
echo "   后端: http://localhost:8000"
echo "   API文档: http://localhost:8000/docs"
echo ""
echo "📋 后台进程："
echo "   后端 PID: $BACKEND_PID"
echo "   前端 PID: $FRONTEND_PID"
echo ""
echo "🛑 停止服务："
echo "   运行: ./stop.sh"
echo "   或手动: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📊 查看日志："
echo "   后端: tail -f logs/backend.log"
echo "   前端: tail -f logs/frontend.log"
echo ""

# 保存 PID
echo "$BACKEND_PID" > "$PROJECT_ROOT/.backend.pid"
echo "$FRONTEND_PID" > "$PROJECT_ROOT/.frontend.pid"

# 如果是 MacOS，自动打开浏览器
if [[ "$OS_TYPE" == "macos" ]]; then
    sleep 2
    echo "🌐 正在打开浏览器..."
    open http://localhost:5173
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

