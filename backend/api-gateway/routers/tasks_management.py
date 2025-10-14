"""
任务管理API - 停止和删除等操作
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from backend.common.database import get_db
from backend.common.models import User, Task, TaskStatus
from backend.common.auth import get_current_user, check_resource_owner
from backend.common.process_manager import ProcessManager

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: int,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    停止训练任务
    
    Args:
        task_id: 任务ID
        force: 是否强制停止（SIGKILL）
    """
    # 获取任务
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
    
    # 检查任务状态
    if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot stop task in {task.status.value} status"
        )
    
    # 停止进程
    try:
        stopped = ProcessManager.stop_process(task_id, force=force)
        
        if stopped:
            # 更新任务状态
            task.status = TaskStatus.CANCELLED
            db.commit()
            db.refresh(task)
            
            logger.info(f"Task {task_id} stopped successfully by user {current_user.id}")
            
            return {
                "success": True,
                "message": f"Task {task_id} stopped successfully",
                "task": {
                    "id": task.id,
                    "status": task.status.value
                }
            }
        else:
            # 即使进程停止失败，也更新状态（可能进程已经结束）
            task.status = TaskStatus.CANCELLED
            db.commit()
            db.refresh(task)
            
            return {
                "success": True,
                "message": f"Task {task_id} marked as cancelled (process may have already stopped)",
                "task": {
                    "id": task.id,
                    "status": task.status.value
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to stop task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop task: {str(e)}"
        )


@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    force: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除训练任务
    
    Args:
        task_id: 任务ID
        force: 是否强制删除（即使任务正在运行）
    """
    # 获取任务
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
    
    # 检查任务状态
    if task.status in [TaskStatus.RUNNING, TaskStatus.PENDING] and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete running task. Stop the task first or use force=True"
        )
    
    try:
        # 如果任务正在运行，先停止
        if task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]:
            logger.info(f"Stopping running task {task_id} before deletion")
            ProcessManager.stop_process(task_id, force=True)
        
        # 删除任务记录
        task_name = task.task_name
        db.delete(task)
        db.commit()
        
        logger.info(f"Task {task_id} ({task_name}) deleted by user {current_user.id}")
        
        return {
            "success": True,
            "message": f"Task '{task_name}' deleted successfully"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


@router.get("/{task_id}/process")
async def get_task_process_status(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取任务的进程状态
    
    Args:
        task_id: 任务ID
    """
    # 获取任务
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
    
    # 获取进程状态
    process_status = ProcessManager.get_task_status(task_id)
    
    return {
        "task_id": task_id,
        "task_status": task.status.value,
        "process": process_status
    }

