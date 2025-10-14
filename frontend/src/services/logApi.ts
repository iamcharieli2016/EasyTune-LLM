/**
 * 训练日志API服务
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// 创建axios实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// 添加请求拦截器，自动添加token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export interface TrainingLog {
  task_id: number;
  filename: string;
  size: number;
  size_human: string;
  modified_at: number;
}

export interface TrainingLogContent {
  task_id: number;
  content: string;
  lines: number;
}

export const logApi = {
  /**
   * 列出所有训练日志
   */
  listLogs: async (): Promise<{ logs: TrainingLog[] }> => {
    const response = await apiClient.get('/logs/list');
    return response.data;
  },

  /**
   * 获取指定任务的训练日志
   */
  getLog: async (taskId: number, tail?: number): Promise<TrainingLogContent> => {
    const params = tail ? { tail } : {};
    const response = await apiClient.get(`/logs/${taskId}`, { params });
    return response.data;
  },

  /**
   * 下载训练日志
   */
  downloadLog: (taskId: number): string => {
    const token = localStorage.getItem('access_token');
    return `${API_BASE_URL}/logs/${taskId}/download?token=${token}`;
  },

  /**
   * 删除训练日志
   */
  deleteLog: async (taskId: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/logs/${taskId}`);
    return response.data;
  },
};

