"""
数据库初始化脚本
创建表结构和初始数据
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.common.database import init_db, SessionLocal
from backend.common.models import User, UserRole, Permission, Role
from backend.common.auth import get_password_hash


def create_initial_data():
    """创建初始数据"""
    db = SessionLocal()
    
    try:
        # 检查是否已有用户
        existing_user = db.query(User).first()
        if existing_user:
            print("数据库已初始化，跳过...")
            return
        
        print("创建初始管理员用户...")
        admin_user = User(
            username="admin",
            email="admin@easytune-llm.com",
            full_name="系统管理员",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin_user)
        
        print("创建测试用户...")
        test_user = User(
            username="test_user",
            email="test@easytune-llm.com",
            full_name="测试用户",
            hashed_password=get_password_hash("test123"),
            role=UserRole.USER,
            is_active=True
        )
        db.add(test_user)
        
        print("创建权限...")
        permissions = [
            Permission(name="model_create", resource="model", action="create", description="创建模型"),
            Permission(name="model_read", resource="model", action="read", description="查看模型"),
            Permission(name="model_update", resource="model", action="update", description="更新模型"),
            Permission(name="model_delete", resource="model", action="delete", description="删除模型"),
            Permission(name="task_create", resource="task", action="create", description="创建任务"),
            Permission(name="task_read", resource="task", action="read", description="查看任务"),
            Permission(name="task_update", resource="task", action="update", description="更新任务"),
            Permission(name="task_delete", resource="task", action="delete", description="删除任务"),
            Permission(name="dataset_create", resource="dataset", action="create", description="创建数据集"),
            Permission(name="dataset_read", resource="dataset", action="read", description="查看数据集"),
            Permission(name="dataset_update", resource="dataset", action="update", description="更新数据集"),
            Permission(name="dataset_delete", resource="dataset", action="delete", description="删除数据集"),
        ]
        
        for perm in permissions:
            db.add(perm)
        
        print("创建角色...")
        admin_role = Role(
            name="admin",
            description="管理员角色",
            permissions=[p.name for p in permissions]
        )
        db.add(admin_role)
        
        user_role = Role(
            name="user",
            description="普通用户角色",
            permissions=[p.name for p in permissions if "delete" not in p.name]
        )
        db.add(user_role)
        
        viewer_role = Role(
            name="viewer",
            description="查看者角色",
            permissions=[p.name for p in permissions if "read" in p.name]
        )
        db.add(viewer_role)
        
        db.commit()
        print("初始数据创建成功！")
        print("\n默认管理员账号：")
        print("用户名: admin")
        print("密码: admin123")
        print("\n默认测试账号：")
        print("用户名: test_user")
        print("密码: test123")
        
    except Exception as e:
        print(f"创建初始数据失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("开始初始化数据库...")
    
    # 创建表结构
    print("创建表结构...")
    init_db()
    
    # 创建初始数据
    create_initial_data()
    
    print("数据库初始化完成！")

