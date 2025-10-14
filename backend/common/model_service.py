"""
模型服务管理
支持模型下载、本地服务启动、远程API访问
"""
import os
import json
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelSource(str, Enum):
    """模型来源"""
    HUGGINGFACE = "huggingface"
    MODELSCOPE = "modelscope"
    LOCAL = "local"
    REMOTE_API = "remote_api"


class ModelServiceType(str, Enum):
    """模型服务类型"""
    LOCAL_VLLM = "local_vllm"  # 使用vLLM启动本地服务
    LOCAL_TRANSFORMERS = "local_transformers"  # 直接使用transformers
    REMOTE_OPENAI = "remote_openai"  # OpenAI兼容API
    REMOTE_CUSTOM = "remote_custom"  # 自定义远程API


class ModelDownloader:
    """模型下载器"""
    
    def __init__(self, download_dir: str = "./models"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download_from_huggingface(
        self,
        model_id: str,
        token: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        从HuggingFace下载模型
        
        Args:
            model_id: 模型ID，如 "Qwen/Qwen-7B-Chat"
            token: HuggingFace token（私有模型需要）
            progress_callback: 进度回调函数
            
        Returns:
            下载结果信息
        """
        try:
            from huggingface_hub import snapshot_download
            
            model_name = model_id.split('/')[-1]
            local_dir = self.download_dir / model_name
            
            logger.info(f"Downloading model from HuggingFace: {model_id}")
            
            # 下载模型
            snapshot_download(
                repo_id=model_id,
                local_dir=str(local_dir),
                token=token,
                resume_download=True,
            )
            
            logger.info(f"Model downloaded to: {local_dir}")
            
            return {
                "success": True,
                "model_path": str(local_dir),
                "model_name": model_name,
                "source": ModelSource.HUGGINGFACE.value,
                "downloaded_at": datetime.now().isoformat()
            }
            
        except ImportError:
            logger.error("huggingface_hub not installed. Run: pip install huggingface_hub")
            return {
                "success": False,
                "error": "huggingface_hub库未安装，请运行: pip install huggingface_hub"
            }
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def download_from_modelscope(
        self,
        model_id: str,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        从ModelScope下载模型（国内镜像）
        
        Args:
            model_id: 模型ID，如 "qwen/Qwen-7B-Chat"
            progress_callback: 进度回调函数
            
        Returns:
            下载结果信息
        """
        try:
            from modelscope.hub.snapshot_download import snapshot_download
            
            model_name = model_id.split('/')[-1]
            local_dir = self.download_dir / model_name
            
            logger.info(f"Downloading model from ModelScope: {model_id}")
            
            # 下载模型
            cache_dir = snapshot_download(
                model_id,
                cache_dir=str(local_dir),
            )
            
            logger.info(f"Model downloaded to: {cache_dir}")
            
            return {
                "success": True,
                "model_path": cache_dir,
                "model_name": model_name,
                "source": ModelSource.MODELSCOPE.value,
                "downloaded_at": datetime.now().isoformat()
            }
            
        except ImportError:
            logger.error("modelscope not installed. Run: pip install modelscope")
            return {
                "success": False,
                "error": "modelscope库未安装，请运行: pip install modelscope"
            }
        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_download_status(self, model_name: str) -> Dict[str, Any]:
        """获取模型下载状态"""
        model_path = self.download_dir / model_name
        
        if model_path.exists():
            # 检查是否有必要文件
            has_config = (model_path / "config.json").exists()
            has_model = any(model_path.glob("*.bin")) or any(model_path.glob("*.safetensors"))
            
            return {
                "exists": True,
                "path": str(model_path),
                "complete": has_config and has_model,
                "files": [f.name for f in model_path.iterdir()]
            }
        
        return {"exists": False, "complete": False}


class ModelServiceLauncher:
    """模型服务启动器"""
    
    def __init__(self):
        self.running_services: Dict[str, subprocess.Popen] = {}
    
    def start_vllm_service(
        self,
        model_path: str,
        port: int = 8001,
        gpu_memory_utilization: float = 0.9,
        max_model_len: int = 4096
    ) -> Dict[str, Any]:
        """
        使用vLLM启动本地模型服务
        
        Args:
            model_path: 模型路径
            port: 服务端口
            gpu_memory_utilization: GPU内存使用率
            max_model_len: 最大序列长度
            
        Returns:
            启动结果
        """
        try:
            cmd = [
                "python", "-m", "vllm.entrypoints.openai.api_server",
                "--model", model_path,
                "--port", str(port),
                "--gpu-memory-utilization", str(gpu_memory_utilization),
                "--max-model-len", str(max_model_len)
            ]
            
            logger.info(f"Starting vLLM service: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            service_key = f"vllm_{port}"
            self.running_services[service_key] = process
            
            return {
                "success": True,
                "service_key": service_key,
                "pid": process.pid,
                "endpoint": f"http://localhost:{port}/v1",
                "type": ModelServiceType.LOCAL_VLLM.value
            }
            
        except Exception as e:
            logger.error(f"Failed to start vLLM service: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def stop_service(self, service_key: str) -> bool:
        """停止模型服务"""
        if service_key in self.running_services:
            process = self.running_services[service_key]
            process.terminate()
            process.wait(timeout=10)
            del self.running_services[service_key]
            logger.info(f"Service {service_key} stopped")
            return True
        return False
    
    def get_service_status(self, service_key: str) -> Dict[str, Any]:
        """获取服务状态"""
        if service_key in self.running_services:
            process = self.running_services[service_key]
            return {
                "running": process.poll() is None,
                "pid": process.pid
            }
        return {"running": False}


class RemoteModelAPI:
    """远程模型API访问"""
    
    def __init__(self, api_config: Dict[str, Any]):
        self.api_type = api_config.get("type", ModelServiceType.REMOTE_OPENAI.value)
        self.base_url = api_config.get("base_url")
        self.api_key = api_config.get("api_key")
        self.model_name = api_config.get("model_name")
    
    def test_connection(self) -> Dict[str, Any]:
        """测试API连接"""
        try:
            if self.api_type == ModelServiceType.REMOTE_OPENAI.value:
                # OpenAI兼容API测试
                headers = {"Authorization": f"Bearer {self.api_key}"}
                response = requests.get(
                    f"{self.base_url}/models",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "message": "API连接成功",
                        "models": response.json().get("data", [])
                    }
            
            return {
                "success": False,
                "error": "Unsupported API type"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


class ModelServiceManager:
    """模型服务管理器（统一接口）"""
    
    def __init__(self):
        self.downloader = ModelDownloader()
        self.launcher = ModelServiceLauncher()
        self.services_config: Dict[str, Dict] = {}
    
    def register_model_service(
        self,
        model_id: int,
        service_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        注册模型服务配置
        
        Args:
            model_id: 模型ID
            service_config: 服务配置
                {
                    "source": "huggingface|modelscope|local|remote_api",
                    "service_type": "local_vllm|local_transformers|remote_openai|remote_custom",
                    "model_path": "路径或ID",
                    "download_config": {...},  # 下载配置
                    "service_config": {...},   # 服务配置
                    "api_config": {...}        # API配置
                }
        """
        self.services_config[model_id] = service_config
        
        return {
            "success": True,
            "model_id": model_id,
            "registered": True
        }
    
    def prepare_model(self, model_id: int) -> Dict[str, Any]:
        """
        准备模型（下载、验证等）
        
        Returns:
            准备结果
        """
        if model_id not in self.services_config:
            return {"success": False, "error": "Model service not registered"}
        
        config = self.services_config[model_id]
        source = config.get("source")
        
        if source == ModelSource.HUGGINGFACE.value:
            download_config = config.get("download_config", {})
            return self.downloader.download_from_huggingface(
                model_id=download_config.get("model_id"),
                token=download_config.get("token")
            )
        
        elif source == ModelSource.MODELSCOPE.value:
            download_config = config.get("download_config", {})
            return self.downloader.download_from_modelscope(
                model_id=download_config.get("model_id")
            )
        
        elif source == ModelSource.LOCAL.value:
            # 验证本地路径
            model_path = config.get("model_path")
            if Path(model_path).exists():
                return {
                    "success": True,
                    "model_path": model_path,
                    "source": "local"
                }
            return {"success": False, "error": "Local model path not found"}
        
        elif source == ModelSource.REMOTE_API.value:
            # 测试远程API连接
            api_config = config.get("api_config", {})
            remote_api = RemoteModelAPI(api_config)
            return remote_api.test_connection()
        
        return {"success": False, "error": "Unknown source type"}
    
    def start_model_service(self, model_id: int) -> Dict[str, Any]:
        """启动模型服务"""
        if model_id not in self.services_config:
            return {"success": False, "error": "Model service not registered"}
        
        config = self.services_config[model_id]
        service_type = config.get("service_type")
        
        if service_type == ModelServiceType.LOCAL_VLLM.value:
            service_config = config.get("service_config", {})
            return self.launcher.start_vllm_service(
                model_path=config.get("model_path"),
                port=service_config.get("port", 8001),
                gpu_memory_utilization=service_config.get("gpu_memory_utilization", 0.9),
                max_model_len=service_config.get("max_model_len", 4096)
            )
        
        elif service_type in [ModelServiceType.REMOTE_OPENAI.value, ModelServiceType.REMOTE_CUSTOM.value]:
            # 远程API不需要启动，直接返回配置
            api_config = config.get("api_config", {})
            return {
                "success": True,
                "type": service_type,
                "endpoint": api_config.get("base_url"),
                "model_name": api_config.get("model_name")
            }
        
        return {"success": False, "error": "Unsupported service type"}


# 全局实例
model_service_manager = ModelServiceManager()

