import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Descriptions, 
  Tag, 
  Progress, 
  Space, 
  Button, 
  Spin, 
  Alert,
  Row,
  Col,
  Statistic,
  Timeline,
  message,
  Modal
} from 'antd';
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  SyncOutlined,
  CloseCircleOutlined,
  RocketOutlined,
  LineChartOutlined,
  StopOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { taskApi } from '../services/api';
import { Task, TaskStatus, TaskComplexity } from '../types';
import TrainingLogViewer from '../components/TrainingLogViewer';
import { formatApiError } from '../utils/errorHandler';

const TaskDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(true);
  const [logViewerVisible, setLogViewerVisible] = useState(false);

  useEffect(() => {
    loadTask(true); // 首次加载显示loading
    // 如果任务正在运行，每5秒刷新一次
    const interval = setInterval(() => {
      if (task?.status === TaskStatus.RUNNING || task?.status === TaskStatus.PENDING) {
        loadTask(false); // 自动刷新不显示loading，避免闪烁
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [id, task?.status]);

  const loadTask = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true);
      }
      const data = await taskApi.getTask(Number(id));
      setTask(data);
    } catch (error: any) {
      message.error(error.response?.data?.message || '加载任务详情失败');
    } finally {
      if (showLoading) {
        setLoading(false);
      }
    }
  };

  const getStatusConfig = (status: TaskStatus) => {
    const configs: Record<TaskStatus, { icon: React.ReactElement; color: string; text: string }> = {
      [TaskStatus.PENDING]: { 
        icon: <ClockCircleOutlined />, 
        color: 'default', 
        text: '等待中' 
      },
      [TaskStatus.QUEUED]: { 
        icon: <ClockCircleOutlined />, 
        color: 'default', 
        text: '队列中' 
      },
      [TaskStatus.RUNNING]: { 
        icon: <SyncOutlined spin />, 
        color: 'processing', 
        text: '运行中' 
      },
      [TaskStatus.COMPLETED]: { 
        icon: <CheckCircleOutlined />, 
        color: 'success', 
        text: '已完成' 
      },
      [TaskStatus.FAILED]: { 
        icon: <CloseCircleOutlined />, 
        color: 'error', 
        text: '失败' 
      },
      [TaskStatus.CANCELLED]: { 
        icon: <CloseCircleOutlined />, 
        color: 'default', 
        text: '已取消' 
      },
    };
    return configs[status] || configs[TaskStatus.PENDING];
  };

  const getComplexityText = (complexity: TaskComplexity) => {
    const map: Record<TaskComplexity, string> = {
      [TaskComplexity.L1_BASIC]: 'L1-基础调整',
      [TaskComplexity.L2_DOMAIN]: 'L2-领域微调',
      [TaskComplexity.L3_COMPLEX]: 'L3-复杂微调',
    };
    return map[complexity] || complexity;
  };

  const handleStopTask = async () => {
    Modal.confirm({
      title: '确认停止任务',
      icon: <ExclamationCircleOutlined />,
      content: `确定要停止训练任务"${task?.task_name}"吗？此操作不可恢复。`,
      okText: '确认停止',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await taskApi.stopTask(Number(id));
          message.success('任务已停止');
          loadTask(true); // 重新加载任务状态
        } catch (error: any) {
          const errorMsg = formatApiError(error, '停止任务失败');
          message.error(errorMsg);
        }
      },
    });
  };

  const handleDeleteTask = async () => {
    Modal.confirm({
      title: '确认删除任务',
      icon: <ExclamationCircleOutlined />,
      content: (
        <div>
          <p>确定要删除训练任务"{task?.task_name}"吗？</p>
          <p style={{ color: 'red' }}>警告：此操作将永久删除任务记录，不可恢复！</p>
          {(task?.status === TaskStatus.RUNNING || task?.status === TaskStatus.PENDING) && (
            <p style={{ color: 'orange' }}>注意：任务正在运行，将被强制停止。</p>
          )}
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          const force = task?.status === TaskStatus.RUNNING || task?.status === TaskStatus.PENDING;
          await taskApi.deleteTask(Number(id), force);
          message.success('任务已删除');
          navigate('/tasks'); // 跳转到任务列表
        } catch (error: any) {
          const errorMsg = formatApiError(error, '删除任务失败');
          message.error(errorMsg);
        }
      },
    });
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  if (!task) {
    return (
      <Alert
        message="任务不存在"
        description="未找到指定的训练任务"
        type="error"
        showIcon
      />
    );
  }

  const statusConfig = getStatusConfig(task.status);
  const progress = (task.num_epochs && task.num_epochs > 0) 
    ? Math.round(((task.current_epoch || 0) / task.num_epochs) * 100) 
    : 0;

  return (
    <div>
      {/* 顶部状态栏 */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="任务状态"
              value={statusConfig.text}
              prefix={statusConfig.icon}
              valueStyle={{ color: statusConfig.color === 'success' ? '#3f8600' : 
                                    statusConfig.color === 'error' ? '#cf1322' :
                                    statusConfig.color === 'processing' ? '#1890ff' : '#000' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="训练进度"
              value={progress}
              suffix="%"
              prefix={<RocketOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="当前轮次"
              value={`${task.current_epoch}/${task.num_epochs}`}
              prefix={<SyncOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="CF分数"
              value={task.cf_score ? task.cf_score.toFixed(4) : '-'}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: task.cf_score && task.cf_score > 0.9 ? '#3f8600' : '#000' }}
            />
          </Col>
        </Row>
        
        {/* 快捷操作 */}
        <div style={{ marginTop: 16, textAlign: 'center' }}>
          <Button 
            type="link" 
            onClick={() => setLogViewerVisible(true)}
            style={{ fontSize: 16 }}
          >
            📋 查看训练日志 →
          </Button>
        </div>
      </Card>

      {/* 训练进度 */}
      {task.status === TaskStatus.RUNNING && (
        <Card title="训练进度" style={{ marginBottom: 16 }}>
          <Progress 
            percent={progress} 
            status={progress === 100 ? 'success' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <div style={{ marginTop: 16 }}>
            <Space size="large">
              {task.train_loss !== null && task.train_loss !== undefined && (
                <span>训练损失: <strong>{task.train_loss.toFixed(4)}</strong></span>
              )}
              {task.eval_loss !== null && task.eval_loss !== undefined && (
                <span>验证损失: <strong>{task.eval_loss.toFixed(4)}</strong></span>
              )}
            </Space>
          </div>
        </Card>
      )}

      {/* 错误信息 */}
      {task.status === TaskStatus.FAILED && task.error_message && (
        <Alert
          message="训练失败"
          description={task.error_message}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 基本信息 */}
      <Card title="基本信息" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="任务名称" span={2}>
            {task.task_name}
          </Descriptions.Item>
          <Descriptions.Item label="任务描述" span={2}>
            {task.description || '无'}
          </Descriptions.Item>
          <Descriptions.Item label="任务复杂度">
            <Tag color="blue">{getComplexityText(task.task_complexity)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="训练意图">
            {task.task_intent || '无'}
          </Descriptions.Item>
          <Descriptions.Item label="基座模型ID">
            {task.base_model_id}
          </Descriptions.Item>
          <Descriptions.Item label="数据集ID">
            {task.dataset_id}
          </Descriptions.Item>
          <Descriptions.Item label="输出路径" span={2}>
            {task.output_model_path || '待生成'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 训练配置 */}
      <Card title="训练配置" style={{ marginBottom: 16 }}>
        <Descriptions column={2} bordered>
          <Descriptions.Item label="训练轮数">
            {task.num_epochs || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="学习率">
            {task.learning_rate || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="LoRA Rank">
            {task.lora_rank || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="LoRA Alpha">
            {task.lora_alpha || '-'}
          </Descriptions.Item>
          <Descriptions.Item label="当前步数">
            {task.current_step ? `${task.current_step}/${task.total_steps || '?'}` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="GPU内存">
            {task.gpu_memory_used ? `${task.gpu_memory_used} MB` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="预计时间">
            {task.estimated_time ? `${Math.round(task.estimated_time / 60)} 分钟` : '-'}
          </Descriptions.Item>
          <Descriptions.Item label="任务意图">
            {task.task_intent || '-'}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      {/* 训练结果 */}
      {task.status === TaskStatus.COMPLETED && (
        <Card title="训练结果" style={{ marginBottom: 16 }}>
          <Descriptions column={2} bordered>
            <Descriptions.Item label="训练损失">
              {task.train_loss?.toFixed(4) || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="验证损失">
              {task.eval_loss?.toFixed(4) || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="CF分数">
              <Tag color={task.cf_score && task.cf_score > 0.9 ? 'green' : 'orange'}>
                {task.cf_score?.toFixed(4) || '-'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="输出路径">
              {task.output_model_path || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="完成时间" span={2}>
              {task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '-'}
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {/* 时间线 */}
      <Card title="时间线">
        <Timeline>
          <Timeline.Item color="green">
            <p>任务创建</p>
            <p style={{ fontSize: 12, color: '#999' }}>
              {new Date(task.created_at).toLocaleString('zh-CN')}
            </p>
          </Timeline.Item>
          
          {task.status !== TaskStatus.PENDING && (
            <Timeline.Item 
              color={task.status === TaskStatus.RUNNING ? 'blue' : 'green'}
              dot={task.status === TaskStatus.RUNNING ? <SyncOutlined spin /> : undefined}
            >
              <p>开始训练</p>
              <p style={{ fontSize: 12, color: '#999' }}>
                {task.status === TaskStatus.RUNNING ? '进行中...' : '已开始'}
              </p>
            </Timeline.Item>
          )}
          
          {task.status === TaskStatus.COMPLETED && (
            <Timeline.Item color="green" dot={<CheckCircleOutlined />}>
              <p>训练完成</p>
              <p style={{ fontSize: 12, color: '#999' }}>
                {task.completed_at ? new Date(task.completed_at).toLocaleString('zh-CN') : '-'}
              </p>
            </Timeline.Item>
          )}
          
          {task.status === TaskStatus.FAILED && (
            <Timeline.Item color="red" dot={<CloseCircleOutlined />}>
              <p>训练失败</p>
              <p style={{ fontSize: 12, color: '#999' }}>
                {task.error_message}
              </p>
            </Timeline.Item>
          )}
        </Timeline>
      </Card>

      {/* 操作按钮 */}
      <div style={{ marginTop: 16, textAlign: 'right' }}>
        <Space>
          <Button onClick={() => navigate('/tasks')}>
            返回列表
          </Button>
          <Button onClick={() => setLogViewerVisible(true)}>
            📋 查看日志
          </Button>
          
          {/* 停止按钮 - 只在运行中或待处理时显示 */}
          {(task.status === TaskStatus.RUNNING || task.status === TaskStatus.PENDING) && (
            <Button 
              icon={<StopOutlined />}
              onClick={handleStopTask}
              danger
            >
              停止任务
            </Button>
          )}
          
          {/* 删除按钮 - 不在运行中可以直接删除 */}
          <Button 
            icon={<DeleteOutlined />}
            onClick={handleDeleteTask}
            danger={task.status === TaskStatus.RUNNING || task.status === TaskStatus.PENDING}
            type={task.status === TaskStatus.RUNNING || task.status === TaskStatus.PENDING ? 'default' : 'dashed'}
          >
            删除任务
          </Button>
          
          <Button type="primary" onClick={() => loadTask(true)}>
            刷新
          </Button>
        </Space>
      </div>

      {/* 日志查看器 */}
      {task && (
        <TrainingLogViewer
          visible={logViewerVisible}
          taskId={task.id}
          taskName={task.task_name}
          onClose={() => setLogViewerVisible(false)}
        />
      )}
    </div>
  );
};

export default TaskDetail;

