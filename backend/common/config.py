"""
配置管理模块
统一管理所有服务的配置
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "EasyTune-LLM"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://easytune:easytune@localhost:5432/easytune_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    
    # Redis配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # JWT认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # 文件上传配置
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 1024 * 1024 * 1024  # 1GB
    ALLOWED_EXTENSIONS: List[str] = ["json", "jsonl", "csv", "txt"]
    
    # 模型配置
    MODELS_DIR: str = "./models"
    LORA_ADAPTERS_DIR: str = "./lora_adapters"
    CACHE_DIR: str = "./cache"
    
    # 训练配置
    MAX_CONCURRENT_TASKS: int = 5
    DEFAULT_BATCH_SIZE: int = 4
    DEFAULT_MAX_LENGTH: int = 512
    GRADIENT_ACCUMULATION_STEPS: int = 4
    
    # LoRA默认配置
    LORA_CONFIG_L1: dict = {
        "rank": 8,
        "alpha": 16,
        "target_modules": ["q_proj", "k_proj", "v_proj"],
        "learning_rate": 3e-4,
    }
    LORA_CONFIG_L2: dict = {
        "rank": 16,
        "alpha": 32,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "learning_rate": 1e-4,
    }
    LORA_CONFIG_L3: dict = {
        "rank": 32,
        "alpha": 64,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        "learning_rate": 5e-5,
    }
    
    # Celery配置
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # 监控配置
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # 安全配置
    ENABLE_RATE_LIMIT: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    ENABLE_AUDIT_LOG: bool = True
    
    # GPU配置
    CUDA_VISIBLE_DEVICES: str = "0"
    USE_MIXED_PRECISION: bool = True
    
    # 微服务地址
    MODEL_SERVICE_URL: str = "http://localhost:8001"
    TASK_SERVICE_URL: str = "http://localhost:8002"
    AUTH_SERVICE_URL: str = "http://localhost:8003"
    TRAINING_SERVICE_URL: str = "http://localhost:8004"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()


# LoRA配置映射
LORA_CONFIG_MAP = {
    "l1_basic": settings.LORA_CONFIG_L1,
    "l2_domain": settings.LORA_CONFIG_L2,
    "l3_complex": settings.LORA_CONFIG_L3,
}


def get_lora_config(complexity: str) -> dict:
    """根据复杂度获取LoRA配置"""
    return LORA_CONFIG_MAP.get(complexity, settings.LORA_CONFIG_L2)


def ensure_directories():
    """确保必要的目录存在"""
    dirs = [
        settings.UPLOAD_DIR,
        settings.MODELS_DIR,
        settings.LORA_ADAPTERS_DIR,
        settings.CACHE_DIR,
        "logs",
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

