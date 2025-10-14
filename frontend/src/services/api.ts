/**
 * API服务层
 * 封装所有HTTP请求
 */

import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import {
  User,
  LoginCredentials,
  RegisterData,
  AuthTokens,
  Model,
  ModelCreate,
  Dataset,
  Task,
  TaskCreate,
  DashboardStats,
  ApiResponse,
  PaginatedResponse,
} from '../types';

// 创建axios实例
const api: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器 - 添加Token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理错误
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token过期，尝试刷新
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(
            `${process.env.REACT_APP_API_URL}/auth/refresh`,
            { refresh_token: refreshToken }
          );
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          // 重试原请求
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${access_token}`;
            return axios.request(error.config);
          }
        } catch {
          // 刷新失败，跳转到登录页
          localStorage.clear();
          window.location.href = '/login';
        }
      } else {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ==================== 认证相关 ====================

export const authApi = {
  // 登录
  login: async (credentials: LoginCredentials): Promise<AuthTokens> => {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    const response = await api.post<AuthTokens>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  // 注册
  register: async (data: RegisterData): Promise<ApiResponse> => {
    const response = await api.post<ApiResponse>('/auth/register', data);
    return response.data;
  },

  // 获取当前用户
  getCurrentUser: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  // 登出
  logout: async (): Promise<ApiResponse> => {
    const response = await api.post<ApiResponse>('/auth/logout');
    return response.data;
  },
};

// ==================== 用户管理 ====================

export const userApi = {
  // 获取用户列表
  getUsers: async (page = 1, pageSize = 20): Promise<PaginatedResponse<User>> => {
    const response = await api.get<PaginatedResponse<User>>('/users', {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  // 获取用户详情
  getUser: async (id: number): Promise<User> => {
    const response = await api.get<User>(`/users/${id}`);
    return response.data;
  },
};

// ==================== 模型管理 ====================

export const modelApi = {
  // 获取模型列表
  getModels: async (
    page = 1,
    pageSize = 20,
    filters?: { model_type?: string; search?: string }
  ): Promise<PaginatedResponse<Model>> => {
    const response = await api.get<PaginatedResponse<Model>>('/models', {
      params: { page, page_size: pageSize, ...filters },
    });
    return response.data;
  },

  // 获取模型详情
  getModel: async (id: number): Promise<Model> => {
    const response = await api.get<Model>(`/models/${id}`);
    return response.data;
  },

  // 创建模型
  createModel: async (data: ModelCreate): Promise<Model> => {
    const response = await api.post<Model>('/models', data);
    return response.data;
  },

  // 删除模型
  deleteModel: async (id: number): Promise<ApiResponse> => {
    const response = await api.delete<ApiResponse>(`/models/${id}`);
    return response.data;
  },
};

// ==================== 数据集管理 ====================

export const datasetApi = {
  // 获取数据集列表
  getDatasets: async (
    page = 1,
    pageSize = 20,
    search?: string
  ): Promise<PaginatedResponse<Dataset>> => {
    const response = await api.get<PaginatedResponse<Dataset>>('/datasets', {
      params: { page, page_size: pageSize, search },
    });
    return response.data;
  },

  // 获取数据集详情
  getDataset: async (id: number): Promise<Dataset> => {
    const response = await api.get<Dataset>(`/datasets/${id}`);
    return response.data;
  },

  // 上传数据集
  upload: async (formData: FormData): Promise<ApiResponse<Dataset>> => {
    const response = await api.post<ApiResponse<Dataset>>('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  uploadDataset: async (
    file: File,
    name: string,
    description?: string,
    datasetType?: string
  ): Promise<Dataset> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', name);
    if (description) formData.append('description', description);
    if (datasetType) formData.append('dataset_type', datasetType);

    const response = await api.post<Dataset>('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  // 预览数据集
  previewDataset: async (id: number, limit = 10) => {
    const response = await api.get(`/datasets/${id}/preview`, {
      params: { limit },
    });
    return response.data;
  },

  // 删除数据集
  delete: async (id: number): Promise<ApiResponse> => {
    const response = await api.delete<ApiResponse>(`/datasets/${id}`);
    return response.data;
  },

  deleteDataset: async (id: number): Promise<ApiResponse> => {
    const response = await api.delete<ApiResponse>(`/datasets/${id}`);
    return response.data;
  },
};

// ==================== 任务管理 ====================

export const taskApi = {
  // 获取仪表板统计
  getStats: async (): Promise<DashboardStats> => {
    const response = await api.get<DashboardStats>('/tasks/stats');
    return response.data;
  },

  // 获取任务列表
  getTasks: async (
    page = 1,
    pageSize = 20,
    statusFilter?: string
  ): Promise<PaginatedResponse<Task>> => {
    const response = await api.get<PaginatedResponse<Task>>('/tasks', {
      params: { page, page_size: pageSize, status_filter: statusFilter },
    });
    return response.data;
  },

  // 获取任务详情
  getTask: async (id: number): Promise<Task> => {
    const response = await api.get<Task>(`/tasks/${id}`);
    return response.data;
  },

  // 创建任务
  createTask: async (data: TaskCreate): Promise<Task> => {
    const response = await api.post<Task>('/tasks', data);
    return response.data;
  },

  // 取消任务
  cancelTask: async (id: number): Promise<ApiResponse> => {
    const response = await api.post<ApiResponse>(`/tasks/${id}/cancel`);
    return response.data;
  },

  // 删除任务
  deleteTask: async (id: number, force: boolean = false): Promise<ApiResponse> => {
    const response = await api.delete<ApiResponse>(`/tasks/${id}`, {
      params: { force }
    });
    return response.data;
  },
  
  // 停止任务
  stopTask: async (id: number, force: boolean = false): Promise<ApiResponse> => {
    const response = await api.post<ApiResponse>(`/tasks/${id}/stop`, null, {
      params: { force }
    });
    return response.data;
  },
  
  // 获取任务进程状态
  getTaskProcess: async (id: number): Promise<any> => {
    const response = await api.get<any>(`/tasks/${id}/process`);
    return response.data;
  },

  // 获取任务日志
  getTaskLogs: async (id: number) => {
    const response = await api.get(`/tasks/${id}/logs`);
    return response.data;
  },
};

export default api;

