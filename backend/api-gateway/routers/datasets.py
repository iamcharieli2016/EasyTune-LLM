"""
数据集管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import json
import csv
import shutil
from datetime import datetime

from backend.common.database import get_db
from backend.common.models import User, Dataset
from backend.common.schemas import (
    DatasetCreate, DatasetResponse, PaginatedResponse, BaseResponse
)
from backend.common.auth import get_current_user, check_resource_owner
from backend.common.config import settings

router = APIRouter()


async def validate_dataset(file_path: str, file_format: str) -> dict:
    """
    验证数据集格式和内容
    返回数据集统计信息
    """
    stats = {
        "total_samples": 0,
        "avg_input_length": 0,
        "avg_output_length": 0,
        "is_valid": False,
        "errors": []
    }
    
    try:
        if file_format == "json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    stats["total_samples"] = len(data)
                    # 验证数据格式
                    if data and all(isinstance(item, dict) for item in data):
                        stats["is_valid"] = True
                    else:
                        stats["errors"].append("Invalid JSON format")
                else:
                    stats["errors"].append("Expected JSON array")
        
        elif file_format == "jsonl":
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                stats["total_samples"] = len(lines)
                stats["is_valid"] = True
        
        elif file_format == "csv":
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                stats["total_samples"] = len(rows)
                stats["is_valid"] = True
        
    except Exception as e:
        stats["errors"].append(str(e))
    
    return stats


@router.get("/", response_model=PaginatedResponse)
async def list_datasets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据集列表
    """
    offset = (page - 1) * page_size
    
    query = db.query(Dataset)
    
    # 只能看到自己的数据集（管理员可以看到所有）
    if current_user.role != "admin":
        query = query.filter(Dataset.owner_id == current_user.id)
    
    # 搜索
    if search:
        query = query.filter(Dataset.name.ilike(f"%{search}%"))
    
    total = query.count()
    datasets = query.offset(offset).limit(page_size).all()
    
    return PaginatedResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[DatasetResponse.from_orm(ds) for ds in datasets]
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取数据集详情
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, dataset.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return dataset


@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    name: str,
    description: Optional[str] = None,
    dataset_type: str = "instruction",
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    上传数据集
    """
    # 检查文件格式
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File format not allowed. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )
    
    # 创建用户目录
    user_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_dir, exist_ok=True)
    
    # 生成唯一文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.{file_ext}"
    file_path = os.path.join(user_dir, filename)
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 验证数据集
    validation_result = await validate_dataset(file_path, file_ext)
    
    # 创建数据集记录
    new_dataset = Dataset(
        name=name,
        description=description,
        dataset_path=file_path,
        dataset_type=dataset_type,
        file_format=file_ext,
        total_samples=validation_result["total_samples"],
        is_validated=validation_result["is_valid"],
        validation_errors=validation_result["errors"] if validation_result["errors"] else None,
        owner_id=current_user.id
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    return new_dataset


@router.post("/", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    dataset_data: DatasetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建数据集记录（用于引用外部数据集）
    """
    new_dataset = Dataset(
        **dataset_data.dict(),
        owner_id=current_user.id
    )
    db.add(new_dataset)
    db.commit()
    db.refresh(new_dataset)
    
    return new_dataset


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除数据集
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, dataset.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 删除文件
    if os.path.exists(dataset.dataset_path):
        try:
            os.remove(dataset.dataset_path)
        except Exception as e:
            print(f"Failed to delete dataset file: {e}")
    
    db.delete(dataset)
    db.commit()
    
    return {"message": "Dataset deleted successfully"}


@router.get("/{dataset_id}/preview")
async def preview_dataset(
    dataset_id: int,
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    预览数据集内容
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dataset not found"
        )
    
    # 检查权限
    if not check_resource_owner(current_user, dataset.owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # 读取数据
    try:
        data = []
        if dataset.file_format == "json":
            with open(dataset.dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)[:limit]
        elif dataset.file_format == "jsonl":
            with open(dataset.dataset_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    data.append(json.loads(line))
        elif dataset.file_format == "csv":
            with open(dataset.dataset_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = [row for i, row in enumerate(reader) if i < limit]
        
        return {
            "dataset_id": dataset_id,
            "preview_count": len(data),
            "total_samples": dataset.total_samples,
            "samples": data
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read dataset: {str(e)}"
        )

