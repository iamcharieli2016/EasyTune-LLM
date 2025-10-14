# EasyTune-LLM 本地环境安装指南

## 📋 目录
- [系统要求](#系统要求)
- [快速安装](#快速安装)
- [详细安装步骤](#详细安装步骤)
- [验证安装](#验证安装)
- [常见问题](#常见问题)

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|-----|---------|---------|
| **CPU** | 4 核心 | 8 核心+ |
| **内存** | 16GB | 32GB+ |
| **显卡** | 无 | NVIDIA GPU (8GB+ 显存) 或 Apple Silicon (M1/M2/M3) |
| **磁盘** | 50GB 可用空间 | 100GB+ SSD |

### 软件要求

| 软件 | 版本要求 | 用途 |
|-----|---------|------|
| **Python** | 3.9 - 3.11 | 后端和训练引擎 |
| **Node.js** | 16+ | 前端开发 |
| **PostgreSQL** | 14+ | 数据库 |
| **Conda** | Miniconda/Anaconda | Python 环境管理（推荐）|
| **Git** | 2.0+ | 代码管理 |

### 可选软件

| 软件 | 用途 |
|-----|------|
| **CUDA** | NVIDIA GPU 加速（11.8+）|
| **Docker** | 容器化部署 |

---

## 快速安装

### MacOS / Linux

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/EasyTune-LLM.git
cd EasyTune-LLM

# 2. 运行一键安装脚本
chmod +x install.sh
./install.sh

# 3. 启动服务
./start_all.sh
```

### Windows

```powershell
# 1. 克隆项目
git clone https://github.com/your-repo/EasyTune-LLM.git
cd EasyTune-LLM

# 2. 运行安装脚本
.\install.ps1

# 3. 启动服务
.\start_all.ps1
```

---

## 详细安装步骤

### 步骤 1: 安装系统依赖

#### MacOS

```bash
# 安装 Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install python@3.10 node postgresql git

# 启动 PostgreSQL
brew services start postgresql
```

#### Ubuntu / Debian

```bash
# 更新包列表
sudo apt update

# 安装依赖
sudo apt install -y python3.10 python3-pip nodejs npm postgresql git

# 启动 PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Windows

1. 下载并安装 [Python 3.10](https://www.python.org/downloads/)
2. 下载并安装 [Node.js](https://nodejs.org/)
3. 下载并安装 [PostgreSQL](https://www.postgresql.org/download/windows/)
4. 下载并安装 [Git](https://git-scm.com/download/win)

### 步骤 2: 克隆项目

```bash
git clone https://github.com/your-repo/EasyTune-LLM.git
cd EasyTune-LLM
```

### 步骤 3: 配置数据库

```bash
# 创建数据库
createdb easytune_db

# 或使用 psql
psql -U postgres
CREATE DATABASE easytune_db;
CREATE USER easytune_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE easytune_db TO easytune_user;
\q
```

### 步骤 4: 安装 Python 环境

#### 使用 Conda（推荐）

```bash
# 创建虚拟环境
conda create -n easytune python=3.10
conda activate easytune

# 安装后端依赖
cd backend
pip install -r requirements.txt
cd ..

# 安装训练引擎依赖
cd training-engine
pip install -r requirements.txt
cd ..
```

#### 使用 venv

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/MacOS
# 或 venv\Scripts\activate  # Windows

# 安装后端依赖
cd backend
pip install -r requirements.txt
cd ..

# 安装训练引擎依赖
cd training-engine
pip install -r requirements.txt
cd ..
```

### 步骤 5: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件
nano .env  # 或使用你喜欢的编辑器
```

`.env` 文件示例：

```bash
# 数据库配置
DATABASE_URL=postgresql://easytune_user:your_password@localhost:5432/easytune_db

# JWT 配置
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 项目路径
PROJECT_ROOT=/absolute/path/to/EasyTune-LLM

# 端口配置
BACKEND_PORT=8000
FRONTEND_PORT=5173

# 文件上传
MAX_FILE_SIZE=524288000  # 500MB

# HuggingFace 配置（可选）
HF_ENDPOINT=https://hf-mirror.com  # 国内镜像加速
```

### 步骤 6: 数据库迁移

```bash
# 进入后端目录
cd backend

# 运行数据库迁移
alembic upgrade head

# 返回项目根目录
cd ..
```

### 步骤 7: 安装前端依赖

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 返回项目根目录
cd ..
```

### 步骤 8: 创建必要的目录

```bash
# 创建数据目录
mkdir -p uploads
mkdir -p lora_adapters
mkdir -p logs/training
mkdir -p cache
```

### 步骤 9: 启动服务

#### 启动后端

```bash
# 方式 1: 使用启动脚本（推荐）
chmod +x start_backend_fixed.sh
./start_backend_fixed.sh

# 方式 2: 手动启动
cd backend/api-gateway
export PYTHONPATH="/absolute/path/to/EasyTune-LLM:$PYTHONPATH"
uvicorn main:app --reload --port 8000
```

#### 启动前端

```bash
# 新开一个终端窗口
cd frontend
npm run dev
```

### 步骤 10: 访问系统

```bash
# 前端地址
http://localhost:5173

# 后端 API 文档
http://localhost:8000/docs

# 默认登录账号
用户名: admin
密码: admin123
```

---

## 验证安装

### 1. 检查后端服务

```bash
# 测试 API 健康检查
curl http://localhost:8000/api/v1/health

# 预期输出
{"status": "healthy"}
```

### 2. 检查数据库连接

```bash
# 连接数据库
psql -U easytune_user -d easytune_db

# 列出表
\dt

# 预期输出
 Schema |    Name    | Type  |     Owner      
--------+------------+-------+----------------
 public | alembic_version | table | easytune_user
 public | datasets   | table | easytune_user
 public | models     | table | easytune_user
 public | tasks      | table | easytune_user
 public | users      | table | easytune_user
```

### 3. 检查前端服务

访问 `http://localhost:5173`，应该看到登录页面。

### 4. 完整功能测试

```bash
# 1. 登录系统
# 2. 上传测试数据集
# 3. 添加模型
# 4. 创建训练任务
# 5. 查看训练日志
```

---

## 常见问题

### Q1: 端口被占用

**问题**: `Address already in use`

**解决**:
```bash
# 查看占用端口的进程
lsof -i :8000  # 后端端口
lsof -i :5173  # 前端端口

# 杀死进程
kill -9 <PID>

# 或修改端口
# 后端: 修改 .env 中的 BACKEND_PORT
# 前端: 修改 frontend/vite.config.ts 中的 port
```

### Q2: 数据库连接失败

**问题**: `could not connect to server: Connection refused`

**解决**:
```bash
# 检查 PostgreSQL 是否运行
# MacOS
brew services list | grep postgresql

# Ubuntu
sudo systemctl status postgresql

# 启动 PostgreSQL
# MacOS
brew services start postgresql

# Ubuntu
sudo systemctl start postgresql
```

### Q3: Python 模块找不到

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```bash
# 确保激活了虚拟环境
conda activate easytune  # Conda
# 或
source venv/bin/activate  # venv

# 重新安装依赖
pip install -r backend/requirements.txt
pip install -r training-engine/requirements.txt
```

### Q4: 前端编译错误

**问题**: `Module not found: Error: Can't resolve 'xxx'`

**解决**:
```bash
# 删除 node_modules 和 lock 文件
cd frontend
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### Q5: PYTHONPATH 错误

**问题**: `ModuleNotFoundError: No module named 'backend'`

**解决**:
```bash
# 确保设置了 PYTHONPATH
export PYTHONPATH="/absolute/path/to/EasyTune-LLM:$PYTHONPATH"

# 或使用启动脚本
./start_backend_fixed.sh
```

### Q6: GPU 不可用

**问题**: 训练时无法使用 GPU

**解决**:
```bash
# 检查 CUDA 是否安装（NVIDIA GPU）
nvcc --version
nvidia-smi

# 检查 PyTorch CUDA 支持
python -c "import torch; print(torch.cuda.is_available())"

# 重新安装支持 CUDA 的 PyTorch
pip uninstall torch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# MacOS (Apple Silicon) 自动支持 MPS
python -c "import torch; print(torch.backends.mps.is_available())"
```

### Q7: 模型下载超时

**问题**: HuggingFace 模型下载失败

**解决**:
```bash
# 使用国内镜像
export HF_ENDPOINT=https://hf-mirror.com

# 或使用 ModelScope
pip install modelscope
python -c "from modelscope import snapshot_download; snapshot_download('qwen/Qwen2-7B')"

# 详见 DEPLOYMENT.md 的模型下载部分
```

### Q8: 训练任务卡在 PENDING

**问题**: 任务创建后一直不启动

**解决**:
```bash
# 检查后端日志
tail -f backend/api-gateway/logs/app.log

# 检查训练日志
ls -lh logs/training/

# 手动测试训练启动
python -c "
from backend.common.training_runner import start_training_task
start_training_task(1)  # 任务 ID
"
```

---

## 开发工具推荐

### IDE
- **VSCode**: 推荐，插件丰富
- **PyCharm**: Python 开发强大
- **WebStorm**: 前端开发专业

### VSCode 插件
- Python
- Pylance
- ESLint
- Prettier
- GitLens
- REST Client

### 调试工具
- **后端**: FastAPI 自带交互式 API 文档 `/docs`
- **前端**: React Developer Tools（浏览器插件）
- **数据库**: pgAdmin 4, TablePlus

---

## 下一步

- 📖 阅读 [平台功能介绍.md](./平台功能介绍.md) 了解功能详情
- 🏗️ 阅读 [ARCHITECTURE.md](./ARCHITECTURE.md) 了解架构设计
- 🚀 阅读 [DEPLOYMENT.md](./DEPLOYMENT.md) 了解生产部署
- 📝 查看 [README.md](./README.md) 快速上手

---

<div align="center">

**需要帮助？**

- 📧 提交 [Issue](https://github.com/your-repo/EasyTune-LLM/issues)
- 💬 加入讨论群

</div>

