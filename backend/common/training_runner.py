"""
训练任务执行器
负责启动和管理训练进程
"""
import subprocess
import os
import json
from pathlib import Path
from typing import Dict, Any
from backend.common.config import settings
from backend.common.models import Task, Model, Dataset, TaskStatus
from backend.common.database import SessionLocal
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


def start_training_task(task_id: int) -> bool:
    """
    启动训练任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        bool: 是否成功启动
    """
    db = SessionLocal()
    try:
        # 获取任务信息
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return False
        
        # 获取模型和数据集信息
        model = db.query(Model).filter(Model.id == task.base_model_id).first()
        dataset = db.query(Dataset).filter(Dataset.id == task.dataset_id).first()
        
        if not model or not dataset:
            logger.error(f"Model or dataset not found for task {task_id}")
            task.status = TaskStatus.FAILED
            task.error_message = "Model or dataset not found"
            db.commit()
            return False
        
        # 更新任务状态
        task.status = TaskStatus.RUNNING
        db.commit()
        
        # 准备训练配置（使用绝对路径）
        output_dir = os.path.abspath(os.path.join(settings.LORA_ADAPTERS_DIR, task.output_model_name))
        dataset_path = os.path.abspath(dataset.dataset_path) if not os.path.isabs(dataset.dataset_path) else dataset.dataset_path
        
        training_config = {
            "task_id": task.id,
            "model_path": model.model_path,
            "dataset_path": dataset_path,
            "output_dir": output_dir,
            "lora_rank": task.lora_rank,
            "lora_alpha": task.lora_alpha,
            "learning_rate": task.learning_rate,
            "num_epochs": task.num_epochs,
            "batch_size": task.batch_size,
            "max_length": task.max_length,
            "gradient_accumulation_steps": task.training_config.get("gradient_accumulation_steps", 4),
            "warmup_steps": task.training_config.get("warmup_steps", 100),
            "save_steps": task.training_config.get("save_steps", 500),
            "logging_steps": task.training_config.get("logging_steps", 10),
            "lora_target_modules": task.training_config.get("lora_target_modules", ["q_proj", "v_proj"]),
        }
        
        # 创建输出目录
        os.makedirs(training_config["output_dir"], exist_ok=True)
        
        # 保存配置文件（使用绝对路径）
        config_file = os.path.abspath(os.path.join(training_config["output_dir"], "training_config.json"))
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(training_config, f, indent=2, ensure_ascii=False)
        
        # 启动训练脚本（后台运行）
        training_engine_path = Path(__file__).parent.parent.parent / "training-engine"
        trainer_script = training_engine_path / "src" / "trainer.py"
        
        # 使用subprocess启动训练（非阻塞）
        # 使用当前Python解释器（确保使用conda环境）
        import sys
        python_executable = sys.executable
        
        cmd = [
            python_executable,
            str(trainer_script),
            "--config", config_file,
            "--task-id", str(task_id)
        ]
        
        # 创建日志目录
        log_dir = Path(__file__).parent.parent.parent / "logs" / "training"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 日志文件路径
        log_file = log_dir / f"task_{task_id}.log"
        
        logger.info(f"Starting training for task {task_id}: {' '.join(cmd)}")
        logger.info(f"Training logs will be written to: {log_file}")
        
        # 后台启动训练进程，输出到日志文件
        with open(log_file, 'w', encoding='utf-8') as f_out:
            process = subprocess.Popen(
                cmd,
                stdout=f_out,
                stderr=subprocess.STDOUT,  # 合并stderr到stdout
                cwd=str(training_engine_path),
                env={**os.environ, "PYTHONPATH": str(Path(__file__).parent.parent.parent)}
            )
        
        logger.info(f"Training process started with PID: {process.pid}")
        logger.info(f"View logs: tail -f {log_file}")
        
        # 保存进程PID用于后续管理
        from backend.common.process_manager import ProcessManager
        ProcessManager.save_pid(task_id, process.pid)
        
        # 注意：这里不等待进程完成，训练在后台运行
        # 训练脚本需要自己更新任务状态
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to start training for task {task_id}: {e}")
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                db.commit()
        except:
            pass
        return False
    finally:
        db.close()


def start_training_in_background(task_id: int):
    """
    在后台线程启动训练
    """
    import threading
    thread = threading.Thread(target=start_training_task, args=(task_id,))
    thread.daemon = True
    thread.start()

