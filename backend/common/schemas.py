"""
Pydantic Schema定义
用于API请求/响应的数据验证
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ==================== 枚举类型 ====================

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskComplexity(str, Enum):
    L1_BASIC = "l1_basic"
    L2_DOMAIN = "l2_domain"
    L3_COMPLEX = "l3_complex"


class ModelType(str, Enum):
    BASE = "base"
    FINETUNED = "finetuned"
    LORA_ADAPTER = "lora_adapter"


# ==================== 用户相关 ====================

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==================== 认证相关 ====================

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# ==================== 模型相关 ====================

class ModelBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = None
    description: Optional[str] = None
    model_type: ModelType = ModelType.BASE


class ModelCreate(ModelBase):
    model_path: str
    model_size: Optional[str] = None
    base_model_id: Optional[int] = None


class ModelUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class ModelResponse(ModelBase):
    id: int
    model_path: str
    model_size: Optional[str] = None
    parameters_count: Optional[str] = None
    framework: str
    is_public: bool
    download_count: int
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 数据集相关 ====================

class DatasetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    dataset_type: str = Field(..., description="instruction, qa, text_generation")


class DatasetCreate(DatasetBase):
    pass


class DatasetResponse(DatasetBase):
    id: int
    dataset_path: str
    file_format: str
    total_samples: Optional[int] = None
    train_samples: Optional[int] = None
    eval_samples: Optional[int] = None
    is_validated: bool
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 任务相关 ====================

class TaskCreate(BaseModel):
    task_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    task_complexity: TaskComplexity
    task_intent: Optional[str] = Field(None, description="用户描述的训练意图")
    base_model_id: int
    dataset_id: int
    output_model_name: str
    
    # 可选的高级配置
    num_epochs: Optional[int] = Field(3, ge=1, le=100)
    batch_size: Optional[int] = Field(None, ge=1, le=128)
    max_length: Optional[int] = Field(512, ge=128, le=4096)


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None


class TaskResponse(BaseModel):
    id: int
    task_name: str
    description: Optional[str] = None
    status: TaskStatus
    task_complexity: TaskComplexity
    task_intent: Optional[str] = None
    
    # 配置信息
    lora_rank: Optional[int] = None
    lora_alpha: Optional[int] = None
    learning_rate: Optional[float] = None
    num_epochs: Optional[int] = None
    
    # 进度信息
    current_epoch: Optional[int] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    train_loss: Optional[float] = None
    eval_loss: Optional[float] = None
    cf_score: Optional[float] = None
    
    # 资源使用
    gpu_memory_used: Optional[float] = None
    estimated_time: Optional[int] = None
    
    # 结果
    output_model_path: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # 关联信息
    owner_id: int
    base_model_id: int
    dataset_id: int
    
    # 时间信息
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskMetrics(BaseModel):
    """训练指标"""
    epoch: int
    step: int
    train_loss: float
    eval_loss: Optional[float] = None
    learning_rate: float
    cf_score: Optional[float] = None
    gpu_memory: Optional[float] = None
    timestamp: datetime


# ==================== 通用响应 ====================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool
    message: str
    data: Optional[Any] = None


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    total: int
    page: int
    page_size: int
    items: List[Any]


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# ==================== 统计信息 ====================

class DashboardStats(BaseModel):
    """仪表板统计信息"""
    total_tasks: int
    running_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_models: int
    total_datasets: int
    total_users: int
    gpu_usage: Optional[float] = None


class SystemHealth(BaseModel):
    """系统健康状态"""
    status: str  # healthy, degraded, down
    database: bool
    redis: bool
    gpu_available: bool
    disk_usage: float
    memory_usage: float
    cpu_usage: float

