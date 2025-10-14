"""
训练引擎核心模块
基于PEFT/LoRA的模型微调
支持多平台：CUDA (NVIDIA), MPS (Apple Silicon), CPU
"""

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    PeftModel
)
from datasets import load_dataset
import json
import os
import platform
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_device_info() -> Dict[str, Any]:
    """
    自动检测当前系统的计算设备
    支持 CUDA (NVIDIA GPU), MPS (Apple Silicon), CPU
    
    Returns:
        dict: 包含设备类型、设备名称、可用性等信息
    """
    device_info = {
        "platform": platform.system(),
        "machine": platform.machine(),
        "device": "cpu",
        "device_name": "CPU",
        "available": True,
        "cuda_available": False,
        "mps_available": False,
        "device_count": 0,
    }
    
    # 检测CUDA (NVIDIA GPU)
    if torch.cuda.is_available():
        device_info.update({
            "device": "cuda",
            "device_name": torch.cuda.get_device_name(0),
            "cuda_available": True,
            "device_count": torch.cuda.device_count(),
            "cuda_version": torch.version.cuda,
        })
        logger.info(f"✅ 检测到 NVIDIA GPU: {device_info['device_name']}")
        logger.info(f"   GPU数量: {device_info['device_count']}")
        logger.info(f"   CUDA版本: {device_info['cuda_version']}")
    
    # 检测MPS (Apple Silicon)
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device_info.update({
            "device": "mps",
            "device_name": "Apple Silicon (MPS)",
            "mps_available": True,
        })
        logger.info(f"✅ 检测到 Apple Silicon GPU (MPS)")
        logger.info(f"   系统: {device_info['platform']} {device_info['machine']}")
    
    # 回退到CPU
    else:
        logger.warning("⚠️  未检测到GPU，将使用CPU进行训练")
        logger.warning("   训练速度会较慢，建议使用GPU")
    
    return device_info


def get_optimal_device() -> str:
    """
    获取最优计算设备
    优先级: CUDA > MPS > CPU
    
    Returns:
        str: 设备字符串 ("cuda", "mps", "cpu")
    """
    device_info = get_device_info()
    return device_info["device"]


def get_torch_dtype(device: str) -> torch.dtype:
    """
    根据设备类型获取最优的数据类型
    
    Args:
        device: 设备类型 ("cuda", "mps", "cpu")
    
    Returns:
        torch.dtype: 推荐的数据类型
    """
    if device == "cuda":
        # CUDA支持float16
        return torch.float16
    elif device == "mps":
        # MPS在某些情况下float16可能有问题，使用float32更稳定
        # 如果PyTorch版本支持，可以使用bfloat16
        if torch.backends.mps.is_built():
            return torch.float32  # MPS目前对float16支持不完全
        return torch.float32
    else:
        # CPU使用float32
        return torch.float32


@dataclass
class TrainingConfig:
    """训练配置"""
    model_name_or_path: str
    dataset_path: str
    output_dir: str
    
    # LoRA配置
    lora_rank: int = 8
    lora_alpha: int = 16
    lora_dropout: float = 0.05
    lora_target_modules: list = None
    
    # 训练参数
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 4
    learning_rate: float = 3e-4
    max_length: int = 512
    
    # 优化参数
    warmup_steps: int = 100
    save_steps: int = 500
    logging_steps: int = 10
    eval_steps: int = 500
    save_total_limit: int = 3
    
    # 硬件配置（自动检测）
    device: str = None  # 自动检测: "cuda", "mps", "cpu"
    fp16: bool = None   # 自动根据设备设置
    bf16: bool = False
    gradient_checkpointing: bool = True
    
    def __post_init__(self):
        if self.lora_target_modules is None:
            self.lora_target_modules = ["q_proj", "k_proj", "v_proj"]
        
        # 自动检测设备
        if self.device is None:
            self.device = get_optimal_device()
            logger.info(f"🔧 自动选择计算设备: {self.device.upper()}")
        
        # 根据设备自动配置精度
        if self.fp16 is None:
            if self.device == "cuda":
                self.fp16 = True
                logger.info("   启用混合精度训练 (FP16)")
            elif self.device == "mps":
                self.fp16 = False  # MPS暂不支持FP16
                logger.info("   使用FP32精度 (MPS)")
            else:
                self.fp16 = False
                logger.info("   使用FP32精度 (CPU)")


class LoRATrainer:
    """LoRA训练器"""
    
    def __init__(self, config: TrainingConfig, progress_callback: Optional[Callable] = None):
        self.config = config
        self.progress_callback = progress_callback
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
    def load_model_and_tokenizer(self):
        """加载模型和分词器（支持多平台）"""
        logger.info(f"📦 加载模型: {self.config.model_name_or_path}")
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=True,
            use_fast=False
        )
        
        # 设置pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 根据设备选择合适的数据类型和加载策略
        torch_dtype = get_torch_dtype(self.config.device)
        
        # 设备映射策略
        if self.config.device == "cuda":
            device_map = "auto"  # CUDA支持自动分配
        elif self.config.device == "mps":
            device_map = None    # MPS需要手动管理
        else:
            device_map = None    # CPU
        
        logger.info(f"   数据类型: {torch_dtype}")
        logger.info(f"   设备映射: {device_map if device_map else 'manual'}")
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=True,
            torch_dtype=torch_dtype,
            device_map=device_map,
            low_cpu_mem_usage=True
        )
        
        # 对于MPS和CPU，手动移动到设备
        if self.config.device in ["mps", "cpu"]:
            self.model = self.model.to(self.config.device)
            logger.info(f"   模型已移动到 {self.config.device.upper()}")
        
        # 启用梯度检查点
        if self.config.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()
            logger.info("   已启用梯度检查点")
        
        logger.info("✅ 模型和分词器加载成功")
        
    def prepare_peft_model(self):
        """准备PEFT模型"""
        logger.info("Preparing PEFT model with LoRA")
        
        # 创建LoRA配置
        peft_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.lora_target_modules,
            bias="none",
            inference_mode=False
        )
        
        # 应用LoRA
        self.model = get_peft_model(self.model, peft_config)
        
        # 打印可训练参数
        self.model.print_trainable_parameters()
        
        logger.info("PEFT model prepared successfully")
        
    def load_and_prepare_dataset(self):
        """加载和准备数据集"""
        logger.info(f"Loading dataset: {self.config.dataset_path}")
        
        # 根据文件扩展名加载数据集
        file_ext = self.config.dataset_path.split('.')[-1]
        
        if file_ext == 'json':
            dataset = load_dataset('json', data_files=self.config.dataset_path)
        elif file_ext == 'jsonl':
            dataset = load_dataset('json', data_files=self.config.dataset_path)
        elif file_ext == 'csv':
            dataset = load_dataset('csv', data_files=self.config.dataset_path)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        # 数据预处理函数
        def preprocess_function(examples):
            # 假设数据格式包含 'instruction', 'input', 'output' 字段
            texts = []
            for i in range(len(examples.get('instruction', examples.get('text', [])))):
                if 'instruction' in examples:
                    instruction = examples['instruction'][i]
                    input_text = examples.get('input', [''] * len(examples['instruction']))[i]
                    output_text = examples['output'][i]
                    
                    # 构建训练文本
                    if input_text:
                        text = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n{output_text}"
                    else:
                        text = f"### Instruction:\n{instruction}\n\n### Response:\n{output_text}"
                else:
                    text = examples['text'][i]
                
                texts.append(text)
            
            # 分词
            tokenized = self.tokenizer(
                texts,
                truncation=True,
                max_length=self.config.max_length,
                padding="max_length",
                return_tensors="pt"
            )
            
            tokenized["labels"] = tokenized["input_ids"].clone()
            return tokenized
        
        # 应用预处理
        processed_dataset = dataset.map(
            preprocess_function,
            batched=True,
            remove_columns=dataset["train"].column_names
        )
        
        # 分割训练集和验证集
        if "validation" not in processed_dataset:
            split_dataset = processed_dataset["train"].train_test_split(test_size=0.1, seed=42)
            train_dataset = split_dataset["train"]
            eval_dataset = split_dataset["test"]
        else:
            train_dataset = processed_dataset["train"]
            eval_dataset = processed_dataset["validation"]
        
        logger.info(f"Dataset loaded: {len(train_dataset)} train, {len(eval_dataset)} eval")
        
        return train_dataset, eval_dataset
        
    def create_trainer(self, train_dataset, eval_dataset):
        """创建训练器（支持多平台）"""
        logger.info("🔨 创建训练器")
        
        # 根据设备调整训练参数
        use_mps_device = self.config.device == "mps"
        
        # 训练参数
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            fp16=self.config.fp16 and self.config.device == "cuda",  # 仅CUDA支持FP16
            bf16=self.config.bf16,
            warmup_steps=self.config.warmup_steps,
            save_steps=self.config.save_steps,
            logging_steps=self.config.logging_steps,
            eval_steps=self.config.eval_steps,
            evaluation_strategy="steps",
            save_strategy="steps",
            save_total_limit=self.config.save_total_limit,
            load_best_model_at_end=True,
            report_to=["tensorboard"],
            logging_dir=f"{self.config.output_dir}/logs",
            remove_unused_columns=False,
            use_mps_device=use_mps_device,  # 启用MPS支持
        )
        
        logger.info(f"   训练设备: {self.config.device.upper()}")
        logger.info(f"   混合精度: {'FP16' if training_args.fp16 else 'FP32'}")
        
        # 数据整理器
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # 创建Trainer
        self.trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
        )
        
        logger.info("Trainer created successfully")
        
    def train(self):
        """执行训练"""
        logger.info("Starting training...")
        
        try:
            # 训练
            train_result = self.trainer.train()
            
            # 保存模型
            self.trainer.save_model()
            
            # 保存训练指标
            metrics = train_result.metrics
            self.trainer.log_metrics("train", metrics)
            self.trainer.save_metrics("train", metrics)
            
            # 评估
            eval_metrics = self.trainer.evaluate()
            self.trainer.log_metrics("eval", eval_metrics)
            self.trainer.save_metrics("eval", eval_metrics)
            
            logger.info("Training completed successfully")
            
            return {
                "success": True,
                "train_metrics": metrics,
                "eval_metrics": eval_metrics
            }
            
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def save_lora_adapter(self, output_path: str):
        """保存LoRA适配器"""
        logger.info(f"Saving LoRA adapter to {output_path}")
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        logger.info("LoRA adapter saved successfully")
    
    def merge_and_save(self, output_path: str):
        """合并LoRA权重并保存完整模型"""
        logger.info(f"Merging LoRA weights and saving to {output_path}")
        
        # 合并权重
        merged_model = self.model.merge_and_unload()
        
        # 保存
        merged_model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)
        
        logger.info("Merged model saved successfully")
        
    def run_full_training(self):
        """运行完整的训练流程"""
        try:
            # 1. 加载模型和分词器
            self.load_model_and_tokenizer()
            
            # 2. 准备PEFT模型
            self.prepare_peft_model()
            
            # 3. 加载数据集
            train_dataset, eval_dataset = self.load_and_prepare_dataset()
            
            # 4. 创建训练器
            self.create_trainer(train_dataset, eval_dataset)
            
            # 5. 训练
            result = self.train()
            
            # 6. 保存LoRA适配器
            lora_adapter_path = os.path.join(self.config.output_dir, "lora_adapter")
            self.save_lora_adapter(lora_adapter_path)
            
            # 7. 可选：保存合并后的完整模型
            # merged_model_path = os.path.join(self.config.output_dir, "merged_model")
            # self.merge_and_save(merged_model_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Training pipeline failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


def calculate_catastrophic_forgetting_score(
    base_model_path: str,
    finetuned_model_path: str,
    eval_dataset_path: str
) -> float:
    """
    计算灾难性遗忘分数 (CF Score)
    通过比较基座模型和微调模型在通用数据集上的性能
    """
    # TODO: 实现CF Score计算逻辑
    # 1. 加载基座模型和微调模型
    # 2. 在通用评估集上计算交叉熵损失
    # 3. 返回损失差异
    pass


if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description='LoRA Training Script')
    parser.add_argument('--config', type=str, help='Path to training config JSON file')
    parser.add_argument('--task-id', type=int, help='Task ID for tracking')
    args = parser.parse_args()
    
    if args.config:
        # 从配置文件加载
        logger.info(f"Loading config from {args.config}")
        with open(args.config, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        # 创建训练配置
        config = TrainingConfig(
            model_name_or_path=config_dict.get('model_path', 'meta-llama/Llama-2-7b-hf'),
            dataset_path=config_dict.get('dataset_path', './data/train.json'),
            output_dir=config_dict.get('output_dir', './outputs/lora_model'),
            lora_rank=config_dict.get('lora_rank', 8),
            lora_alpha=config_dict.get('lora_alpha', 16),
            learning_rate=config_dict.get('learning_rate', 1e-4),
            num_train_epochs=config_dict.get('num_epochs', 3),
            per_device_train_batch_size=config_dict.get('batch_size', 4),
            gradient_accumulation_steps=config_dict.get('gradient_accumulation_steps', 4),
            warmup_steps=config_dict.get('warmup_steps', 100),
            logging_steps=config_dict.get('logging_steps', 10),
            save_steps=config_dict.get('save_steps', 500),
            lora_target_modules=config_dict.get('lora_target_modules', ["q_proj", "v_proj"]),
        )
        
        logger.info(f"Task ID: {args.task_id}")
        logger.info(f"Config loaded: model={config.model_name_or_path}, dataset={config.dataset_path}")
        
        # 运行训练
        trainer = LoRATrainer(config)
        result = trainer.run_full_training()
        
        # 输出结果
        logger.info(f"Training result: {result}")
        print(json.dumps(result, ensure_ascii=False))
        
        # 返回退出码
        sys.exit(0 if result.get('success', False) else 1)
    else:
        # 测试模式（无配置文件）
        logger.warning("No config file provided, running in test mode")
        config = TrainingConfig(
            model_name_or_path="meta-llama/Llama-2-7b-hf",
            dataset_path="./data/train.json",
            output_dir="./outputs/test_run",
            lora_rank=8,
            lora_alpha=16,
            num_train_epochs=3,
        )
        
        trainer = LoRATrainer(config)
        result = trainer.run_full_training()
        print(json.dumps(result, ensure_ascii=False))

