"""
训练引擎核心模块
基于PEFT/LoRA的模型微调
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
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    
    # 硬件配置
    fp16: bool = True
    bf16: bool = False
    gradient_checkpointing: bool = True
    
    def __post_init__(self):
        if self.lora_target_modules is None:
            self.lora_target_modules = ["q_proj", "k_proj", "v_proj"]


class LoRATrainer:
    """LoRA训练器"""
    
    def __init__(self, config: TrainingConfig, progress_callback: Optional[Callable] = None):
        self.config = config
        self.progress_callback = progress_callback
        self.model = None
        self.tokenizer = None
        self.trainer = None
        
    def load_model_and_tokenizer(self):
        """加载模型和分词器"""
        logger.info(f"Loading model: {self.config.model_name_or_path}")
        
        # 加载分词器
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=True,
            use_fast=False
        )
        
        # 设置pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.model_name_or_path,
            trust_remote_code=True,
            torch_dtype=torch.float16 if self.config.fp16 else torch.float32,
            device_map="auto"
        )
        
        # 启用梯度检查点
        if self.config.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()
        
        logger.info("Model and tokenizer loaded successfully")
        
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
        """创建训练器"""
        logger.info("Creating trainer")
        
        # 训练参数
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_train_epochs,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            fp16=self.config.fp16,
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
        )
        
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
    # 测试代码
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
    print(result)

