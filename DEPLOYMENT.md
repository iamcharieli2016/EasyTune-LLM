# EasyTune-LLM 生产环境部署指南

## 📋 目录
- [部署架构](#部署架构)
- [Docker部署](#docker部署)
- [手动部署](#手动部署)
- [生产配置](#生产配置)
- [性能优化](#性能优化)
- [监控告警](#监控告警)
- [故障排查](#故障排查)

---

## 部署架构

### 推荐架构

```
             Internet
                 │
                 ▼
        ┌────────────────┐
        │  Nginx (443)   │  ← SSL 终止 + 负载均衡
        └────────┬───────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
┌────────┐  ┌────────┐  ┌────────┐
│Frontend│  │Backend │  │Backend │
│ Static │  │ Worker1│  │ Worker2│
└────────┘  └────┬───┘  └────┬───┘
                  │           │
                  └─────┬─────┘
                        │
              ┌─────────▼──────────┐
              │   PostgreSQL       │
              │   (主从复制)       │
              └────────────────────┘
                        │
              ┌─────────▼──────────┐
              │   文件存储         │
              │   (NFS/S3/OSS)     │
              └────────────────────┘
```

---

## Docker 部署

### 方式 1: Docker Compose（推荐）

#### 1.1 准备工作

```bash
# 克隆项目
git clone https://github.com/your-repo/EasyTune-LLM.git
cd EasyTune-LLM

# 复制环境变量
cp .env.example .env.production

# 编辑配置
nano .env.production
```

#### 1.2 创建 `docker-compose.yml`

```yaml
version: '3.8'

services:
  # Nginx 前端代理
  nginx:
    image: nginx:alpine
    container_name: easytune-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./uploads:/usr/share/nginx/uploads:ro
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - easytune-network

  # 后端服务
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: easytune-backend
    command: gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
    environment:
      - DATABASE_URL=postgresql://easytune:${DB_PASSWORD}@postgres:5432/easytune_db
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - PROJECT_ROOT=/app
    volumes:
      - ./uploads:/app/uploads
      - ./lora_adapters:/app/lora_adapters
      - ./logs:/app/logs
      - ./cache:/app/cache
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - easytune-network

  # PostgreSQL 数据库
  postgres:
    image: postgres:14-alpine
    container_name: easytune-postgres
    environment:
      - POSTGRES_USER=easytune
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=easytune_db
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - easytune-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U easytune"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis 缓存
  redis:
    image: redis:alpine
    container_name: easytune-redis
    restart: unless-stopped
    networks:
      - easytune-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:

networks:
  easytune-network:
    driver: bridge
```

#### 1.3 创建 Nginx 配置

```bash
mkdir -p nginx
cat > nginx/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 500M;

    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript 
               application/json application/javascript application/xml+rss 
               application/rss+xml font/truetype font/opentype 
               application/vnd.ms-fontobject image/svg+xml;

    # 后端代理
    upstream backend {
        server backend:8000;
    }

    # HTTP -> HTTPS 重定向
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS 服务
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL 证书
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket 支持
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # 超时设置
            proxy_connect_timeout 600;
            proxy_send_timeout 600;
            proxy_read_timeout 600;
        }

        # 文件上传
        location /uploads/ {
            alias /usr/share/nginx/uploads/;
            autoindex off;
        }
    }
}
EOF
```

#### 1.4 创建后端 Dockerfile

```bash
cat > backend/Dockerfile << 'EOF'
FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY backend/requirements.txt ./backend/
COPY training-engine/requirements.txt ./training-engine/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r backend/requirements.txt
RUN pip install --no-cache-dir -r training-engine/requirements.txt

# 复制项目文件
COPY backend ./backend
COPY training-engine ./training-engine
COPY common ./common

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
```

#### 1.5 构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 1.6 启动服务

```bash
# 启动所有服务
docker-compose -f docker-compose.yml --env-file .env.production up -d

# 查看日志
docker-compose logs -f

# 查看状态
docker-compose ps
```

#### 1.7 数据库迁移

```bash
# 进入后端容器
docker-compose exec backend bash

# 运行迁移
cd backend
alembic upgrade head
exit
```

---

## 手动部署

### 方式 2: 传统部署

#### 2.1 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装依赖
sudo apt install -y python3.10 python3-pip nodejs npm nginx postgresql redis git

# 安装 PM2（进程管理）
sudo npm install -g pm2
```

#### 2.2 部署后端

```bash
# 创建用户
sudo useradd -m -s /bin/bash easytune

# 创建项目目录
sudo mkdir -p /opt/easytune
sudo chown easytune:easytune /opt/easytune

# 切换用户
sudo su - easytune
cd /opt/easytune

# 克隆项目
git clone https://github.com/your-repo/EasyTune-LLM.git
cd EasyTune-LLM

# 安装 Python 依赖
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
pip install -r training-engine/requirements.txt
pip install gunicorn

# 配置环境变量
cp .env.example .env.production
nano .env.production

# 数据库迁移
cd backend
alembic upgrade head
cd ..

# 使用 PM2 启动后端
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

#### 2.3 部署前端

```bash
# 构建前端
cd frontend
npm install
npm run build

# 复制到 Nginx 目录
sudo cp -r dist/* /var/www/easytune/
```

#### 2.4 配置 Nginx

```bash
# 创建配置文件
sudo nano /etc/nginx/sites-available/easytune

# 内容同上面的 nginx.conf

# 启用站点
sudo ln -s /etc/nginx/sites-available/easytune /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 2.5 配置 Systemd

```bash
# 创建后端服务
sudo nano /etc/systemd/system/easytune-backend.service
```

内容：

```ini
[Unit]
Description=EasyTune-LLM Backend
After=network.target postgresql.service

[Service]
Type=simple
User=easytune
WorkingDirectory=/opt/easytune/EasyTune-LLM
Environment="PYTHONPATH=/opt/easytune/EasyTune-LLM"
ExecStart=/opt/easytune/EasyTune-LLM/venv/bin/gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable easytune-backend
sudo systemctl start easytune-backend
sudo systemctl status easytune-backend
```

---

## 生产配置

### SSL 证书

#### 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

### 环境变量

`.env.production` 示例：

```bash
# 数据库
DATABASE_URL=postgresql://easytune:STRONG_PASSWORD@localhost:5432/easytune_db

# JWT
SECRET_KEY=STRONG_RANDOM_KEY_HERE
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 项目路径
PROJECT_ROOT=/opt/easytune/EasyTune-LLM

# 端口
BACKEND_PORT=8000

# 文件上传
MAX_FILE_SIZE=524288000

# 日志级别
LOG_LEVEL=INFO

# Redis
REDIS_URL=redis://localhost:6379/0

# HuggingFace
HF_ENDPOINT=https://hf-mirror.com
```

### 数据库优化

```sql
-- PostgreSQL 配置
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;
ALTER SYSTEM SET work_mem = '16MB';
ALTER SYSTEM SET min_wal_size = '1GB';
ALTER SYSTEM SET max_wal_size = '4GB';

-- 重启 PostgreSQL
sudo systemctl restart postgresql

-- 创建索引
CREATE INDEX idx_datasets_user_id ON datasets(user_id);
CREATE INDEX idx_datasets_created_at ON datasets(created_at DESC);
CREATE INDEX idx_models_user_id ON models(user_id);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
```

---

## 性能优化

### 后端优化

#### Gunicorn 配置

```python
# gunicorn.conf.py
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5

# 日志
accesslog = "/opt/easytune/logs/gunicorn-access.log"
errorlog = "/opt/easytune/logs/gunicorn-error.log"
loglevel = "info"
```

#### 数据库连接池

```python
# backend/common/database.py
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,              # 连接池大小
    max_overflow=10,           # 溢出连接数
    pool_recycle=3600,         # 连接回收时间（秒）
    pool_pre_ping=True,        # 连接前检查
    echo=False                 # 生产环境关闭 SQL 日志
)
```

### 前端优化

#### Nginx 缓存

```nginx
# 静态文件缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# HTML 不缓存
location ~* \.html$ {
    expires -1;
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

### 模型下载加速

#### 方案 1: 使用 ModelScope

```bash
# 安装 ModelScope
pip install modelscope

# 下载模型
python << 'EOF'
from modelscope import snapshot_download
snapshot_download('qwen/Qwen2-7B', cache_dir='/data/models')
EOF
```

#### 方案 2: 预下载常用模型

```bash
# 创建下载脚本
cat > download_models.sh << 'EOF'
#!/bin/bash
export HF_ENDPOINT=https://hf-mirror.com

models=(
    "Qwen/Qwen2-7B"
    "Qwen/Qwen2-1.5B"
)

for model in "${models[@]}"; do
    echo "Downloading $model..."
    huggingface-cli download --repo-type model "$model"
done
EOF

chmod +x download_models.sh
./download_models.sh
```

---

## 监控告警

### Prometheus + Grafana

#### 安装 Prometheus

```bash
# 下载 Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# 配置
cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'easytune-backend'
    static_configs:
      - targets: ['localhost:8000']
EOF

# 启动
./prometheus --config.file=prometheus.yml
```

#### 后端暴露指标

```python
# backend/api-gateway/main.py
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# 定义指标
api_requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration')

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    api_requests_total.labels(method=request.method, endpoint=request.url.path).inc()
    api_request_duration.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

### 日志收集（ELK）

```bash
# 安装 Filebeat
wget https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-8.8.0-amd64.deb
sudo dpkg -i filebeat-8.8.0-amd64.deb

# 配置 Filebeat
sudo nano /etc/filebeat/filebeat.yml

# 启动
sudo systemctl enable filebeat
sudo systemctl start filebeat
```

### 告警规则

```yaml
# alertmanager.yml
groups:
  - name: easytune
    rules:
      - alert: HighErrorRate
        expr: rate(api_requests_total{status="500"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
      
      - alert: DatabaseConnectionPoolFull
        expr: pg_stat_database_numbackends > 90
        for: 5m
        annotations:
          summary: "Database connection pool nearly full"
```

---

## 故障排查

### 常见生产问题

#### 1. 后端无响应

```bash
# 检查进程
ps aux | grep gunicorn

# 检查日志
tail -f /opt/easytune/logs/gunicorn-error.log

# 检查端口
netstat -tlnp | grep 8000

# 重启服务
sudo systemctl restart easytune-backend
```

#### 2. 数据库连接耗尽

```sql
-- 查看当前连接数
SELECT count(*) FROM pg_stat_activity;

-- 查看最大连接数
SHOW max_connections;

-- 杀死空闲连接
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'idle'
  AND state_change < NOW() - INTERVAL '30 minutes';
```

#### 3. 磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 清理日志
sudo find /opt/easytune/logs -name "*.log" -mtime +7 -delete

# 清理模型缓存
rm -rf ~/.cache/huggingface/hub/blobs/*.incomplete
```

#### 4. 训练任务卡死

```bash
# 查看训练进程
ps aux | grep trainer.py

# 检查 GPU 使用
nvidia-smi  # NVIDIA
# 或
ps aux | grep python  # CPU

# 杀死僵尸进程
pkill -f trainer.py
```

---

## 备份策略

### 数据库备份

```bash
# 每日自动备份
cat > /opt/easytune/backup_db.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/opt/easytune/backups"
mkdir -p $BACKUP_DIR

pg_dump easytune_db > $BACKUP_DIR/easytune_db_$DATE.sql
gzip $BACKUP_DIR/easytune_db_$DATE.sql

# 保留最近 7 天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x /opt/easytune/backup_db.sh

# 添加到 crontab
crontab -e
# 添加: 0 2 * * * /opt/easytune/backup_db.sh
```

### 文件备份

```bash
# 备份上传文件和模型
rsync -avz /opt/easytune/EasyTune-LLM/uploads/ user@backup-server:/backups/uploads/
rsync -avz /opt/easytune/EasyTune-LLM/lora_adapters/ user@backup-server:/backups/lora_adapters/
```

---

<div align="center">

**生产环境部署完成！**

需要帮助？提交 [Issue](https://github.com/your-repo/EasyTune-LLM/issues)

</div>

