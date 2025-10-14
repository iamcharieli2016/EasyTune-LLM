# EasyTune-LLM 系统架构设计文档

## 1. 概述

EasyTune-LLM 是一个企业级大语言模型微调平台，采用前后端分离的三层架构设计，旨在降低 LLM 微调的技术门槛，提供零代码的可视化微调解决方案。

### 1.1 设计目标

- **易用性**: 提供可视化 Web 界面，无需编写代码
- **可靠性**: 进程隔离，任务失败不影响主服务
- **可扩展性**: 模块化设计，支持水平扩展
- **高性能**: 异步 I/O，支持 GPU/MPS 加速
- **可维护性**: 清晰的代码结构，完善的日志系统

## 2. 整体架构

### 2.1 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     用户层 (User Layer)                      │
│                      Web 浏览器                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS
┌──────────────────────────▼──────────────────────────────────┐
│                 前端层 (Frontend Layer)                      │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │         React 18 + TypeScript                     │      │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐       │      │
│  │  │ 数据集   │  │  模型    │  │  任务    │       │      │
│  │  │ 管理     │  │  管理    │  │  管理    │       │      │
│  │  └──────────┘  └──────────┘  └──────────┘       │      │
│  │  ┌──────────┐  ┌──────────┐                     │      │
│  │  │ 日志监控 │  │ 仪表盘   │                     │      │
│  │  └──────────┘  └──────────┘                     │      │
│  │                                                   │      │
│  │  UI 组件库: Ant Design 5.x                       │      │
│  │  状态管理: React Hooks                           │      │
│  │  HTTP 客户端: Axios                              │      │
│  └──────────────────────────────────────────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │ RESTful API (JSON)
┌──────────────────────────▼──────────────────────────────────┐
│              API 网关层 (API Gateway Layer)                  │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │              FastAPI Application                  │      │
│  │  ┌──────────────────────────────────────────┐    │      │
│  │  │           API Routers                     │    │      │
│  │  │  • /api/v1/datasets   (数据集)           │    │      │
│  │  │  • /api/v1/models     (模型)             │    │      │
│  │  │  • /api/v1/tasks      (任务)             │    │      │
│  │  │  • /api/v1/logs       (日志)             │    │      │
│  │  └──────────────────────────────────────────┘    │      │
│  │  ┌──────────────────────────────────────────┐    │      │
│  │  │           Middleware                      │    │      │
│  │  │  • CORS 处理                              │    │      │
│  │  │  • 认证授权 (JWT)                         │    │      │
│  │  │  • 请求日志                               │    │      │
│  │  │  • 异常处理                               │    │      │
│  │  └──────────────────────────────────────────┘    │      │
│  └──────────────────────────────────────────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│            业务逻辑层 (Business Logic Layer)                 │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 数据集服务   │  │  模型服务    │  │  训练服务    │     │
│  │ DatasetSvc   │  │  ModelSvc    │  │  TrainingSvc │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ 进程管理     │  │  日志服务    │  │  文件服务    │     │
│  │ ProcessMgr   │  │  LogService  │  │  FileService │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              数据持久层 (Data Layer)                         │
│                                                              │
│  ┌──────────────────────┐      ┌──────────────────────┐    │
│  │   PostgreSQL 14+     │      │   文件系统           │    │
│  │   ┌──────────────┐   │      │   ┌──────────────┐   │    │
│  │   │ 数据集表     │   │      │   │ uploads/     │   │    │
│  │   │ 模型表       │   │      │   │ lora_adapters│   │    │
│  │   │ 任务表       │   │      │   │ logs/        │   │    │
│  │   │ 用户表       │   │      │   │ cache/       │   │    │
│  │   └──────────────┘   │      │   └──────────────┘   │    │
│  └──────────────────────┘      └──────────────────────┘    │
└──────────────────────────┬──────────────────────────────────┘
                           │ subprocess
┌──────────────────────────▼──────────────────────────────────┐
│             训练引擎层 (Training Engine Layer)               │
│                                                              │
│  ┌──────────────────────────────────────────────────┐      │
│  │       独立 Python 进程 (trainer.py)               │      │
│  │                                                   │      │
│  │  PyTorch 2.0+                                    │      │
│  │  Transformers                                    │      │
│  │  PEFT (LoRA/QLoRA)                              │      │
│  │                                                   │      │
│  │  ┌──────────────────────────────────────┐       │      │
│  │  │  数据加载 → 模型加载 → 训练循环      │       │      │
│  │  │  → 保存模型 → 更新状态               │       │      │
│  │  └──────────────────────────────────────┘       │      │
│  └──────────────────────────────────────────────────┘      │
│                                                              │
│  硬件支持: CUDA / MPS / CPU                                 │
└─────────────────────────────────────────────────────────────┘
```

## 3. 核心模块设计

### 3.1 前端架构

#### 3.1.1 技术栈
- **框架**: React 18 (Hooks)
- **语言**: TypeScript 4.9+
- **UI 库**: Ant Design 5.x
- **路由**: React Router v6
- **HTTP**: Axios
- **构建**: Vite

#### 3.1.2 目录结构
```
frontend/
├── src/
│   ├── pages/           # 页面组件
│   │   ├── Dashboard.tsx
│   │   ├── Datasets.tsx
│   │   ├── Models.tsx
│   │   ├── Tasks.tsx
│   │   ├── TaskDetail.tsx
│   │   └── Login.tsx
│   ├── components/      # 公共组件
│   │   ├── Layout/
│   │   └── TrainingLogViewer/
│   ├── services/        # API 服务
│   │   └── api.ts
│   ├── utils/           # 工具函数
│   │   └── errorHandler.ts
│   ├── types/           # TypeScript 类型定义
│   └── App.tsx
├── public/
└── package.json
```

#### 3.1.3 核心设计模式
- **组件化**: 页面级组件 + 通用组件
- **Hooks**: 使用 useState, useEffect, useMemo 管理状态
- **类型安全**: TypeScript 严格模式
- **错误处理**: 统一的 API 错误处理

### 3.2 后端架构

#### 3.2.1 技术栈
- **框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0 (异步)
- **异步**: asyncio + asyncpg
- **验证**: Pydantic v2
- **进程管理**: psutil

#### 3.2.2 目录结构
```
backend/
├── api-gateway/
│   ├── main.py              # 应用入口
│   ├── routers/             # API 路由
│   │   ├── datasets.py
│   │   ├── models.py
│   │   ├── tasks.py
│   │   ├── tasks_management.py
│   │   └── logs.py
│   └── requirements.txt
├── common/
│   ├── models.py            # 数据库模型
│   ├── schemas.py           # Pydantic 模型
│   ├── database.py          # 数据库连接
│   ├── config.py            # 配置管理
│   ├── training_runner.py   # 训练启动器
│   └── process_manager.py   # 进程管理
└── alembic/                 # 数据库迁移
```

#### 3.2.3 核心设计模式
- **RESTful API**: 标准的 HTTP 方法和状态码
- **异步 I/O**: async/await 异步处理
- **依赖注入**: FastAPI Depends
- **分层架构**: Router → Service → Repository

### 3.3 训练引擎

#### 3.3.1 技术栈
- **深度学习**: PyTorch 2.0+
- **模型库**: Transformers
- **微调**: PEFT (LoRA, QLoRA)
- **设备**: CUDA / MPS / CPU

#### 3.3.2 目录结构
```
training-engine/
├── src/
│   ├── trainer.py           # 训练主脚本
│   ├── data_loader.py       # 数据加载
│   ├── model_loader.py      # 模型加载
│   └── utils.py             # 工具函数
└── requirements.txt
```

#### 3.3.3 训练流程
```python
1. 解析命令行参数 (--config, --task-id)
2. 加载训练配置 (JSON)
3. 初始化设备 (CUDA/MPS/CPU)
4. 加载数据集
5. 加载模型和 Tokenizer
6. 配置 LoRA
7. 训练循环
   - Forward pass
   - Backward pass
   - 参数更新
   - 记录日志
8. 保存模型
9. 更新任务状态
```

## 4. 数据库设计

### 4.1 ER 图

```
┌──────────────┐        ┌──────────────┐
│    User      │        │   Dataset    │
├──────────────┤        ├──────────────┤
│ id           │───┐    │ id           │
│ username     │   │    │ name         │
│ password_hash│   │    │ file_path    │
│ created_at   │   │    │ total_samples│
└──────────────┘   │    │ file_format  │
                   │    │ user_id      │──┐
                   │    │ created_at   │  │
                   │    └──────────────┘  │
                   │                      │
                   │    ┌──────────────┐  │
                   │    │    Model     │  │
                   │    ├──────────────┤  │
                   │    │ id           │  │
                   │    │ name         │  │
                   │    │ model_path   │  │
                   │    │ model_type   │  │
                   │    │ user_id      │──┤
                   │    │ created_at   │  │
                   │    └──────────────┘  │
                   │                      │
                   │    ┌──────────────┐  │
                   └────│    Task      │  │
                        ├──────────────┤  │
                        │ id           │  │
                        │ task_name    │  │
                        │ base_model_id│──┘
                        │ dataset_id   │──┘
                        │ status       │
                        │ progress     │
                        │ output_dir   │
                        │ config       │
                        │ user_id      │──┘
                        │ created_at   │
                        │ updated_at   │
                        └──────────────┘
```

### 4.2 主要表结构

#### users 表
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### datasets 表
```sql
CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    total_samples INTEGER DEFAULT 0,
    file_format VARCHAR(20),
    description TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### models 表
```sql
CREATE TABLE models (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    model_path VARCHAR(500) NOT NULL,
    model_type VARCHAR(50),
    description TEXT,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### tasks 表
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(255) NOT NULL,
    base_model_id INTEGER REFERENCES models(id),
    dataset_id INTEGER REFERENCES datasets(id),
    status VARCHAR(50) DEFAULT 'PENDING',
    progress FLOAT DEFAULT 0.0,
    output_dir VARCHAR(500),
    config JSONB,
    user_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## 5. 关键设计决策

### 5.1 为什么选择前后端分离？

**优点**:
- 前后端独立开发，并行迭代
- 前端可部署到 CDN，提高加载速度
- 后端可独立扩展和部署
- API 可被多端复用（Web/移动端/CLI）

**缺点**:
- 增加了部署复杂度
- 需要处理跨域问题

**结论**: 对于企业级应用，前后端分离的优势远大于缺点。

### 5.2 为什么使用 subprocess 而不是 Celery？

**对比**:

| 方案 | 优点 | 缺点 |
|-----|------|------|
| subprocess | 轻量、无额外依赖、易调试 | 功能简单、缺少任务队列 |
| Celery | 成熟、功能丰富、支持分布式 | 需要 Redis/RabbitMQ、配置复杂 |

**结论**: 当前规模下，subprocess 已满足需求。未来可平滑迁移到 Celery。

### 5.3 为什么使用 PostgreSQL 而不是 MongoDB？

**对比**:

| 特性 | PostgreSQL | MongoDB |
|-----|-----------|---------|
| 事务 | 强 ACID | 弱一致性 |
| JSON | 支持 JSONB | 原生支持 |
| 查询 | SQL 强大 | 文档查询 |
| 生态 | 成熟 | 新兴 |

**结论**: 需要强事务保证（任务状态一致性），PostgreSQL 更合适。

### 5.4 路径管理策略

**问题**: 相对路径在不同进程中解析不同

**解决方案**:
```python
# 统一使用绝对路径
PROJECT_ROOT = os.path.abspath(os.path.join(__file__, "../../.."))
UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
LORA_DIR = os.path.join(PROJECT_ROOT, "lora_adapters")

# 配置类集中管理
class Config:
    PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/app")
    UPLOAD_DIR = os.path.join(PROJECT_ROOT, "uploads")
```

## 6. 安全设计

### 6.1 认证授权
- JWT Token 认证
- Token 过期时间: 24 小时
- 密码使用 bcrypt 加密

### 6.2 输入验证
- Pydantic 自动验证
- 文件上传大小限制: 500MB
- 文件类型白名单

### 6.3 SQL 注入防护
- 使用 SQLAlchemy ORM
- 参数化查询

### 6.4 XSS 防护
- 前端使用 React（自动转义）
- Content-Security-Policy 头

## 7. 性能优化

### 7.1 数据库优化
```sql
-- 索引优化
CREATE INDEX idx_datasets_user_id ON datasets(user_id);
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);

-- 连接池
pool_size = 20
max_overflow = 10
pool_recycle = 3600
```

### 7.2 异步 I/O
```python
# 使用 asyncio 处理 I/O 密集操作
async def upload_file(file: UploadFile):
    async with aiofiles.open(path, 'wb') as f:
        await f.write(await file.read())
```

### 7.3 前端优化
- 代码分割（React.lazy）
- 路由懒加载
- 列表虚拟化（大数据量）
- 防抖/节流（搜索框）

## 8. 可扩展性设计

### 8.1 水平扩展
```
Nginx (负载均衡)
    ↓
Backend 1, Backend 2, Backend 3 (无状态)
    ↓
PostgreSQL (主从复制)
```

### 8.2 任务队列
```python
# 未来可升级到 Celery
@celery.task
def train_task(task_id):
    start_training(task_id)
```

### 8.3 对象存储
```python
# 未来可替换为 S3/OSS
class FileStorage:
    def upload(self, file):
        # 当前: 本地文件系统
        # 未来: S3/OSS
        pass
```

## 9. 监控与日志

### 9.1 日志系统
```python
# 分级日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### 9.2 监控指标
- API 请求量 (QPS)
- API 响应时间 (P50, P95, P99)
- 数据库连接数
- 训练任务成功率
- 系统资源使用率 (CPU, 内存, GPU)

## 10. 部署架构

### 10.1 开发环境
```
本地开发:
- 前端: npm run dev (http://localhost:5173)
- 后端: uvicorn main:app --reload (http://localhost:8000)
- 数据库: PostgreSQL (localhost:5432)
```

### 10.2 生产环境
```
Docker Compose:
- Nginx (80/443)
- Frontend (静态文件)
- Backend (Gunicorn + Uvicorn)
- PostgreSQL (持久化卷)
- Redis (可选，缓存)
```

## 11. 技术债务与未来改进

### 11.1 短期改进
- [ ] 增加单元测试覆盖率 (目标 80%)
- [ ] 实现 WebSocket 实时日志推送
- [ ] 增加训练结果评估模块

### 11.2 中期改进
- [ ] 升级到 Celery 任务队列
- [ ] 使用 S3/OSS 对象存储
- [ ] 实现分布式训练

### 11.3 长期改进
- [ ] 微服务架构拆分
- [ ] Kubernetes 容器编排
- [ ] 多租户支持

---

<div align="center">

**EasyTune-LLM 架构设计文档**

版本: 1.0  
最后更新: 2025-10-14

</div>

