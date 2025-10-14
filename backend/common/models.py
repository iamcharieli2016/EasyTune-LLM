"""
数据库模型定义
包含所有核心业务实体
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, JSON, Float, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

from backend.common.database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class TaskStatus(str, enum.Enum):
    """任务状态枚举"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskComplexity(str, enum.Enum):
    """任务复杂度枚举"""
    L1_BASIC = "l1_basic"          # 基础风格调整
    L2_DOMAIN = "l2_domain"        # 领域知识注入
    L3_COMPLEX = "l3_complex"      # 复杂指令重塑


class ModelType(str, enum.Enum):
    """模型类型枚举"""
    BASE = "base"                  # 基座模型
    FINETUNED = "finetuned"        # 微调后模型
    LORA_ADAPTER = "lora_adapter"  # LoRA适配器


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # 关系
    tasks = relationship("Task", back_populates="owner")
    models = relationship("Model", back_populates="owner")
    datasets = relationship("Dataset", back_populates="owner")


class Model(Base):
    """模型表"""
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(200))
    description = Column(Text)
    model_type = Column(SQLEnum(ModelType), default=ModelType.BASE)
    model_path = Column(String(500), nullable=False)  # 本地路径或HF Hub路径
    model_size = Column(String(50))  # 如 "7B", "13B"
    base_model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    
    # LoRA相关
    lora_rank = Column(Integer)
    lora_alpha = Column(Integer)
    lora_target_modules = Column(JSON)
    
    # 元数据
    parameters_count = Column(String(50))
    framework = Column(String(50), default="pytorch")
    quantization = Column(String(50))  # 如 "int4", "int8"
    is_public = Column(Boolean, default=False)
    download_count = Column(Integer, default=0)
    
    # 模型服务配置
    service_config = Column(JSON)  # 服务配置（下载源、服务类型、API配置等）
    service_status = Column(String(50))  # 服务状态：not_configured, downloading, ready, running, error
    service_endpoint = Column(String(500))  # 服务访问端点
    
    # 所有者和时间
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    owner = relationship("User", back_populates="models")
    base_model = relationship("Model", remote_side=[id])
    tasks = relationship("Task", back_populates="base_model")


class Dataset(Base):
    """数据集表"""
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    dataset_path = Column(String(500), nullable=False)
    dataset_type = Column(String(50))  # instruction, qa, text_generation
    file_format = Column(String(50))   # json, jsonl, csv
    total_samples = Column(Integer)
    train_samples = Column(Integer)
    eval_samples = Column(Integer)
    
    # 数据统计
    avg_input_length = Column(Float)
    avg_output_length = Column(Float)
    
    # 元数据
    is_validated = Column(Boolean, default=False)
    validation_errors = Column(JSON)
    
    # 所有者和时间
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    owner = relationship("User", back_populates="datasets")
    tasks = relationship("Task", back_populates="dataset")


class Task(Base):
    """训练任务表"""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.PENDING)
    
    # 意图驱动配置
    task_complexity = Column(SQLEnum(TaskComplexity), nullable=False)
    task_intent = Column(Text)  # 用户描述的训练意图
    
    # 模型和数据配置
    base_model_id = Column(Integer, ForeignKey("models.id"))
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    output_model_name = Column(String(200))
    
    # 训练配置（自动生成）
    training_config = Column(JSON)  # 包含所有LoRA参数
    
    # 训练参数
    lora_rank = Column(Integer)
    lora_alpha = Column(Integer)
    learning_rate = Column(Float)
    num_epochs = Column(Integer)
    batch_size = Column(Integer)
    max_length = Column(Integer)
    
    # 训练进度和指标
    current_epoch = Column(Integer, default=0)
    current_step = Column(Integer, default=0)
    total_steps = Column(Integer)
    train_loss = Column(Float)
    eval_loss = Column(Float)
    cf_score = Column(Float)  # 灾难性遗忘分数
    
    # 资源使用
    gpu_memory_used = Column(Float)
    estimated_time = Column(Integer)  # 预计剩余时间（秒）
    
    # 结果
    output_model_path = Column(String(500))
    metrics = Column(JSON)  # 最终评估指标
    error_message = Column(Text)
    
    # 所有者和时间
    owner_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 关系
    owner = relationship("User", back_populates="tasks")
    base_model = relationship("Model", back_populates="tasks")
    dataset = relationship("Dataset", back_populates="tasks")
    logs = relationship("TaskLog", back_populates="task", cascade="all, delete-orphan")


class TaskLog(Base):
    """任务日志表"""
    __tablename__ = "task_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    log_level = Column(String(20))  # INFO, WARNING, ERROR
    message = Column(Text)
    details = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    task = relationship("Task", back_populates="logs")


class Role(Base):
    """角色表"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    permissions = Column(JSON)  # 权限列表
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Permission(Base):
    """权限表"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50))  # model, task, dataset, user
    action = Column(String(50))    # create, read, update, delete
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

