# EasyTune-LLM

<div align="center">

**企业级大语言模型微调平台**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)](https://fastapi.tiangolo.com/)

零代码微调 | 可视化界面 | 企业级稳定

[快速开始](#-快速开始) • [功能特性](#-功能特性) • [技术架构](#-技术架构) • [文档](#-文档)

</div>

---

## 项目简介

EasyTune-LLM 是一个专业的大语言模型微调平台，旨在**降低 LLM 微调的技术门槛**，通过 Web 界面实现零代码微调，将传统微调流程从 2 天缩短到 2 小时。

### 核心特性

- **零代码操作** - 可视化 Web 界面，无需编写代码
- **高效微调** - 支持 LoRA/QLoRA，显存占用小，训练速度快
- **实时监控** - 训练进度、日志实时查看，全流程可控
- **灵活配置** - 智能参数推荐，支持多种训练方式
- **生产就绪** - 进程隔离、异步I/O、完善的监控告警

---

## ✨ 功能特性

| 模块 | 功能 | 状态 |
|-----|------|-----|
| **仪表盘** | 统计概览、快捷操作、系统监控 | ✅ |
| **数据集管理** | 上传/预览/删除，支持多种格式 | ✅ |
| **模型管理** | 预置模型库、自定义路径、模型服务 | ✅ |
| **训练任务** | 创建/监控/停止/删除任务 | ✅ |
| **日志监控** | 实时日志、下载、搜索 | ✅ |

### 界面预览

```
┌─────────────────────────────────────────────────────┐
│  EasyTune-LLM                    [用户] [设置] [退出]│
├──────────┬──────────────────────────────────────────┤
│ 仪表盘   │  统计概览                              │
│ 数据集   │  ├─ 数据集: 5 个                          │
│ 模型     │  ├─ 模型: 3 个                            │
│ 训练任务 │  └─ 任务: 12 个 (2 个运行中)             │
│ 日志     │                                          │
│          │  快捷操作                              │
│          │  [创建任务] [上传数据] [添加模型]        │
│          │                                          │
│          │  最近任务                              │
│          │  ├─ 客服机器人微调 (运行中) ██████░░ 75% │
│          │  ├─ 问答模型训练 (已完成) ✓              │
│          │  └─ 分类任务 (失败) ✗                    │
└──────────┴──────────────────────────────────────────┘
```

---

## 快速开始

### 前置要求

```bash
# 硬件要求
CPU: 4+ 核心
内存: 16GB+
显卡: NVIDIA GPU (8GB+) 或 Apple Silicon
磁盘: 50GB+ 可用空间

# 软件要求
Python 3.9+
Node.js 16+
PostgreSQL 14+
CUDA 11.8+ (NVIDIA) 或 macOS 13+ (Apple)
```

### 一键安装

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/EasyTune-LLM.git
cd EasyTune-LLM

# 2. 安装后端
conda create -n easytune python=3.10
conda activate easytune
pip install -r backend/requirements.txt
pip install -r training-engine/requirements.txt

# 3. 配置数据库
createdb easytune_db
cd backend && alembic upgrade head

# 4. 启动后端
./start_backend_fixed.sh
# 后端运行在: http://localhost:8000

# 5. 安装并启动前端
cd frontend
npm install
npm run dev
# 前端运行在: http://localhost:5173
```

### 首次使用

```bash
1. 访问 http://localhost:5173
2. 登录 (默认: admin / admin123)
3. 上传训练数据集
4. 添加基座模型
5. 创建训练任务
6. 监控训练进度
```

---

## 文档

### 核心文档

| 文档 | 说明 |
|-----|------|
| [平台功能介绍](./平台功能介绍.md) | 完整的功能说明和使用指南 |
| [系统架构设计](./ARCHITECTURE.md) | 技术架构和设计决策 |
| [本地环境安装](./INSTALLATION.md) | 开发环境配置和安装步骤 |
| [生产环境部署](./DEPLOYMENT.md) | Docker 部署和生产配置 |

### 快速链接

-  [快速开始](#-快速开始) - 5 分钟快速体验
-  [技术架构](#-技术架构) - 了解系统设计
-  [性能数据](#-性能数据) - 查看性能指标
-  [贡献指南](#-贡献) - 参与项目开发

---

##  技术栈

### 前端
```
React 18 + TypeScript
Ant Design 5.x
React Router v6
Axios
Vite
```

### 后端
```
FastAPI
PostgreSQL + SQLAlchemy
asyncio + asyncpg
psutil (进程管理)
```

### 训练引擎
```
PyTorch 2.0+
HuggingFace Transformers
PEFT (LoRA, QLoRA)
支持 CUDA / MPS / CPU
```

---

##  使用场景

###  客服机器人
```python
# 适用于: 企业客服、售后支持
- 数据: 客服对话历史
- 模型: Qwen2-7B
- 方式: LoRA 微调
- 时间: 2-4 小时
```

###  专业问答
```python
# 适用于: 医疗、法律、金融等垂直领域
- 数据: 专业知识库
- 模型: ChatGLM3-6B
- 方式: 全量微调
- 时间: 4-8 小时
```

###  文本分类
```python
# 适用于: 情感分析、意图识别
- 数据: 标注文本
- 模型: Qwen2-1.5B
- 方式: LoRA 微调
- 时间: 1-2 小时
```

###  多语言翻译
```python
# 适用于: 文档翻译、实时翻译
- 数据: 平行语料
- 模型: LLaMA-3-8B
- 方式: Seq2Seq 微调
- 时间: 6-10 小时
```

---

##  性能基准

### 训练性能

| 模型 | 数据量 | 硬件 | 时间 | 显存 |
|-----|--------|------|-----|------|
| Qwen2-1.5B | 10K | RTX 3090 | 1h | 8GB |
| Qwen2-7B | 10K | RTX 4090 | 4h | 20GB |
| LLaMA-13B | 10K | A100 40GB | 6h | 35GB |
| Qwen2-7B (LoRA) | 10K | RTX 3090 | 1.5h | 8GB |

### 推理性能

| 模型 | 硬件 | 吞吐量 | 延迟 |
|-----|------|-------|------|
| 1.5B | RTX 3090 | 2000 tok/s | 50ms |
| 7B | RTX 4090 | 800 tok/s | 120ms |
| 13B | A100 | 500 tok/s | 200ms |

---

##  高级功能

### 分布式训练
```yaml
training:
  distributed:
    enabled: true
    num_gpus: 4
```

### 模型量化
```yaml
quantization:
  enabled: true
  bits: 4  # 4-bit QLoRA
```

### 梯度检查点
```yaml
gradient_checkpointing:
  enabled: true  # 节省显存
```

---

##  贡献

我们欢迎所有形式的贡献！

### 贡献方式
-  提交 Bug 报告
-  提出新功能建议
-  改进文档
-  提交代码

### 贡献流程
```bash
1. Fork 项目
2. 创建特性分支 (git checkout -b feature/AmazingFeature)
3. 提交更改 (git commit -m 'Add AmazingFeature')
4. 推送分支 (git push origin feature/AmazingFeature)
5. 提交 Pull Request
```

---

##  更新日志

### v1.0.0 (2025-10-14)
-  完成数据集管理功能
-  完成模型管理功能
-  完成训练任务创建和监控
-  完成日志实时查看
-  添加任务停止和删除功能
-  修复路径问题，支持绝对路径
-  优化错误处理和用户体验

### v0.9.0 (2025-10-10)
-  初始版本发布
- 基础功能实现

---

##  许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

##  致谢

感谢以下开源项目:

- [HuggingFace Transformers](https://github.com/huggingface/transformers) - 模型库
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架
- [Ant Design](https://ant.design/) - UI 组件
- [PyTorch](https://pytorch.org/) - 深度学习框架
- [PEFT](https://github.com/huggingface/peft) - 高效微调

---

##  联系我们

- 主页: [https://github.com/iamcharieli2016/EasyTune-LLM](https://github.com/your-repo/EasyTune-LLM)
- 问题: [Issues](https://github.com/iamcharieli2016/EasyTune-LLM/EasyTune-LLM/issues)
- 邮箱: 574485592@qq.com

---

<div align="center">

**如果这个项目对您有帮助，请给我们一个 Star！**

Made with by EasyTune-LLM Team

</div>
