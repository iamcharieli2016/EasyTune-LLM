/**
 * 类型定义文件
 */

// ==================== 枚举类型 ====================

export enum UserRole {
  ADMIN = 'admin',
  USER = 'user',
  VIEWER = 'viewer',
}

export enum TaskStatus {
  PENDING = 'pending',
  QUEUED = 'queued',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum TaskComplexity {
  L1_BASIC = 'l1_basic',
  L2_DOMAIN = 'l2_domain',
  L3_COMPLEX = 'l3_complex',
}

export enum ModelType {
  BASE = 'base',
  FINETUNED = 'finetuned',
  LORA_ADAPTER = 'lora_adapter',
}

// ==================== 用户相关 ====================

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ==================== 模型相关 ====================

export interface Model {
  id: number;
  name: string;
  display_name?: string;
  description?: string;
  model_type: ModelType;
  model_path: string;
  model_size?: string;
  parameters_count?: string;
  framework: string;
  is_public: boolean;
  download_count: number;
  owner_id: number;
  created_at: string;
}

export interface ModelCreate {
  name: string;
  display_name?: string;
  description?: string;
  model_type: ModelType;
  model_path: string;
  model_size?: string;
  base_model_id?: number;
}

// ==================== 数据集相关 ====================

export interface Dataset {
  id: number;
  name: string;
  description?: string;
  dataset_path: string;
  dataset_type: string;
  file_format: string;
  total_samples?: number;
  train_samples?: number;
  eval_samples?: number;
  is_validated: boolean;
  owner_id: number;
  created_at: string;
}

export interface DatasetCreate {
  name: string;
  description?: string;
  dataset_type: string;
}

// ==================== 任务相关 ====================

export interface Task {
  id: number;
  task_name: string;
  description?: string;
  status: TaskStatus;
  task_complexity: TaskComplexity;
  task_intent?: string;
  lora_rank?: number;
  lora_alpha?: number;
  learning_rate?: number;
  num_epochs?: number;
  current_epoch?: number;
  current_step?: number;
  total_steps?: number;
  train_loss?: number;
  eval_loss?: number;
  cf_score?: number;
  gpu_memory_used?: number;
  estimated_time?: number;
  output_model_path?: string;
  metrics?: Record<string, any>;
  error_message?: string;
  owner_id: number;
  base_model_id: number;
  dataset_id: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface TaskCreate {
  task_name: string;
  description?: string;
  task_complexity: TaskComplexity;
  task_intent?: string;
  base_model_id: number;
  dataset_id: number;
  output_model_name: string;
  num_epochs?: number;
  batch_size?: number;
  max_length?: number;
}

export interface TaskMetrics {
  epoch: number;
  step: number;
  train_loss: number;
  eval_loss?: number;
  learning_rate: number;
  cf_score?: number;
  gpu_memory?: number;
  timestamp: string;
}

// ==================== 统计信息 ====================

export interface DashboardStats {
  total_tasks: number;
  running_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  total_models: number;
  total_datasets: number;
  total_users: number;
  gpu_usage?: number;
}

export interface SystemHealth {
  status: string;
  database: boolean;
  redis: boolean;
  gpu_available: boolean;
  disk_usage: number;
  memory_usage: number;
  cpu_usage: number;
}

// ==================== API响应 ====================

export interface ApiResponse<T = any> {
  success: boolean;
  message: string;
  data?: T;
}

export interface PaginatedResponse<T = any> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface ErrorResponse {
  error: string;
  detail?: string;
  code?: string;
}

// ==================== 复杂度配置 ====================

export interface ComplexityConfig {
  level: TaskComplexity;
  label: string;
  description: string;
  icon: string;
  color: string;
  rank: string;
  modules: string;
  use_cases: string[];
}

