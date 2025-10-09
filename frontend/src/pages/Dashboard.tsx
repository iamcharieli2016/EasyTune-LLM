/**
 * 仪表板页面
 */

import React, { useEffect, useState } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Tag,
  Space,
  Button,
  Progress,
  Typography,
} from 'antd';
import {
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  CloudUploadOutlined,
  UserOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import ReactECharts from 'echarts-for-react';
import { taskApi } from '../services/api';
import { DashboardStats, Task, TaskStatus } from '../types';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [statsData, tasksData] = await Promise.all([
        taskApi.getStats(),
        taskApi.getTasks(1, 5),
      ]);
      setStats(statsData);
      setRecentTasks(tasksData.items);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusTag = (status: TaskStatus) => {
    const statusConfig = {
      [TaskStatus.RUNNING]: { color: 'processing', text: '运行中' },
      [TaskStatus.COMPLETED]: { color: 'success', text: '已完成' },
      [TaskStatus.FAILED]: { color: 'error', text: '失败' },
      [TaskStatus.PENDING]: { color: 'default', text: '待处理' },
      [TaskStatus.QUEUED]: { color: 'warning', text: '排队中' },
      [TaskStatus.CANCELLED]: { color: 'default', text: '已取消' },
    };
    const config = statusConfig[status];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  const columns = [
    {
      title: '任务名称',
      dataIndex: 'task_name',
      key: 'task_name',
      render: (text: string, record: Task) => (
        <a onClick={() => navigate(`/tasks/${record.id}`)}>{text}</a>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: TaskStatus) => getStatusTag(status),
    },
    {
      title: '进度',
      key: 'progress',
      render: (_: any, record: Task) => {
        if (record.status === TaskStatus.RUNNING && record.current_epoch && record.num_epochs) {
          const progress = (record.current_epoch / record.num_epochs) * 100;
          return <Progress percent={Math.round(progress)} size="small" />;
        }
        return '-';
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Task) => (
        <Button
          type="link"
          size="small"
          onClick={() => navigate(`/tasks/${record.id}`)}
        >
          查看详情
        </Button>
      ),
    },
  ];

  // 任务状态分布图表配置
  const taskDistributionOption = {
    tooltip: {
      trigger: 'item',
    },
    legend: {
      orient: 'vertical',
      left: 'left',
    },
    series: [
      {
        name: '任务状态',
        type: 'pie',
        radius: '50%',
        data: stats
          ? [
              { value: stats.running_tasks, name: '运行中' },
              { value: stats.completed_tasks, name: '已完成' },
              { value: stats.failed_tasks, name: '失败' },
              {
                value:
                  stats.total_tasks -
                  stats.running_tasks -
                  stats.completed_tasks -
                  stats.failed_tasks,
                name: '其他',
              },
            ]
          : [],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
      },
    ],
  };

  return (
    <div className="fade-in">
      <Row gutter={[16, 16]}>
        {/* 统计卡片 */}
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
            <Statistic
              title={<Text style={{ color: 'white' }}>总任务数</Text>}
              value={stats?.total_tasks || 0}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: 'white' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card" style={{ background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)' }}>
            <Statistic
              title={<Text style={{ color: 'white' }}>运行中</Text>}
              value={stats?.running_tasks || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: 'white' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card" style={{ background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)' }}>
            <Statistic
              title={<Text style={{ color: 'white' }}>已完成</Text>}
              value={stats?.completed_tasks || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: 'white' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="stat-card" style={{ background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)' }}>
            <Statistic
              title={<Text style={{ color: 'white' }}>模型数量</Text>}
              value={stats?.total_models || 0}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: 'white' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* 快速操作 */}
        <Col xs={24} lg={8}>
          <Card title="快速操作" className="custom-card">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Button
                type="primary"
                size="large"
                block
                icon={<ThunderboltOutlined />}
                onClick={() => navigate('/tasks/create')}
              >
                创建训练任务
              </Button>
              <Button
                size="large"
                block
                icon={<CloudUploadOutlined />}
                onClick={() => navigate('/datasets')}
              >
                上传数据集
              </Button>
              <Button
                size="large"
                block
                icon={<DatabaseOutlined />}
                onClick={() => navigate('/models')}
              >
                管理模型
              </Button>
            </Space>
          </Card>
        </Col>

        {/* 任务状态分布 */}
        <Col xs={24} lg={16}>
          <Card title="任务状态分布" className="custom-card">
            <ReactECharts option={taskDistributionOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 最近任务 */}
      <Card
        title="最近任务"
        extra={
          <Button
            type="link"
            onClick={() => navigate('/tasks')}
            icon={<ArrowRightOutlined />}
          >
            查看全部
          </Button>
        }
        style={{ marginTop: 16 }}
        className="custom-card"
      >
        <Table
          columns={columns}
          dataSource={recentTasks}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default Dashboard;

