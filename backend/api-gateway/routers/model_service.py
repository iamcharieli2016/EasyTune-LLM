"""
模型服务管理API
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from backend.common.database import get_db
from backend.common.models import User, Model
from backend.common.auth import get_current_user
from backend.common.model_service import (
    model_service_manager,
    ModelSource,
    ModelServiceType
)
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class ModelServiceConfig(BaseModel):
    """模型服务配置"""
    source: ModelSource = Field(..., description="模型来源")
    service_type: ModelServiceType = Field(..., description="服务类型")
    model_path: Optional[str] = Field(None, description="本地模型路径")
    
    # 下载配置（用于HuggingFace/ModelScope）
    download_config: Optional[Dict[str, Any]] = Field(None, description="下载配置")
    
    # 服务配置（用于本地服务）
    service_config: Optional[Dict[str, Any]] = Field(None, description="服务配置")
    
    # API配置（用于远程API）
    api_config: Optional[Dict[str, Any]] = Field(None, description="API配置")


class DownloadRequest(BaseModel):
    """模型下载请求"""
    model_id: str = Field(..., description="模型ID，如 Qwen/Qwen-7B-Chat")
    source: ModelSource = Field(ModelSource.HUGGINGFACE, description="下载源")
    token: Optional[str] = Field(None, description="访问令牌")


@router.post("/{model_id}/configure")
async def configure_model_service(
    model_id: int,
    config: ModelServiceConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    配置模型服务
    """
    # 验证模型存在
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # 注册服务配置
    result = model_service_manager.register_model_service(
        model_id=model_id,
        service_config=config.dict()
    )
    
    return result


@router.post("/{model_id}/download")
async def download_model(
    model_id: int,
    download_req: DownloadRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下载模型文件（后台任务）
    """
    # 验证模型存在
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # 配置下载任务
    service_config = {
        "source": download_req.source.value,
        "service_type": ModelServiceType.LOCAL_TRANSFORMERS.value,
        "download_config": {
            "model_id": download_req.model_id,
            "token": download_req.token
        }
    }
    
    model_service_manager.register_model_service(model_id, service_config)
    
    # 后台下载
    def download_task():
        result = model_service_manager.prepare_model(model_id)
        if result.get("success"):
            # 更新数据库中的模型路径
            model.model_path = result.get("model_path")
            db.commit()
            logger.info(f"Model {model_id} downloaded successfully")
        else:
            logger.error(f"Model {model_id} download failed: {result.get('error')}")
    
    background_tasks.add_task(download_task)
    
    return {
        "message": "模型下载已在后台启动",
        "model_id": model_id,
        "status": "downloading"
    }


@router.get("/{model_id}/download/status")
async def get_download_status(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取模型下载状态
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # 检查模型文件状态
    model_name = model.name
    status_info = model_service_manager.downloader.get_download_status(model_name)
    
    return {
        "model_id": model_id,
        "model_name": model_name,
        **status_info
    }


@router.post("/{model_id}/prepare")
async def prepare_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    准备模型（下载或验证）
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    result = model_service_manager.prepare_model(model_id)
    
    if result.get("success"):
        # 更新模型路径
        if "model_path" in result:
            model.model_path = result["model_path"]
            db.commit()
    
    return result


@router.post("/{model_id}/start")
async def start_model_service(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    启动模型服务
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    result = model_service_manager.start_model_service(model_id)
    
    return result


@router.post("/{model_id}/stop")
async def stop_model_service(
    model_id: int,
    service_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    停止模型服务
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    success = model_service_manager.launcher.stop_service(service_key)
    
    return {
        "success": success,
        "service_key": service_key
    }


@router.get("/{model_id}/status")
async def get_service_status(
    model_id: int,
    service_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取服务状态
    """
    status_info = model_service_manager.launcher.get_service_status(service_key)
    
    return {
        "model_id": model_id,
        "service_key": service_key,
        **status_info
    }


@router.post("/test-api")
async def test_remote_api(
    api_config: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    测试远程API连接
    """
    from backend.common.model_service import RemoteModelAPI
    
    api = RemoteModelAPI(api_config)
    result = api.test_connection()
    
    return result

