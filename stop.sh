#!/bin/bash

# EasyTune-LLM 停止脚本

echo "=========================================="
echo "🛑 EasyTune-LLM 停止服务"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 获取项目根目录
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$PROJECT_ROOT"

# 停止后端
if [[ -f ".backend.pid" ]]; then
    BACKEND_PID=$(cat .backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "停止后端服务 (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
        sleep 1
        # 如果还在运行，强制杀死
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null
        fi
        echo -e "${GREEN}✓${NC} 后端已停止"
    else
        echo -e "${YELLOW}⚠${NC} 后端进程不存在 (PID: $BACKEND_PID)"
    fi
    rm -f .backend.pid
else
    echo -e "${YELLOW}⚠${NC} 未找到后端 PID 文件"
    # 尝试通过端口查找并停止
    if lsof -ti:8000 > /dev/null 2>&1; then
        echo "通过端口查找并停止后端..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✓${NC} 后端已停止"
    fi
fi

echo ""

# 停止前端
if [[ -f ".frontend.pid" ]]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "停止前端服务 (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID 2>/dev/null
        sleep 1
        # 如果还在运行，强制杀死
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            kill -9 $FRONTEND_PID 2>/dev/null
        fi
        echo -e "${GREEN}✓${NC} 前端已停止"
    else
        echo -e "${YELLOW}⚠${NC} 前端进程不存在 (PID: $FRONTEND_PID)"
    fi
    rm -f .frontend.pid
else
    echo -e "${YELLOW}⚠${NC} 未找到前端 PID 文件"
    # 尝试通过端口查找并停止
    if lsof -ti:5173 > /dev/null 2>&1; then
        echo "通过端口查找并停止前端..."
        lsof -ti:5173 | xargs kill -9 2>/dev/null
        echo -e "${GREEN}✓${NC} 前端已停止"
    fi
fi

echo ""

# 停止所有训练进程
echo "检查训练进程..."
TRAINING_PIDS=$(ps aux | grep "trainer.py" | grep -v grep | awk '{print $2}')
if [[ -n "$TRAINING_PIDS" ]]; then
    echo "发现训练进程，正在停止..."
    echo "$TRAINING_PIDS" | xargs kill 2>/dev/null
    sleep 1
    # 强制杀死
    echo "$TRAINING_PIDS" | xargs kill -9 2>/dev/null
    echo -e "${GREEN}✓${NC} 训练进程已停止"
else
    echo -e "${GREEN}✓${NC} 无训练进程运行"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 所有服务已停止"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

