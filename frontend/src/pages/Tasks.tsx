/**
 * 任务列表页面
 */

import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Space, Card, Input, Select, message } from 'antd';
import { PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { taskApi } from '../services/api';
import { Task, TaskStatus } from '../types';

const Tasks: React.FC = () => {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });

  useEffect(() => {
    loadTasks();
  }, [pagination.current]);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await taskApi.getTasks(pagination.current, pagination.pageSize);
      setTasks(response.items);
      setPagination({ ...pagination, total: response.total });
    } catch (error) {
      message.error('加载任务列表失败');
    } finally {
      setLoading(false);
    }
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
      render: (_: any, record: Task) => (
        <Button type="link" onClick={() => navigate(`/tasks/${record.id}`)}>
          查看详情
        </Button>
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

