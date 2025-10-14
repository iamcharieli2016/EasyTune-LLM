#!/bin/bash

# EasyTune-LLM 启动脚本

set -e

echo "=========================================="
echo "EasyTune-LLM 启动脚本"
echo "=========================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker未安装${NC}"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: Docker Compose未安装${NC}"
    echo "请先安装Docker Compose"
    exit 1
fi

# 检查环境配置文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: .env文件不存在${NC}"
    echo "从env.example创建.env文件..."
    cp env.example .env
    echo -e "${GREEN}.env文件创建成功${NC}"
    echo "请根据需要修改.env文件中的配置"
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p uploads models lora_adapters cache logs

# 拉取最新镜像
echo -e "${GREEN}拉取Docker镜像...${NC}"
docker-compose pull

# 构建镜像
echo -e "${GREEN}构建Docker镜像...${NC}"
docker-compose build

# 启动服务
echo -e "${GREEN}启动服务...${NC}"
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 初始化数据库
echo -e "${GREEN}初始化数据库...${NC}"
docker-compose exec api-gateway python deployment/scripts/init_db.py

# 检查服务状态
echo -e "\n${GREEN}服务状态:${NC}"
docker-compose ps

# 显示访问信息
echo -e "\n=========================================="
echo -e "${GREEN}EasyTune-LLM 启动成功！${NC}"
echo -e "=========================================="
echo -e "前端地址: ${GREEN}http://localhost:3000${NC}"
echo -e "API文档: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "默认管理员账号: ${YELLOW}admin / admin123${NC}"
echo -e "=========================================="
echo -e "\n查看日志: ${YELLOW}docker-compose logs -f${NC}"
echo -e "停止服务: ${YELLOW}docker-compose down${NC}"
echo -e "=========================================="

