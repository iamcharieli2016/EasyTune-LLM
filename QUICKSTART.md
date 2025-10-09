# 🚀 EasyTune-LLM 快速开始指南

## 5分钟启动平台

### 前置条件检查

```bash
# 检查Docker版本
docker --version  # 需要 20.10+

# 检查Docker Compose版本
docker-compose --version  # 需要 2.0+

# 检查GPU（可选，训练时需要）
nvidia-smi
```

### 一键启动

```bash
# 1. 克隆项目
git clone https://github.com/your-org/EasyTune-LLM.git
cd EasyTune-LLM

# 2. 启动所有服务
chmod +x deployment/scripts/start.sh
./deployment/scripts/start.sh

# 等待约1分钟，服务启动完成
```

### 访问平台

打开浏览器，访问：

- **前端界面**: http://localhost:3000
- **API文档**: http://localhost:8000/docs

默认账号：
- 用户名: `admin`
- 密码: `admin123`

## 🎯 第一次使用

### 步骤1: 上传数据集

1. 登录后，点击左侧 **"数据集"** 菜单
2. 点击 **"上传数据集"** 按钮
3. 选择您的训练数据文件（支持JSON、JSONL、CSV）
4. 填写数据集名称和描述
5. 点击确认上传

**数据格式示例** (JSON):
```json
[
  {
    "instruction": "解释什么是机器学习",
    "input": "",
    "output": "机器学习是人工智能的一个分支..."
  },
  {
    "instruction": "将以下文本翻译成英文",
    "input": "你好，世界",
    "output": "Hello, World"
  }
]
```

### 步骤2: 添加基座模型

1. 点击左侧 **"模型管理"** 菜单
2. 点击 **"添加模型"** 按钮
3. 填写模型信息：
   - 模型名称
   - 模型路径（HuggingFace模型ID 或 本地路径）
   - 模型大小（如 7B、13B）
4. 点击确认添加

**示例模型**:
- `meta-llama/Llama-2-7b-hf`
- `THUDM/chatglm3-6b`
- `Qwen/Qwen-7B`

### 步骤3: 创建训练任务

1. 点击左侧 **"训练任务"** 菜单
2. 点击右上角 **"创建任务"** 按钮
3. 按照四步向导配置：

**第一步 - 选择模型和数据**:
- 任务名称: `my-first-task`
- 基座模型: 选择刚才添加的模型
- 训练数据集: 选择上传的数据集

**第二步 - 意图驱动配置**:
- 训练意图描述: "我希望模型能够回答医疗领域的专业问题"
- 任务复杂度: 选择 **L2 - 领域知识注入**

**第三步 - 高级设置**:
- 输出模型名称: `my-medical-model`
- 训练轮数: 3（推荐）

**第四步 - 确认创建**:
- 检查配置无误
- 点击 **"开始训练"** 按钮

### 步骤4: 监控训练

任务创建后，会自动跳转到任务详情页面：

- 实时查看训练进度
- 监控 Loss 曲线
- 查看灾难性遗忘分数 (CF Score)
- 查看GPU使用情况

训练完成后：
- 下载微调后的模型
- 查看评估指标
- 部署模型进行推理

## 🎮 常用操作

### 查看服务状态

```bash
docker-compose ps
```

### 查看实时日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api-gateway
docker-compose logs -f training-engine
```

### 停止服务

```bash
docker-compose down
```

### 重启服务

```bash
docker-compose restart
```

### 清理数据

```bash
# 停止并删除所有容器、网络、卷
docker-compose down -v

# 清理临时文件
make clean
```

## 📊 项目结构速览

```
EasyTune-LLM/
├── backend/              # 后端服务
│   ├── api-gateway/     # API网关
│   ├── common/          # 公共模块（数据库、认证）
│   └── requirements.txt
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── pages/       # 页面组件
│   │   ├── components/  # 公共组件
│   │   ├── services/    # API服务
│   │   └── types/       # 类型定义
│   └── package.json
├── training-engine/     # 训练引擎
│   ├── src/trainer.py   # 核心训练逻辑
│   └── requirements.txt
├── deployment/          # 部署配置
│   ├── docker/          # Docker配置
│   └── scripts/         # 部署脚本
├── docs/                # 文档
└── docker-compose.yml   # 服务编排
```

## 🔧 故障排查

### 问题1: 端口被占用

```bash
# 查找占用端口的进程
sudo lsof -i :8000
sudo lsof -i :3000

# 杀死进程或修改配置使用其他端口
```

### 问题2: Docker镜像拉取失败

```bash
# 手动拉取镜像
docker pull postgres:15-alpine
docker pull redis:7-alpine

# 或配置Docker镜像加速器
```

### 问题3: 数据库连接失败

```bash
# 检查PostgreSQL状态
docker-compose logs postgres

# 重新初始化数据库
docker-compose exec api-gateway python deployment/scripts/init_db.py
```

### 问题4: GPU不可用

```bash
# 检查NVIDIA Docker支持
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# 如果失败，安装nvidia-docker2
# Ubuntu
sudo apt-get install nvidia-docker2
sudo systemctl restart docker
```

## 📚 更多资源

- **完整文档**: [docs/README.md](docs/README.md)
- **架构设计**: [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md)
- **部署指南**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **API文档**: http://localhost:8000/docs (启动后访问)

## 🎓 视频教程

_(待添加)_

1. 5分钟快速入门
2. 创建第一个训练任务
3. 理解意图驱动配置
4. 监控和优化训练
5. 模型导出和部署

## 💬 获取帮助

遇到问题？

1. 查看 [故障排查章节](#故障排查)
2. 搜索 [GitHub Issues](https://github.com/your-org/EasyTune-LLM/issues)
3. 加入 [Discord社区](https://discord.gg/easytune-llm)
4. 发送邮件到 support@easytune-llm.com

## ⭐ 下一步

- 尝试不同的任务复杂度配置
- 探索高级训练参数
- 了解灾难性遗忘监控
- 学习模型导出和量化
- 部署模型到生产环境

---

**祝您使用愉快！** 🎉

