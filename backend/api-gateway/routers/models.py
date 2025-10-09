"""
模型管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil

from backend.common.database import get_db
from backend.common.models import User, Model, ModelType
from backend.common.schemas import (
    ModelCreate, ModelUpdate, ModelResponse, PaginatedResponse, BaseResponse
)
from backend.common.auth import get_current_user, check_resource_owner
from backend.common.config import settings

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_models(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    model_type: Optional[ModelType] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取模型列表
    支持分页、筛选和搜索
    """
    offset = (page - 1) * page_size
    
    query = db.query(Model)
    
    # 非管理员只能看到公开模型和自己的模型
    if current_user.role != "admin":
        query = query.filter(
            (Model.is_public == True) | (Model.owner_id == current_user.id)
        )
    
    # 按类型筛选
    if model_type:
        query = query.filter(Model.model_type == model_type)
    
    # 搜索
    if search:
        query = query.filter(
            Model.name.ilike(f"%{search}%") | 
            Model.display_name.ilike(f"%{search}%")
        )
    
    total = query.count()
    models = query.offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[ModelResponse.from_orm(model) for model in models]
    )


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取模型详情
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # 检查权限（私有模型只有所有者和管理员可以访问）
    if not model.is_public and not check_resource_owner(current_user, model.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return model


@router.post("/", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    model_data: ModelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建模型记录
    """
    # 检查模型名称是否已存在
    existing = db.query(Model).filter(
        Model.name == model_data.name,
        Model.owner_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Model name already exists"
        )
    
    # 创建模型
    new_model = Model(
        **model_data.dict(),
        owner_id=current_user.id,
        framework="pytorch"
    )
    db.add(new_model)
    db.commit()
    db.refresh(new_model)
    
    return new_model


@router.put("/{model_id}", response_model=ModelResponse)
async def update_model(
    model_id: int,
    model_update: ModelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新模型信息
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, model.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 更新字段
    for field, value in model_update.dict(exclude_unset=True).items():
        setattr(model, field, value)
    
    db.commit()
    db.refresh(model)
    
    return model


@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除模型
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, model.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 删除模型文件（如果存在）
    if os.path.exists(model.model_path) and model.model_path.startswith(settings.MODELS_DIR):
        try:
            shutil.rmtree(model.model_path)
        except Exception as e:
            # 记录日志但不阻止删除
            print(f"Failed to delete model files: {e}")
    
    db.delete(model)
    db.commit()
    
    return {"message": "Model deleted successfully"}


@router.post("/{model_id}/download")
async def download_model(
    model_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    下载模型（增加下载计数）
    """
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )
    
    # 检查权限
    if not model.is_public and not check_resource_owner(current_user, model.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 增加下载计数
    model.download_count += 1
    db.commit()
    
    return {
        "message": "Model download initiated",
        "model_path": model.model_path
    }

