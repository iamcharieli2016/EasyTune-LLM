"""
任务管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.common.database import get_db
from backend.common.models import User, Task, TaskStatus, Model, Dataset
from backend.common.schemas import (
    TaskCreate, TaskUpdate, TaskResponse, PaginatedResponse, 
    BaseResponse, DashboardStats
)
from backend.common.auth import get_current_user, check_resource_owner
from backend.common.config import settings, get_lora_config

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取仪表板统计信息
    """
    query = db.query(Task)
    if current_user.role != "admin":
        query = query.filter(Task.owner_id == current_user.id)
    
    total_tasks = query.count()
    running_tasks = query.filter(Task.status == TaskStatus.RUNNING).count()
    completed_tasks = query.filter(Task.status == TaskStatus.COMPLETED).count()
    failed_tasks = query.filter(Task.status == TaskStatus.FAILED).count()
    
    # 模型和数据集统计
    model_query = db.query(Model)
    dataset_query = db.query(Dataset)
    if current_user.role != "admin":
        model_query = model_query.filter(Model.owner_id == current_user.id)
        dataset_query = dataset_query.filter(Dataset.owner_id == current_user.id)
    
    total_models = model_query.count()
    total_datasets = dataset_query.count()
    
    # 用户统计（仅管理员）
    total_users = 0
    if current_user.role == "admin":
        total_users = db.query(User).count()
    
    return DashboardStats(
        total_tasks=total_tasks,
        running_tasks=running_tasks,
        completed_tasks=completed_tasks,
        failed_tasks=failed_tasks,
        total_models=total_models,
        total_datasets=total_datasets,
        total_users=total_users
    )


@router.get("/", response_model=PaginatedResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TaskStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取任务列表
    """
    offset = (page - 1) * page_size
    
    query = db.query(Task)
    
    # 只能看到自己的任务（管理员可以看到所有）
    if current_user.role != "admin":
        query = query.filter(Task.owner_id == current_user.id)
    
    # 状态筛选
    if status_filter:
        query = query.filter(Task.status == status_filter)
    
    # 按创建时间倒序
    query = query.order_by(Task.created_at.desc())
    
    total = query.count()
    tasks = query.offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[TaskResponse.from_orm(task) for task in tasks]
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取任务详情
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, task.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建训练任务
    基于意图驱动自动配置LoRA参数
    """
    # 验证模型存在
    base_model = db.query(Model).filter(Model.id == task_data.base_model_id).first()
    if not base_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base model not found"
        )
    
    # 验证数据集存在
    dataset = db.query(Dataset).filter(Dataset.id == task_data.dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # 根据任务复杂度自动生成LoRA配置
    lora_config = get_lora_config(task_data.task_complexity.value)
    
    # 创建训练配置
    training_config = {
        "task_complexity": task_data.task_complexity.value,
        "lora_rank": lora_config["rank"],
        "lora_alpha": lora_config["alpha"],
        "lora_target_modules": lora_config["target_modules"],
        "learning_rate": lora_config["learning_rate"],
        "num_epochs": task_data.num_epochs or 3,
        "batch_size": task_data.batch_size or settings.DEFAULT_BATCH_SIZE,
        "max_length": task_data.max_length or settings.DEFAULT_MAX_LENGTH,
        "gradient_accumulation_steps": settings.GRADIENT_ACCUMULATION_STEPS,
        "warmup_steps": 100,
        "save_steps": 500,
        "logging_steps": 10,
    }
    
    # 创建任务
    new_task = Task(
        task_name=task_data.task_name,
        description=task_data.description,
        task_complexity=task_data.task_complexity,
        task_intent=task_data.task_intent,
        base_model_id=task_data.base_model_id,
        dataset_id=task_data.dataset_id,
        output_model_name=task_data.output_model_name,
        training_config=training_config,
        lora_rank=lora_config["rank"],
        lora_alpha=lora_config["alpha"],
        learning_rate=lora_config["learning_rate"],
        num_epochs=training_config["num_epochs"],
        batch_size=training_config["batch_size"],
        max_length=training_config["max_length"],
        status=TaskStatus.PENDING,
        owner_id=current_user.id
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    # TODO: 发送任务到训练队列
    # send_to_training_queue(new_task.id)
    
    return new_task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新任务信息
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, task.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 更新字段
    for field, value in task_update.dict(exclude_unset=True).items():
        setattr(task, field, value)
    
    db.commit()
    db.refresh(task)
    
    return task


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    取消任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, task.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 只能取消待处理或运行中的任务
    if task.status not in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled"
        )
    
    task.status = TaskStatus.CANCELLED
    db.commit()
    
    # TODO: 通知训练引擎取消任务
    # cancel_training_task(task_id)
    
    return {"message": "Task cancelled successfully"}


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除任务
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, task.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 不能删除运行中的任务
    if task.status == TaskStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running task"
        )
    
    db.delete(task)
    db.commit()
    
    return {"message": "Task deleted successfully"}


@router.get("/{task_id}/logs")
async def get_task_logs(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取任务日志
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, task.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    logs = [
        {
            "id": log.id,
            "level": log.log_level,
            "message": log.message,
            "details": log.details,
            "timestamp": log.created_at
        }
        for log in task.logs
    ]
    
    return {
        "task_id": task_id,
        "logs": logs
    }

