#!/bin/bash

# EasyTune-LLM 本地环境安装脚本
# 支持 MacOS 和 Linux

set -e

echo "=========================================="
echo "📦 EasyTune-LLM 安装脚本"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 获取项目根目录
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

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

echo ""

# 步骤 1: 检查系统依赖
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 步骤 1/7: 检查系统依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查 Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Python: $PYTHON_VERSION"
else
    echo -e "${RED}✗${NC} 未安装 Python 3"
    exit 1
fi

# 检查 Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js: $NODE_VERSION"
else
    echo -e "${RED}✗${NC} 未安装 Node.js"
    if [[ "$OS_TYPE" == "macos" ]]; then
        echo "   安装: brew install node"
    else
        echo "   安装: sudo apt install nodejs npm"
    fi
    exit 1
fi

# 检查 PostgreSQL
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version | awk '{print $3}')
    echo -e "${GREEN}✓${NC} PostgreSQL: $PSQL_VERSION"
else
    echo -e "${YELLOW}⚠${NC} 未安装 PostgreSQL"
    if [[ "$OS_TYPE" == "macos" ]]; then
        echo "   安装: brew install postgresql@14"
    else
        echo "   安装: sudo apt install postgresql"
    fi
fi

# 检查 Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    echo -e "${GREEN}✓${NC} Git: $GIT_VERSION"
else
    echo -e "${RED}✗${NC} 未安装 Git"
    exit 1
fi

echo ""

# 步骤 2: 创建 Python 虚拟环境
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 步骤 2/7: 创建 Python 虚拟环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v conda &> /dev/null; then
    echo "使用 Conda 创建环境..."
    source ~/miniconda3/etc/profile.d/conda.sh 2>/dev/null || source ~/anaconda3/etc/profile.d/conda.sh 2>/dev/null
    
    if conda env list | grep -q "easytune"; then
        echo -e "${YELLOW}⚠${NC} 环境 'easytune' 已存在，跳过创建"
    else
        conda create -n easytune python=3.10 -y
        echo -e "${GREEN}✓${NC} Conda 环境已创建"
    fi
    
    conda activate easytune
else
    echo "使用 venv 创建环境..."
    if [[ -d "venv" ]]; then
        echo -e "${YELLOW}⚠${NC} venv 已存在，跳过创建"
    else
        python3 -m venv venv
        echo -e "${GREEN}✓${NC} venv 环境已创建"
    fi
    
    source venv/bin/activate
fi

echo ""

# 步骤 3: 安装 Python 依赖
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 步骤 3/7: 安装 Python 依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "安装后端依赖..."
pip install -r backend/requirements.txt

echo "安装训练引擎依赖..."
pip install -r training-engine/requirements.txt

echo -e "${GREEN}✓${NC} Python 依赖已安装"
echo ""

# 步骤 4: 配置数据库
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️ 步骤 4/7: 配置数据库"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查数据库是否运行
if pg_isready -h localhost -p 5432 &> /dev/null; then
    echo -e "${GREEN}✓${NC} PostgreSQL 正在运行"
    
    # 创建数据库
    if psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw easytune_db; then
        echo -e "${YELLOW}⚠${NC} 数据库 'easytune_db' 已存在"
    else
        echo "创建数据库 'easytune_db'..."
        createdb -h localhost -U postgres easytune_db 2>/dev/null || \
        psql -h localhost -U postgres -c "CREATE DATABASE easytune_db;" 2>/dev/null
        echo -e "${GREEN}✓${NC} 数据库已创建"
    fi
else
    echo -e "${YELLOW}⚠${NC} PostgreSQL 未运行，请先启动 PostgreSQL"
    if [[ "$OS_TYPE" == "macos" ]]; then
        echo "   启动: brew services start postgresql@14"
    else
        echo "   启动: sudo systemctl start postgresql"
    fi
fi

echo ""

# 步骤 5: 配置环境变量
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚙️ 步骤 5/7: 配置环境变量"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ ! -f ".env" ]]; then
    echo "创建 .env 文件..."
    cat > .env << EOF
# 数据库配置
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/easytune_db

# JWT 配置
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 项目路径
PROJECT_ROOT=$PROJECT_ROOT

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=5173

# 文件上传
MAX_FILE_SIZE=524288000

# HuggingFace 配置
HF_ENDPOINT=https://hf-mirror.com
EOF
    echo -e "${GREEN}✓${NC} .env 文件已创建"
else
    echo -e "${YELLOW}⚠${NC} .env 文件已存在，跳过"
fi

echo ""

# 步骤 6: 运行数据库迁移
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 步骤 6/7: 运行数据库迁移"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if pg_isready -h localhost -p 5432 &> /dev/null; then
    cd backend
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    alembic upgrade head
    cd "$PROJECT_ROOT"
    echo -e "${GREEN}✓${NC} 数据库迁移完成"
else
    echo -e "${YELLOW}⚠${NC} 数据库未运行，跳过迁移"
fi

echo ""

# 步骤 7: 安装前端依赖
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 步骤 7/7: 安装前端依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd frontend

if [[ -d "node_modules" ]]; then
    echo -e "${YELLOW}⚠${NC} node_modules 已存在"
    read -p "是否重新安装？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf node_modules package-lock.json
        npm install
        echo -e "${GREEN}✓${NC} 前端依赖已安装"
    else
        echo "跳过安装"
    fi
else
    npm install
    echo -e "${GREEN}✓${NC} 前端依赖已安装"
fi

cd "$PROJECT_ROOT"
echo ""

# 创建必要的目录
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📁 创建项目目录"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p uploads
mkdir -p lora_adapters
mkdir -p logs/training
mkdir -p cache

echo -e "${GREEN}✓${NC} 目录已创建"
echo ""

# 完成
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 安装完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 下一步："
echo "   1. 确保 PostgreSQL 正在运行"
echo "   2. 运行启动脚本: ./start.sh"
echo "   3. 访问 http://localhost:5173"
echo ""
echo "📚 文档："
echo "   查看 INSTALLATION.md 了解更多详情"
echo ""

