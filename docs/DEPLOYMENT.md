# 🚀 EasyTune-LLM 部署指南

## 📋 目录

- [系统要求](#系统要求)
- [快速开始 (Docker Compose)](#快速开始-docker-compose)
- [手动部署](#手动部署)
- [生产环境部署 (Kubernetes)](#生产环境部署-kubernetes)
- [配置说明](#配置说明)
- [常见问题](#常见问题)

## 系统要求

### 最低配置
- **CPU**: 4核
- **内存**: 16GB RAM
- **存储**: 100GB 可用空间
- **GPU**: NVIDIA GPU 8GB+ (推荐)
- **操作系统**: Linux (Ubuntu 20.04+) / macOS / Windows (WSL2)

### 推荐配置
- **CPU**: 8核+
- **内存**: 32GB+ RAM
- **存储**: 500GB+ SSD
- **GPU**: NVIDIA A100 / V100 / 3090+
- **操作系统**: Ubuntu 22.04 LTS

### 软件依赖
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker (GPU训练)
- Python 3.10+ (手动部署)
- Node.js 18+ (手动部署)

## 快速开始 (Docker Compose)

### 1. 克隆项目

```bash
git clone https://github.com/your-org/EasyTune-LLM.git
cd EasyTune-LLM
```

### 2. 配置环境变量

```bash
# 复制环境配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**重要配置项**：
```bash
# 修改JWT密钥（生产环境必须更改）
SECRET_KEY=your-very-long-and-random-secret-key-here

# 数据库配置
DATABASE_URL=postgresql://easytune:easytune@postgres:5432/easytune_db

# Redis配置
REDIS_HOST=redis
REDIS_PORT=6379
```

### 3. 启动所有服务

```bash
# 使用启动脚本（推荐）
chmod +x deployment/scripts/start.sh
./deployment/scripts/start.sh

# 或手动启动
docker-compose up -d
```

### 4. 初始化数据库

```bash
# 等待服务启动（约30秒）
sleep 30

# 初始化数据库
docker-compose exec api-gateway python deployment/scripts/init_db.py
```

### 5. 访问平台

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs
- **默认账号**: admin / admin123

### 6. 验证部署

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 健康检查
curl http://localhost:8000/health
```

## 手动部署

### 后端服务部署

#### 1. 安装PostgreSQL

```bash
# Ubuntu
sudo apt update
sudo apt install postgresql postgresql-contrib

# 创建数据库和用户
sudo -u postgres psql
CREATE DATABASE easytune_db;
CREATE USER easytune WITH PASSWORD 'easytune';
GRANT ALL PRIVILEGES ON DATABASE easytune_db TO easytune;
\q
```

#### 2. 安装Redis

```bash
# Ubuntu
sudo apt install redis-server

# 启动Redis
sudo systemctl start redis
sudo systemctl enable redis
```

#### 3. 部署后端API

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
export DATABASE_URL="postgresql://easytune:easytune@localhost:5432/easytune_db"
export SECRET_KEY="your-secret-key"

# 初始化数据库
cd ..
python deployment/scripts/init_db.py

# 启动API网关
cd backend/api-gateway
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 4. 部署训练引擎

```bash
cd training-engine

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装PyTorch (CUDA 11.8)
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装其他依赖
pip install -r requirements.txt

# 启动训练服务
python src/trainer_service.py
```

### 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 使用Nginx部署
sudo cp -r build/* /var/www/easytune-llm/
```

#### Nginx配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/easytune-llm;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 生产环境部署 (Kubernetes)

### 1. 准备Kubernetes集群

```bash
# 确认集群状态
kubectl cluster-info
kubectl get nodes
```

### 2. 创建命名空间

```bash
kubectl create namespace easytune-llm
```

### 3. 配置Secrets

```bash
# 创建数据库密钥
kubectl create secret generic db-secret \
  --from-literal=username=easytune \
  --from-literal=password=your-secure-password \
  -n easytune-llm

# 创建JWT密钥
kubectl create secret generic jwt-secret \
  --from-literal=secret-key=your-very-long-secret-key \
  -n easytune-llm
```

### 4. 部署存储

```bash
# 创建PersistentVolume和PersistentVolumeClaim
kubectl apply -f deployment/kubernetes/storage.yaml
```

### 5. 部署数据库和Redis

```bash
kubectl apply -f deployment/kubernetes/postgres.yaml
kubectl apply -f deployment/kubernetes/redis.yaml
```

### 6. 部署应用服务

```bash
# API网关
kubectl apply -f deployment/kubernetes/api-gateway.yaml

# 训练引擎
kubectl apply -f deployment/kubernetes/training-engine.yaml

# 前端
kubectl apply -f deployment/kubernetes/frontend.yaml
```

### 7. 配置Ingress

```bash
kubectl apply -f deployment/kubernetes/ingress.yaml
```

### 8. 验证部署

```bash
# 查看所有资源
kubectl get all -n easytune-llm

# 查看日志
kubectl logs -f deployment/api-gateway -n easytune-llm

# 访问应用
kubectl port-forward svc/frontend 3000:80 -n easytune-llm
```

## 配置说明

### 数据库配置

```python
# backend/common/config.py
DATABASE_URL = "postgresql://user:password@host:5432/dbname"
DB_POOL_SIZE = 10  # 连接池大小
DB_MAX_OVERFLOW = 20  # 最大溢出连接
```

### LoRA默认配置

```python
# L1 - 基础风格调整
LORA_CONFIG_L1 = {
    "rank": 8,
    "alpha": 16,
    "target_modules": ["q_proj", "k_proj", "v_proj"],
    "learning_rate": 3e-4,
}

# L2 - 领域知识注入
LORA_CONFIG_L2 = {
    "rank": 16,
    "alpha": 32,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "learning_rate": 1e-4,
}

# L3 - 复杂指令重塑
LORA_CONFIG_L3 = {
    "rank": 32,
    "alpha": 64,
    "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    "learning_rate": 5e-5,
}
```

### GPU配置

```bash
# 指定使用的GPU
export CUDA_VISIBLE_DEVICES=0,1,2,3

# 启用混合精度训练
USE_MIXED_PRECISION=True
```

## 常见问题

### 1. GPU无法识别

**问题**: 训练时提示"CUDA not available"

**解决方案**:
```bash
# 检查NVIDIA驱动
nvidia-smi

# 安装NVIDIA Docker支持
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# 测试GPU访问
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 2. 数据库连接失败

**问题**: "could not connect to server"

**解决方案**:
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 检查连接配置
psql -h localhost -U easytune -d easytune_db

# 修改pg_hba.conf允许密码连接
sudo nano /etc/postgresql/15/main/pg_hba.conf
# 添加: host all all 0.0.0.0/0 md5
```

### 3. 端口被占用

**问题**: "Address already in use"

**解决方案**:
```bash
# 查找占用端口的进程
sudo lsof -i :8000

# 杀死进程
sudo kill -9 <PID>

# 或修改配置使用其他端口
PORT=8001 uvicorn main:app
```

### 4. 内存不足

**问题**: "CUDA out of memory"

**解决方案**:
```python
# 减小batch size
batch_size = 2

# 启用梯度累积
gradient_accumulation_steps = 8

# 启用梯度检查点
gradient_checkpointing = True

# 使用更小的模型或更低的LoRA rank
lora_rank = 4
```

### 5. 训练速度慢

**优化建议**:
```python
# 使用混合精度
fp16 = True  # 或 bf16 = True

# 增加num_workers
dataloader_num_workers = 4

# 使用更快的优化器
optimizer = "adamw_torch_fused"

# 预编译模型
torch.compile(model)
```

## 🔧 维护和监控

### 日志查看

```bash
# Docker Compose
docker-compose logs -f [service_name]

# Kubernetes
kubectl logs -f deployment/api-gateway -n easytune-llm
```

### 备份数据库

```bash
# 备份
docker-compose exec postgres pg_dump -U easytune easytune_db > backup.sql

# 恢复
docker-compose exec -T postgres psql -U easytune easytune_db < backup.sql
```

### 更新服务

```bash
# 拉取最新代码
git pull origin main

# 重新构建
docker-compose build

# 重启服务
docker-compose down
docker-compose up -d
```

## 📞 获取帮助

- **文档**: https://docs.easytune-llm.com
- **GitHub Issues**: https://github.com/your-org/EasyTune-LLM/issues
- **Discord社区**: https://discord.gg/easytune-llm
- **邮件支持**: support@easytune-llm.com

---

**祝您部署顺利！** 🎉

