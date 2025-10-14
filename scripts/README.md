# EasyTune-LLM 脚本使用指南

## 📋 脚本列表

项目根目录包含 4 个核心脚本，用于本地开发环境的管理：

| 脚本 | 大小 | 用途 |
|-----|------|------|
| **install.sh** | 8.5KB | 本地环境安装和配置 |
| **start.sh** | 8.0KB | 启动所有服务（后端+前端）|
| **stop.sh** | 2.9KB | 停止所有服务 |
| **check.sh** | 6.3KB | 检查服务状态 |

---

## 🚀 快速开始

### 首次安装

```bash
# 1. 克隆项目（如果还没有）
git clone https://github.com/your-repo/EasyTune-LLM.git
cd EasyTune-LLM

# 2. 运行安装脚本
./install.sh

# 3. 启动服务
./start.sh

# 4. 访问平台
open http://localhost:5173
```

### 日常使用

```bash
# 启动服务
./start.sh

# 检查状态
./check.sh

# 停止服务
./stop.sh
```

---

## 📖 详细说明

### 1️⃣ install.sh - 环境安装脚本

#### 功能
- 检查系统依赖（Python、Node.js、PostgreSQL、Git）
- 创建 Python 虚拟环境（Conda 或 venv）
- 安装 Python 依赖
- 配置数据库
- 生成 .env 配置文件
- 运行数据库迁移
- 安装前端依赖
- 创建必要的目录

#### 使用方法
```bash
./install.sh
```

#### 前置要求
- Python 3.9+
- Node.js 16+
- PostgreSQL 14+（或 Docker）
- Git

#### 执行步骤
```
步骤 1/7: 检查系统依赖
步骤 2/7: 创建 Python 虚拟环境
步骤 3/7: 安装 Python 依赖
步骤 4/7: 配置数据库
步骤 5/7: 配置环境变量
步骤 6/7: 运行数据库迁移
步骤 7/7: 安装前端依赖
```

#### 支持的系统
- ✅ MacOS (Intel / Apple Silicon)
- ✅ Linux (Ubuntu / Debian / CentOS)

---

### 2️⃣ start.sh - 启动服务脚本

#### 功能
- 自动检测操作系统
- 检查并启动数据库
- 激活 Python 虚拟环境
- 检查端口占用
- 启动后端服务（uvicorn）
- 启动前端服务（vite）
- 保存进程 PID
- 自动打开浏览器（MacOS）

#### 使用方法
```bash
./start.sh
```

#### 服务端口
- 后端: http://localhost:8000
- 前端: http://localhost:5173
- API文档: http://localhost:8000/docs

#### 后台运行
脚本会在后台启动服务，日志输出到：
- `logs/backend.log` - 后端日志
- `logs/frontend.log` - 前端日志

#### 进程管理
PID 保存在：
- `.backend.pid` - 后端进程 PID
- `.frontend.pid` - 前端进程 PID

---

### 3️⃣ stop.sh - 停止服务脚本

#### 功能
- 停止后端服务
- 停止前端服务
- 停止所有训练进程
- 清理 PID 文件
- 优雅停止（SIGTERM）+ 强制停止（SIGKILL）

#### 使用方法
```bash
./stop.sh
```

#### 停止顺序
```
1. 读取 PID 文件，停止后端
2. 读取 PID 文件，停止前端
3. 查找并停止训练进程
4. 通过端口查找并停止残留进程
5. 清理 PID 文件
```

---

### 4️⃣ check.sh - 状态检查脚本

#### 功能
- 检查数据库服务状态
- 检查后端服务状态（端口 8000）
- 检查前端服务状态（端口 5173）
- 检查训练进程
- 检查磁盘空间
- 检查数据目录大小
- 检查 Python 环境
- 显示最近日志

#### 使用方法
```bash
./check.sh
```

#### 输出示例
```
🔍 EasyTune-LLM 服务状态检查
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🗄️ 数据库服务
✓ PostgreSQL 运行中
  psql (PostgreSQL) 14.5

🔧 后端服务
✓ 后端运行中 (PID: 12345)
  端口: 8000
✓ API 可访问
  URL: http://localhost:8000/docs

🎨 前端服务
✓ 前端运行中 (PID: 12346)
  端口: 5173
  URL: http://localhost:5173

🚀 训练进程
ℹ 无训练进程运行

💾 磁盘空间
✓ 磁盘空间充足
  使用率: 45%
  可用: 50G

📁 数据目录：
  uploads: 2.1G
  lora_adapters: 5.4G
  logs: 128M
```

---

## 🔧 故障排查

### 问题 1: 端口被占用

**现象**:
```
⚠ 端口 8000 已被占用
```

**解决**:
```bash
# 查看占用进程
lsof -i :8000

# 停止占用进程
./stop.sh

# 或手动杀死
kill -9 $(lsof -ti:8000)
```

---

### 问题 2: 数据库连接失败

**现象**:
```
✗ PostgreSQL 未运行
```

**解决**:
```bash
# MacOS
brew services start postgresql@14

# Linux
sudo systemctl start postgresql

# 或使用 Docker
docker start easytune-postgres
```

---

### 问题 3: Python 环境未激活

**现象**:
```
✗ 未找到 Python 虚拟环境
```

**解决**:
```bash
# 重新运行安装脚本
./install.sh

# 或手动创建环境
conda create -n easytune python=3.10
conda activate easytune
```

---

### 问题 4: 前端依赖错误

**现象**:
```
Module not found: Error: Can't resolve 'xxx'
```

**解决**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
cd ..
./start.sh
```

---

### 问题 5: 后端启动失败

**现象**:
```
✗ 后端启动失败
```

**排查步骤**:
```bash
# 1. 查看日志
tail -f logs/backend.log

# 2. 检查环境变量
cat .env

# 3. 测试数据库连接
psql -h localhost -U postgres -d easytune_db

# 4. 手动启动测试
cd backend/api-gateway
export PYTHONPATH="/path/to/project:$PYTHONPATH"
uvicorn main:app --reload
```

---

## 💡 高级用法

### 自定义端口

编辑 `.env` 文件：
```bash
BACKEND_PORT=8888
FRONTEND_PORT=3000
```

然后修改脚本中的端口检查部分。

---

### 后台运行（不占用终端）

脚本默认已经在后台运行，如果需要完全分离：

```bash
nohup ./start.sh > /dev/null 2>&1 &
```

---

### 查看实时日志

```bash
# 后端日志
tail -f logs/backend.log

# 前端日志
tail -f logs/frontend.log

# 训练日志
tail -f logs/training/task_1.log
```

---

### 性能监控

```bash
# 监控 CPU 和内存
top -p $(cat .backend.pid .frontend.pid)

# 监控网络
netstat -an | grep ':8000\|:5173'

# 监控磁盘 I/O
iotop -p $(cat .backend.pid)
```

---

## 📚 相关文档

- [INSTALLATION.md](../INSTALLATION.md) - 详细安装指南
- [DEPLOYMENT.md](../DEPLOYMENT.md) - 生产环境部署
- [ARCHITECTURE.md](../ARCHITECTURE.md) - 系统架构设计

---

## ⚙️ 脚本维护

### 修改脚本

所有脚本都可以根据需要自定义：

```bash
# 编辑启动脚本
nano start.sh

# 添加执行权限
chmod +x start.sh
```

### 添加新脚本

```bash
# 创建新脚本
cat > backup.sh << 'EOF'
#!/bin/bash
# 备份脚本
echo "开始备份..."
EOF

# 添加执行权限
chmod +x backup.sh
```

---

<div align="center">

**需要帮助？**

查看 [INSTALLATION.md](../INSTALLATION.md) 或提交 [Issue](https://github.com/your-repo/EasyTune-LLM/issues)

</div>

