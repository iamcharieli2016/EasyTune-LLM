/**
 * 任务列表页面
 */

import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Space, Card, message, Modal } from 'antd';
import { PlusOutlined, StopOutlined, DeleteOutlined, EyeOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { taskApi } from '../services/api';
import { Task, TaskStatus } from '../types';
import { formatApiError } from '../utils/errorHandler';

const Tasks: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  useEffect(() => {
    loadTasks(true); // 首次加载显示loading
    
    // 自动刷新（每10秒，不显示loading）
    const interval = setInterval(() => {
      loadTasks(false);
    }, 10000);
    
    return () => clearInterval(interval);
  }, [pagination.current]);

  const loadTasks = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      const response = await taskApi.getTasks(pagination.current, pagination.pageSize);
      setTasks(response.items);
      setPagination({ ...pagination, total: response.total });
    } catch (error) {
      message.error('加载任务列表失败');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const handleStopTask = async (task: Task) => {
    Modal.confirm({
      title: '确认停止任务',
      icon: <ExclamationCircleOutlined />,
      content: `确定要停止训练任务"${task.task_name}"吗？此操作不可恢复。`,
      okText: '确认停止',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await taskApi.stopTask(task.id);
          message.success('任务已停止');
          loadTasks(true);
        } catch (error: any) {
          const errorMsg = formatApiError(error, '停止任务失败');
          message.error(errorMsg);
        }
      },
    });
  };

  const handleDeleteTask = async (task: Task) => {
    Modal.confirm({
      title: '确认删除任务',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要删除训练任务"{task.task_name}"吗？</p>
          <p style={{ color: 'red' }}>警告：此操作将永久删除任务记录，不可恢复！</p>
          {(task.status === TaskStatus.RUNNING || task.status === TaskStatus.PENDING) && (
            <p style={{ color: 'orange' }}>注意：任务正在运行，将被强制停止。</p>
          )}
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const force = task.status === TaskStatus.RUNNING || task.status === TaskStatus.PENDING;
          await taskApi.deleteTask(task.id, force);
          message.success('任务已删除');
          loadTasks(true);
        } catch (error: any) {
          const errorMsg = formatApiError(error, '删除任务失败');
          message.error(errorMsg);
        }
      },
    });
  };

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: TaskStatus) => {
        const colors: Record<TaskStatus, string> = {
          [TaskStatus.PENDING]: 'default',
          [TaskStatus.QUEUED]: 'warning',
          [TaskStatus.RUNNING]: 'processing',
          [TaskStatus.COMPLETED]: 'success',
          [TaskStatus.FAILED]: 'error',
          [TaskStatus.CANCELLED]: 'default',
        };
        return <Tag color={colors[status]}>{status}</Tag>;
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      render: (_: any, record: Task) => (
        <Space size="small">
          <Button 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => navigate(`/tasks/${record.id}`)}
          >
            查看
          </Button>
          
          {/* 停止按钮 - 只在运行中或待处理时显示 */}
          {(record.status === TaskStatus.RUNNING || record.status === TaskStatus.PENDING) && (
            <Button 
              type="link"
              icon={<StopOutlined />}
              onClick={() => handleStopTask(record)}
              danger
            >
              停止
            </Button>
          )}
          
          {/* 删除按钮 */}
          <Button 
            type="link"
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteTask(record)}
            danger
          >
            删除
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card>
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/tasks/create')}
          >
            创建任务
          </Button>
        </Space>

        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="id"
          loading={loading}
          pagination={pagination}
          onChange={(newPagination) => setPagination(newPagination as any)}
        />
      </Card>
    </div>
  );
};

export default Tasks;

