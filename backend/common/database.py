"""
数据库配置模块
提供数据库连接和会话管理
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# 从环境变量读取数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://easytune:easytune@localhost:5432/easytune_db"
)

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=False
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI依赖注入
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库
    创建所有表
    """
    from backend.common.models import (
        User, Model, Dataset, Task, TaskLog, Permission, Role
    )
    Base.metadata.create_all(bind=engine)


def drop_db():
    """
    删除所有表
    仅用于开发/测试
    """
    Base.metadata.drop_all(bind=engine)

