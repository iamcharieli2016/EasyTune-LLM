"""
训练进程管理
用于追踪和管理训练进程
"""
import os
import signal
import psutil
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import json

logger = logging.getLogger(__name__)

# PID文件存储目录
PID_DIR = Path(__file__).parent.parent.parent / "logs" / "pids"
PID_DIR.mkdir(parents=True, exist_ok=True)


class ProcessManager:
    """训练进程管理器"""
    
    @staticmethod
    def save_pid(task_id: int, pid: int) -> None:
        """
        保存训练进程的PID
        
        Args:
            task_id: 任务ID
            pid: 进程ID
        """
        pid_file = PID_DIR / f"task_{task_id}.pid"
        try:
            with open(pid_file, 'w') as f:
                json.dump({
                    'task_id': task_id,
                    'pid': pid,
                    'timestamp': psutil.Process(pid).create_time()
                }, f)
            logger.info(f"Saved PID {pid} for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to save PID for task {task_id}: {e}")
    
    @staticmethod
    def get_pid(task_id: int) -> Optional[int]:
        """
        获取任务的进程ID
        
        Args:
            task_id: 任务ID
            
        Returns:
            进程ID，如果不存在返回None
        """
        pid_file = PID_DIR / f"task_{task_id}.pid"
        if not pid_file.exists():
            return None
        
        try:
            with open(pid_file, 'r') as f:
                data = json.load(f)
                return data.get('pid')
        except Exception as e:
            logger.error(f"Failed to read PID for task {task_id}: {e}")
            return None
    
    @staticmethod
    def remove_pid_file(task_id: int) -> None:
        """
        删除PID文件
        
        Args:
            task_id: 任务ID
        """
        pid_file = PID_DIR / f"task_{task_id}.pid"
        if pid_file.exists():
            try:
                pid_file.unlink()
                logger.info(f"Removed PID file for task {task_id}")
            except Exception as e:
                logger.error(f"Failed to remove PID file for task {task_id}: {e}")
    
    @staticmethod
    def is_process_running(pid: int) -> bool:
        """
        检查进程是否在运行
        
        Args:
            pid: 进程ID
            
        Returns:
            True如果进程在运行，否则False
        """
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    @staticmethod
    def get_process_info(pid: int) -> Optional[Dict[str, Any]]:
        """
        获取进程信息
        
        Args:
            pid: 进程ID
            
        Returns:
            进程信息字典
        """
        try:
            process = psutil.Process(pid)
            return {
                'pid': pid,
                'name': process.name(),
                'status': process.status(),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'memory_percent': process.memory_percent(),
                'create_time': process.create_time()
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Failed to get process info for PID {pid}: {e}")
            return None
    
    @staticmethod
    def stop_process(task_id: int, force: bool = False) -> bool:
        """
        停止训练进程
        
        Args:
            task_id: 任务ID
            force: 是否强制终止（SIGKILL vs SIGTERM）
            
        Returns:
            True如果成功停止，否则False
        """
        pid = ProcessManager.get_pid(task_id)
        if not pid:
            logger.warning(f"No PID found for task {task_id}")
            return False
        
        if not ProcessManager.is_process_running(pid):
            logger.info(f"Process {pid} is not running for task {task_id}")
            ProcessManager.remove_pid_file(task_id)
            return True
        
        try:
            process = psutil.Process(pid)
            
            if force:
                # 强制终止
                logger.info(f"Force killing process {pid} for task {task_id}")
                process.kill()  # SIGKILL
            else:
                # 优雅终止
                logger.info(f"Terminating process {pid} for task {task_id}")
                process.terminate()  # SIGTERM
                
                # 等待进程结束（最多5秒）
                try:
                    process.wait(timeout=5)
                except psutil.TimeoutExpired:
                    logger.warning(f"Process {pid} did not terminate gracefully, force killing")
                    process.kill()
            
            # 删除PID文件
            ProcessManager.remove_pid_file(task_id)
            logger.info(f"Successfully stopped process {pid} for task {task_id}")
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.error(f"Failed to stop process {pid} for task {task_id}: {e}")
            ProcessManager.remove_pid_file(task_id)
            return False
    
    @staticmethod
    def get_task_status(task_id: int) -> Dict[str, Any]:
        """
        获取任务的进程状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            状态信息字典
        """
        pid = ProcessManager.get_pid(task_id)
        
        if not pid:
            return {
                'has_process': False,
                'is_running': False
            }
        
        is_running = ProcessManager.is_process_running(pid)
        
        result = {
            'has_process': True,
            'is_running': is_running,
            'pid': pid
        }
        
        if is_running:
            process_info = ProcessManager.get_process_info(pid)
            if process_info:
                result.update(process_info)
        
        return result

