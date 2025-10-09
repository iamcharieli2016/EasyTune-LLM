# EasyTune-LLM 架构设计文档

## 📐 系统架构概览

EasyTune-LLM 采用现代化的微服务架构，将系统划分为多个独立的服务模块，确保高可用性、可扩展性和易维护性。

## 🏗️ 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        客户端层 (Client Layer)                   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Web UI     │  │  Mobile App  │  │   CLI Tool   │         │
│  │  (React)     │  │   (Future)   │  │   (Future)   │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      API网关层 (API Gateway)                     │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  • 路由转发    • 负载均衡    • 限流控制                │    │
│  │  • JWT认证     • RBAC权限    • 日志审计                │    │
│  │  • 熔断降级    • 监控统计    • 安全防护                │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      业务服务层 (Service Layer)                  │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│  │  模型管理服务  │  │  任务调度服务  │  │  认证授权服务  │      │
│  │    (MMS)      │  │    (TSS)      │  │   (AUTH)      │      │
│  │               │  │               │  │               │      │
│  │ • 模型存储    │  │ • 任务队列    │  │ • 用户管理    │      │
│  │ • 版本控制    │  │ • 状态追踪    │  │ • 权限控制    │      │
│  │ • 元数据管理  │  │ • 资源调度    │  │ • Token管理   │      │
│  └───────────────┘  └───────────────┘  └───────────────┘      │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐                          │
│  │  数据集服务    │  │  监控告警服务  │                          │
│  │    (DMS)      │  │   (MONITOR)   │                          │
│  └───────────────┘  └───────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      训练引擎层 (Training Engine)                │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │            PEFT/LoRA 训练引擎                          │    │
│  │  • PyTorch + Transformers + PEFT                      │    │
│  │  • 自动配置LoRA参数                                    │    │
│  │  • 灾难性遗忘监控 (CF Score)                           │    │
│  │  • 分布式训练支持 (Accelerate/DeepSpeed)               │    │
│  │  • 混合精度训练                                        │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      数据存储层 (Data Layer)                     │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│  │  PostgreSQL   │  │     Redis     │  │  File System  │      │
│  │  (关系数据)    │  │   (缓存队列)   │  │  (模型文件)    │      │
│  └───────────────┘  └───────────────┘  └───────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

## 🔧 核心组件详解

### 1. API网关服务 (API Gateway)

**职责**：
- 统一入口，路由转发到各微服务
- JWT Token验证和刷新
- 基于RBAC的权限控制
- 请求限流和熔断
- 日志记录和审计
- 跨域处理 (CORS)

**技术栈**：
- FastAPI 0.100+
- SlowAPI (限流)
- Python-Jose (JWT)
- HTTPX (异步HTTP客户端)

**关键设计**：
```python
# 中间件架构
Request → CORS → RateLimit → Auth → Route → Service
```

### 2. 模型管理服务 (Model Management Service)

**职责**：
- 管理基座模型和微调后的模型
- LoRA适配器的版本控制
- 模型元数据存储
- 模型下载和上传
- 模型权限管理

**数据模型**：
```python
Model {
    id, name, type, path,
    lora_rank, lora_alpha, target_modules,
    is_public, owner_id
}
```

### 3. 任务调度服务 (Task Scheduling Service)

**职责**：
- 接收训练任务请求
- 意图驱动的参数自动配置
- 任务队列管理 (Celery)
- 训练状态追踪
- 资源调度和负载均衡

**任务生命周期**：
```
创建 → 排队 → 运行中 → 完成/失败
```

**核心算法**：意图驱动配置引擎
```python
def configure_lora_params(complexity: TaskComplexity) -> LoRAConfig:
    """根据任务复杂度自动配置LoRA参数"""
    config_map = {
        "L1_BASIC": {rank: 8, alpha: 16, modules: ["q_proj", "k_proj", "v_proj"]},
        "L2_DOMAIN": {rank: 16, alpha: 32, modules: ["q_proj", ..., "ffn"]},
        "L3_COMPLEX": {rank: 32, alpha: 64, modules: ["all"]}
    }
    return config_map[complexity]
```

### 4. 训练引擎服务 (Training Engine)

**职责**：
- 执行实际的模型微调
- PEFT/LoRA集成
- 实时训练指标上报
- 灾难性遗忘监控
- 模型合并和导出

**训练流程**：
```
1. 加载基座模型和分词器
2. 应用LoRA配置
3. 加载和预处理数据集
4. 创建Trainer并开始训练
5. 实时上报指标 (loss, CF Score, GPU使用率)
6. 保存LoRA适配器
7. (可选) 合并为完整模型
```

**关键优化**：
- 混合精度训练 (FP16/BF16)
- 梯度累积
- 梯度检查点
- 分布式训练 (Accelerate)

### 5. 认证授权服务 (Authentication Service)

**职责**：
- 用户注册和登录
- JWT Token签发和验证
- 权限管理 (RBAC)
- 会话管理

**安全机制**：
- 密码加密 (Bcrypt)
- Token双层验证 (Access + Refresh)
- 角色权限分离
- 操作审计日志

## 📊 数据库设计

### ER图概览

```
┌──────────┐       ┌──────────┐       ┌──────────┐
│  User    │──────▶│   Task   │──────▶│  Model   │
└──────────┘       └──────────┘       └──────────┘
     │                   │
     │                   ▼
     │             ┌──────────┐
     └────────────▶│ Dataset  │
                   └──────────┘
```

### 核心表结构

**users 表**：
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**tasks 表**：
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    task_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    task_complexity VARCHAR(20) NOT NULL,
    base_model_id INTEGER REFERENCES models(id),
    dataset_id INTEGER REFERENCES datasets(id),
    lora_rank INTEGER,
    lora_alpha INTEGER,
    learning_rate FLOAT,
    owner_id INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🚀 技术栈总览

### 后端
| 组件 | 技术 | 版本 |
|------|------|------|
| Web框架 | FastAPI | 0.100+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据库 | PostgreSQL | 15+ |
| 缓存 | Redis | 7.0+ |
| 任务队列 | Celery | 5.3+ |
| 认证 | JWT + Bcrypt | - |

### 训练引擎
| 组件 | 技术 | 版本 |
|------|------|------|
| 深度学习 | PyTorch | 2.0+ |
| 模型库 | Transformers | 4.35+ |
| PEFT | Hugging Face PEFT | 0.7+ |
| 加速 | Accelerate | 0.24+ |
| 量化 | BitsAndBytes | 0.41+ |

### 前端
| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | React | 18+ |
| 语言 | TypeScript | 5+ |
| UI库 | Ant Design | 5.0+ |
| 状态管理 | Redux Toolkit | 1.9+ |
| 图表 | ECharts | 5.0+ |
| HTTP | Axios | 1.6+ |

### DevOps
| 组件 | 技术 |
|------|------|
| 容器化 | Docker |
| 编排 | Docker Compose / K8s |
| CI/CD | GitHub Actions |
| 监控 | Prometheus + Grafana |
| 日志 | ELK Stack |

## 🔐 安全架构

### 1. 认证机制
- **JWT双Token设计**：Access Token (30分钟) + Refresh Token (7天)
- **密码策略**：Bcrypt加密，最少8位
- **会话管理**：支持多设备登录，可强制下线

### 2. 权限控制 (RBAC)
```
Admin → 所有权限
  ├─ User → 创建、查看、更新
  │   └─ Viewer → 仅查看
```

### 3. 数据安全
- 传输加密：TLS/SSL
- 数据隔离：用户只能访问自己的资源
- SQL注入防护：参数化查询
- XSS防护：输入验证和输出转义

### 4. PEFT安全威胁应对
- **PaaA攻击防护**：Post-PEFT Safety Alignment (PPSA)
- **模型审计**：上传和训练完成的LoRA权重检查
- **安全测试集**：验证模型是否维持安全对齐

## 📈 性能优化

### 1. 后端优化
- **连接池**：数据库连接池 (pool_size=10)
- **缓存策略**：Redis缓存热点数据
- **异步处理**：FastAPI异步路由
- **负载均衡**：多Worker进程

### 2. 训练优化
- **混合精度**：FP16/BF16训练，显存占用降低50%
- **梯度累积**：模拟大batch_size
- **梯度检查点**：降低70%显存占用
- **LoRA优势**：参数量减少90%，训练速度提升3-5倍

### 3. 前端优化
- **代码分割**：React.lazy动态导入
- **图片优化**：WebP格式，懒加载
- **缓存策略**：静态资源CDN + 强缓存
- **构建优化**：Tree Shaking，压缩混淆

## 🔄 可扩展性设计

### 1. 水平扩展
- API网关：无状态设计，可任意扩展
- 训练引擎：支持多GPU卡、多节点训练
- 数据库：主从复制，读写分离

### 2. 垂直扩展
- 支持GPU资源动态分配
- 支持更大模型和数据集
- 支持更多并发训练任务

### 3. 功能扩展
- 插件化架构，易于添加新功能
- 支持自定义训练策略
- 支持多种PEFT方法 (AdaLoRA, QLoRA等)

## 📝 部署架构

### Docker Compose部署 (推荐快速开始)
```yaml
services:
  - postgres (数据库)
  - redis (缓存)
  - api-gateway (API网关)
  - training-engine (训练引擎)
  - frontend (前端)
```

### Kubernetes部署 (生产环境)
```yaml
- Deployment: 各微服务
- Service: 服务发现
- Ingress: 流量入口
- PV/PVC: 持久化存储
- ConfigMap/Secret: 配置管理
```

## 🎯 设计原则

1. **高内聚，低耦合**：微服务独立部署
2. **关注点分离**：业务逻辑与基础设施分离
3. **容错性设计**：服务降级、熔断、重试
4. **可观测性**：日志、监控、链路追踪
5. **安全第一**：多层防护，最小权限原则
6. **用户体验**：意图驱动，简化复杂度

---

**文档版本**: v1.0  
**最后更新**: 2024-12-10  
**维护者**: EasyTune-LLM Team

