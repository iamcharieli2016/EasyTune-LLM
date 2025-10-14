#!/bin/bash

# EasyTune-LLM 服务状态检查脚本

echo "=========================================="
echo "🔍 EasyTune-LLM 服务状态检查"
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

# 检查数据库
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗄️ 数据库服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        echo -e "${GREEN}✓${NC} PostgreSQL 运行中"
        psql --version
    else
        echo -e "${RED}✗${NC} PostgreSQL 未运行"
    fi
else
    if command -v docker &> /dev/null; then
        if docker ps --format '{{.Names}}' | grep -q "easytune-postgres"; then
            echo -e "${GREEN}✓${NC} Docker PostgreSQL 运行中"
        else
            echo -e "${RED}✗${NC} Docker PostgreSQL 未运行"
        fi
    else
        echo -e "${YELLOW}⚠${NC} 未检测到 PostgreSQL 或 Docker"
    fi
fi

echo ""

# 检查后端
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 后端服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    BACKEND_PID=$(lsof -ti:8000)
    echo -e "${GREEN}✓${NC} 后端运行中 (PID: $BACKEND_PID)"
    echo "   端口: 8000"
    
    # 测试 API
    if curl -s http://localhost:8000/docs > /dev/null; then
        echo -e "${GREEN}✓${NC} API 可访问"
        echo "   URL: http://localhost:8000/docs"
    else
        echo -e "${YELLOW}⚠${NC} API 响应异常"
    fi
else
    echo -e "${RED}✗${NC} 后端未运行"
fi

echo ""

# 检查前端
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 前端服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    FRONTEND_PID=$(lsof -ti:5173)
    echo -e "${GREEN}✓${NC} 前端运行中 (PID: $FRONTEND_PID)"
    echo "   端口: 5173"
    echo "   URL: http://localhost:5173"
else
    echo -e "${RED}✗${NC} 前端未运行"
fi

echo ""

# 检查训练进程
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 训练进程"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TRAINING_PIDS=$(ps aux | grep "trainer.py" | grep -v grep | awk '{print $2}')
if [[ -n "$TRAINING_PIDS" ]]; then
    TRAINING_COUNT=$(echo "$TRAINING_PIDS" | wc -l)
    echo -e "${GREEN}✓${NC} 发现 $TRAINING_COUNT 个训练进程"
    echo "$TRAINING_PIDS" | while read pid; do
        echo "   PID: $pid"
    done
else
    echo -e "${BLUE}ℹ${NC} 无训练进程运行"
fi

echo ""

# 检查磁盘空间
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💾 磁盘空间"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DISK_USAGE=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $5}' | sed 's/%//')
DISK_AVAIL=$(df -h "$PROJECT_ROOT" | tail -1 | awk '{print $4}')

if [[ $DISK_USAGE -lt 80 ]]; then
    echo -e "${GREEN}✓${NC} 磁盘空间充足"
else
    echo -e "${YELLOW}⚠${NC} 磁盘空间不足"
fi
echo "   使用率: $DISK_USAGE%"
echo "   可用: $DISK_AVAIL"

# 检查目录大小
echo ""
echo "📁 数据目录："
if [[ -d "$PROJECT_ROOT/uploads" ]]; then
    UPLOADS_SIZE=$(du -sh "$PROJECT_ROOT/uploads" 2>/dev/null | cut -f1)
    echo "   uploads: $UPLOADS_SIZE"
fi
if [[ -d "$PROJECT_ROOT/lora_adapters" ]]; then
    LORA_SIZE=$(du -sh "$PROJECT_ROOT/lora_adapters" 2>/dev/null | cut -f1)
    echo "   lora_adapters: $LORA_SIZE"
fi
if [[ -d "$PROJECT_ROOT/logs" ]]; then
    LOGS_SIZE=$(du -sh "$PROJECT_ROOT/logs" 2>/dev/null | cut -f1)
    echo "   logs: $LOGS_SIZE"
fi

echo ""

# 检查 Python 环境
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🐍 Python 环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command -v conda &> /dev/null; then
    if conda env list | grep -q "easytune"; then
        echo -e "${GREEN}✓${NC} Conda 环境 'easytune' 存在"
    else
        echo -e "${RED}✗${NC} Conda 环境 'easytune' 不存在"
    fi
elif [[ -d "$PROJECT_ROOT/venv" ]]; then
    echo -e "${GREEN}✓${NC} venv 环境存在"
else
    echo -e "${RED}✗${NC} 未找到 Python 虚拟环境"
fi

echo ""

# 检查日志
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 最近日志"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -f "$PROJECT_ROOT/logs/backend.log" ]]; then
    echo "后端日志（最后5行）:"
    tail -5 "$PROJECT_ROOT/logs/backend.log" 2>/dev/null | sed 's/^/   /'
else
    echo "   未找到后端日志"
fi

echo ""

if [[ -f "$PROJECT_ROOT/logs/frontend.log" ]]; then
    echo "前端日志（最后5行）:"
    tail -5 "$PROJECT_ROOT/logs/frontend.log" 2>/dev/null | sed 's/^/   /'
else
    echo "   未找到前端日志"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 检查完成"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

