"""
训练日志API路由
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Optional
import os
from pathlib import Path
from backend.common.auth import get_current_user
from backend.common.models import User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# 日志目录
LOGS_DIR = Path(__file__).parent.parent.parent.parent / "logs" / "training"


@router.get("/list")
async def list_training_logs(
    current_user: User = Depends(get_current_user)
):
    """
    列出所有训练日志文件
    """
    try:
        if not LOGS_DIR.exists():
            return {"logs": []}
        
        log_files = []
        for log_file in LOGS_DIR.glob("task_*.log"):
            try:
                task_id = int(log_file.stem.replace("task_", ""))
                stat = log_file.stat()
                log_files.append({
                    "task_id": task_id,
                    "filename": log_file.name,
                    "size": stat.st_size,
                    "size_human": _format_size(stat.st_size),
                    "modified_at": stat.st_mtime,
                })
            except ValueError:
                continue
        
        # 按修改时间倒序排序
        log_files.sort(key=lambda x: x["modified_at"], reverse=True)
        
        return {"logs": log_files}
    
    except Exception as e:
        logger.error(f"Failed to list logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def get_training_log(
    task_id: int,
    tail: Optional[int] = None,
    current_user: User = Depends(get_current_user)
):
    """
    获取指定任务的训练日志
    
    Args:
        task_id: 任务ID
        tail: 只返回最后N行（可选）
    """
    log_file = LOGS_DIR / f"task_{task_id}.log"
    
    if not log_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Log file not found for task {task_id}"
        )
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            if tail and tail > 0:
                # 返回最后N行
                lines = f.readlines()
                content = ''.join(lines[-tail:])
            else:
                # 返回全部内容
                content = f.read()
        
        return {
            "task_id": task_id,
            "content": content,
            "lines": len(content.split('\n')),
        }
    
    except Exception as e:
        logger.error(f"Failed to read log for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/download")
async def download_training_log(
    task_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    下载训练日志文件
    """
    log_file = LOGS_DIR / f"task_{task_id}.log"
    
    if not log_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Log file not found for task {task_id}"
        )
    
    return FileResponse(
        path=str(log_file),
        filename=f"task_{task_id}_training.log",
        media_type="text/plain"
    )


@router.get("/{task_id}/stream")
async def stream_training_log(
    task_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    流式传输训练日志（类似tail -f）
    """
    log_file = LOGS_DIR / f"task_{task_id}.log"
    
    if not log_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Log file not found for task {task_id}"
        )
    
    async def generate():
        """生成器：持续读取日志文件"""
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # 先发送已有内容
                yield f.read()
                
                # 然后持续监听新内容
                while True:
                    line = f.readline()
                    if line:
                        yield line
                    else:
                        # 暂停一下再检查
                        import asyncio
                        await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Error streaming log: {e}")
            yield f"\n\n[Error: {e}]\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@router.delete("/{task_id}")
async def delete_training_log(
    task_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    删除训练日志文件
    """
    log_file = LOGS_DIR / f"task_{task_id}.log"
    
    if not log_file.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Log file not found for task {task_id}"
        )
    
    try:
        log_file.unlink()
        return {"message": f"Log file for task {task_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Failed to delete log for task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

