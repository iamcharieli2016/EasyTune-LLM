# EasyTune-LLM: 意图驱动的傻瓜式大模型微调平台

<div align="center">

![EasyTune-LLM](docs/assets/logo.png)

**企业级大模型微调平台 | 轻量 · 安全 · 易用**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18.0+-blue.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)](https://fastapi.tiangolo.com)

</div>

## 📋 项目简介

EasyTune-LLM 是一个企业级的大模型微调平台，致力于通过**意图驱动**的设计理念，将复杂的大模型微调过程简化为傻瓜式的四步操作。平台基于 PEFT（参数高效微调）技术，支持 LoRA、QLoRA 等先进方法，为企业和个人开发者提供轻量、安全、高性能的模型微调解决方案。

### 🎯 核心特性

- **🚀 极致简化**：意图驱动配置，无需深入理解复杂超参数
- **⚡ 轻量高效**：基于 LoRA/QLoRA 技术，显存占用降低 90%
- **🔒 安全私有**：支持私有化部署，完整的 RBAC 权限体系
- **📊 实时监控**：可视化训练过程，灾难性遗忘智能预警
- **🐳 容器化**：完整 Docker/Kubernetes 支持，一键部署
- **🔄 高移植性**：支持多种硬件平台，OpenVINO 优化导出

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                     前端 (React + TS)                    │
│              现代化UI · 实时监控 · 可视化配置            │
└─────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────┐
│              API Gateway (安全网关服务)                  │
│          JWT认证 · RBAC · 限流 · 路由转发               │
└─────────────────────────────────────────────────────────┘
           ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ 模型管理服务 │ │ 任务调度服务 │ │ 认证授权服务 │
│   (MMS)      │ │   (TSS)      │ │   (AUTH)     │
└──────────────┘ └──────────────┘ └──────────────┘
                     ↓
           ┌──────────────────┐
           │   训练引擎服务    │
           │  PEFT/LoRA 训练  │
           └──────────────────┘
                     ↓
           ┌──────────────────┐
           │   数据存储层      │
           │ PostgreSQL+Redis │
           └──────────────────┘
```

## 🚦 快速开始

### 前置要求

- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.10+
- **Node.js**: 18.0+
- **CUDA**: 11.8+ (GPU训练)

### 一键部署（推荐）

```bash
# 克隆项目
git clone https://github.com/your-org/EasyTune-LLM.git
cd EasyTune-LLM

# 启动所有服务
docker-compose up -d

# 访问平台
# 前端: http://localhost:3000
# API文档: http://localhost:8000/docs
```

### 开发环境部署

#### 1. 后端服务

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动各个微服务
cd api-gateway && uvicorn main:app --reload --port 8000
cd model-service && uvicorn main:app --reload --port 8001
cd task-service && uvicorn main:app --reload --port 8002
```

#### 2. 前端服务

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm start
```

#### 3. 训练引擎

```bash
cd training-engine

# 安装训练依赖
pip install -r requirements.txt

# 启动训练服务
python src/trainer_service.py
```

## 📖 使用指南

### 四步完成模型微调

#### 步骤 1: 选择基座模型与数据

- 支持从 HuggingFace Hub、本地路径导入模型
- 拖拽式数据上传，自动格式校验
- 支持 JSON、JSONL、CSV 等多种数据格式

#### 步骤 2: 意图驱动配置

选择您的训练意图：

| 意图等级 | 适用场景 | 自动配置 |
|---------|---------|---------|
| **L1 - 基础风格调整** | 改变语气、格式 | Rank=4-8, QKV层 |
| **L2 - 领域知识注入** | 垂直领域适配 | Rank=8-16, QKV+FFN |
| **L3 - 复杂指令重塑** | 代码生成、复杂推理 | Rank=16-32, 全层 |

#### 步骤 3: 实时监控

- **训练进度**：实时loss曲线、GPU使用率
- **灾难性遗忘监控**：CF Score 实时追踪
- **智能预警**：过拟合、知识遗忘自动提示

#### 步骤 4: 导出与部署

- **标准导出**：PyTorch、ONNX 格式
- **优化导出**：INT4/INT8 量化，OpenVINO 格式
- **一键部署**：生成推理服务配置

## 🔧 技术栈

### 后端

- **Web框架**: FastAPI 0.100+
- **ORM**: SQLAlchemy 2.0
- **任务队列**: Celery + Redis
- **数据库**: PostgreSQL 15
- **缓存**: Redis 7.0

### 前端

- **框架**: React 18 + TypeScript 5
- **UI组件**: Ant Design 5.0
- **状态管理**: Redux Toolkit
- **图表**: ECharts 5.0
- **HTTP客户端**: Axios

### 训练引擎

- **深度学习**: PyTorch 2.0+
- **PEFT**: Hugging Face PEFT
- **分布式**: Accelerate
- **优化**: DeepSpeed (可选)

### DevOps

- **容器化**: Docker + Docker Compose
- **编排**: Kubernetes (生产环境)
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana

## 📂 项目结构

```
EasyTune-LLM/
├── backend/                    # 后端服务
│   ├── api-gateway/           # API网关服务
│   ├── model-service/         # 模型管理服务
│   ├── task-service/          # 任务调度服务
│   ├── auth-service/          # 认证授权服务
│   └── common/                # 公共模块
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # React组件
│   │   ├── pages/             # 页面
│   │   ├── services/          # API服务
│   │   └── styles/            # 样式
│   └── public/
├── training-engine/            # 训练引擎
│   ├── src/                   # 训练核心代码
│   ├── models/                # 模型配置
│   └── configs/               # 训练配置
├── deployment/                 # 部署配置
│   ├── docker/                # Docker配置
│   ├── kubernetes/            # K8s配置
│   └── scripts/               # 部署脚本
├── docs/                       # 文档
│   ├── architecture/          # 架构设计
│   ├── api/                   # API文档
│   └── user-guide/            # 用户指南
└── docker-compose.yml         # Docker编排
```

## 🔐 安全特性

- **认证机制**: JWT Token + Refresh Token
- **权限控制**: 细粒度 RBAC 权限体系
- **数据加密**: TLS/SSL 传输加密
- **安全审计**: 完整的操作日志
- **PaaA防护**: Post-PEFT Safety Alignment

## 📊 性能指标

- **显存占用**: 相比全量微调降低 90%
- **训练速度**: 提升 3-5倍
- **模型体积**: LoRA 权重仅 10-50MB
- **并发能力**: 支持 100+ 并发训练任务

## 🛣️ 发展路线图

### v1.0 (当前版本)
- ✅ 基础微调功能
- ✅ LoRA/QLoRA 支持
- ✅ Web UI 界面
- ✅ Docker 部署

### v1.5 (计划中)
- 🔄 AdaLoRA 动态秩调整
- 🔄 多模型对比训练
- 🔄 联邦学习支持
- 🔄 强化学习 RLHF

### v2.0 (规划中)
- 📋 多模态模型支持
- 📋 AutoML 超参数优化
- 📋 模型商店
- 📋 云原生部署

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 参与方式

- 🐛 提交 Bug 报告
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码 PR

## 📄 开源协议

本项目采用 [Apache 2.0](LICENSE) 开源协议。

## 📞 联系我们

- **官网**: https://easytune-llm.com
- **邮箱**: support@easytune-llm.com
- **Discord**: https://discord.gg/easytune-llm
- **微信群**: 扫码加入技术交流群

## 🌟 致谢

感谢以下开源项目和社区的支持：

- [Hugging Face PEFT](https://github.com/huggingface/peft)
- [PyTorch](https://pytorch.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Ant Design](https://ant.design/)

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-org/EasyTune-LLM&type=Date)](https://star-history.com/#your-org/EasyTune-LLM&Date)

---

<div align="center">
Made with ❤️ by EasyTune-LLM Team
</div>

