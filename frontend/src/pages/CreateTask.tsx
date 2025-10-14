/**
 * 创建任务页面 - 意图驱动的四步配置向导
 */

import React, { useState, useEffect } from 'react';
import {
  Steps,
  Card,
  Form,
  Input,
  Select,
  Button,
  Radio,
  Space,
  Typography,
  Divider,
  message,
  Row,
  Col,
  Tag,
  Alert,
} from 'antd';
import {
  ThunderboltOutlined,
  DatabaseOutlined,
  CloudUploadOutlined,
  SettingOutlined,
  RocketOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { modelApi, datasetApi, taskApi } from '../services/api';
import { Model, Dataset, TaskComplexity, TaskCreate } from '../types';
import { formatApiError } from '../utils/errorHandler';
import './CreateTask.css';

const { Step } = Steps;
const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

// 复杂度配置
const complexityConfigs = [
  {
    level: TaskComplexity.L1_BASIC,
    label: 'L1 - 基础风格调整',
    description: '改变语气或格式，无需注入新知识',
    icon: '🎨',
    color: '#52c41a',
    rank: '4-8',
    modules: 'QKV Layers',
    useCases: ['语气风格调整', '格式统一', '简单对话优化'],
  },
  {
    level: TaskComplexity.L2_DOMAIN,
    label: 'L2 - 领域知识注入',
    description: '适配特定领域词汇，进行简单QA任务',
    icon: '📚',
    color: '#1890ff',
    rank: '8-16',
    modules: 'QKV + FFN Layers',
    useCases: ['垂直领域适配', '专业术语学习', '知识问答'],
  },
  {
    level: TaskComplexity.L3_COMPLEX,
    label: 'L3 - 复杂指令重塑',
    description: '提升复杂指令遵循能力、代码生成等',
    icon: '🚀',
    color: '#722ed1',
    rank: '16-32',
    modules: 'All Attention + FFN',
    useCases: ['复杂推理', '代码生成', '多步骤任务'],
  },
];

const CreateTask: React.FC = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState<Model[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedComplexity, setSelectedComplexity] = useState<TaskComplexity>(
    TaskComplexity.L2_DOMAIN
  );

  useEffect(() => {
    loadModels();
    loadDatasets();
  }, []);

  const loadModels = async () => {
    try {
      const response = await modelApi.getModels(1, 100);
      setModels(response.items.filter((m) => m.model_type === 'base'));
    } catch (error) {
      message.error('加载模型列表失败');
    }
  };

  const loadDatasets = async () => {
    try {
      const response = await datasetApi.getDatasets(1, 100);
      setDatasets(response.items.filter((d) => d.is_validated));
    } catch (error) {
      message.error('加载数据集列表失败');
    }
  };

  const next = () => {
    form
      .validateFields()
      .then(() => {
        setCurrent(current + 1);
      })
      .catch(() => {
        message.warning('请完成当前步骤的必填项');
      });
  };

  const prev = () => {
    setCurrent(current - 1);
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      
      // 获取所有字段值（包括隐藏的步骤）
      const allValues = form.getFieldsValue(true);
      console.log('📊 表单所有值:', allValues);
      
      // 验证必填字段
      await form.validateFields();
      
      const taskData: TaskCreate = {
        task_name: allValues.task_name,
        description: allValues.description,
        task_complexity: allValues.task_complexity,
        task_intent: allValues.task_intent,
        base_model_id: allValues.base_model_id,
        dataset_id: allValues.dataset_id,
        output_model_name: allValues.output_model_name,
        num_epochs: allValues.num_epochs || 3,
      };

      console.log('📤 提交的任务数据:', taskData);

      const task = await taskApi.createTask(taskData);
      message.success('任务创建成功！');
      navigate(`/tasks/${task.id}`);
    } catch (error: any) {
      const errorMsg = formatApiError(error, '任务创建失败');
      message.error(errorMsg);
      console.error('创建任务失败:', error.response?.data);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    {
      title: '选择模型与数据',
      icon: <DatabaseOutlined />,
    },
    {
      title: '意图驱动配置',
      icon: <SettingOutlined />,
    },
    {
      title: '高级设置',
      icon: <ThunderboltOutlined />,
    },
    {
      title: '确认创建',
      icon: <RocketOutlined />,
    },
  ];

  return (
    <div className="create-task-container fade-in">
      <Card className="custom-card">
        <Title level={2}>
          <ThunderboltOutlined /> 创建训练任务
        </Title>
        <Paragraph type="secondary">
          通过意图驱动的四步配置向导，轻松完成模型微调
        </Paragraph>

        <Steps current={current} style={{ marginTop: 32, marginBottom: 32 }}>
          {steps.map((item) => (
            <Step key={item.title} title={item.title} icon={item.icon} />
          ))}
        </Steps>

        <Form 
          form={form} 
          layout="vertical" 
          preserve={true}
          initialValues={{ task_complexity: TaskComplexity.L2_DOMAIN, num_epochs: 3 }}
        >
          {/* 步骤1：选择模型与数据 */}
          {current === 0 && (
            <div className="step-content">
              <Alert
                message="第一步：选择基座模型和训练数据集"
                description="请选择您要微调的基座模型和用于训练的数据集"
                type="info"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form.Item
                label="任务名称"
                name="task_name"
                rules={[{ required: true, message: '请输入任务名称' }]}
              >
                <Input placeholder="为您的微调任务起一个名字" size="large" />
              </Form.Item>

              <Form.Item
                label="任务描述"
                name="description"
              >
                <TextArea rows={3} placeholder="简单描述一下训练目标（可选）" />
              </Form.Item>

              <Form.Item
                label="基座模型"
                name="base_model_id"
                rules={[{ required: true, message: '请选择基座模型' }]}
              >
                <Select
                  placeholder="选择基座模型"
                  size="large"
                  showSearch
                  optionFilterProp="children"
                >
                  {models.map((model) => (
                    <Select.Option key={model.id} value={model.id}>
                      <Space>
                        <DatabaseOutlined />
                        {model.display_name || model.name}
                        {model.model_size && <Tag>{model.model_size}</Tag>}
                      </Space>
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                label="训练数据集"
                name="dataset_id"
                rules={[{ required: true, message: '请选择数据集' }]}
              >
                <Select
                  placeholder="选择训练数据集"
                  size="large"
                  showSearch
                  optionFilterProp="children"
                >
                  {datasets.map((dataset) => (
                    <Select.Option key={dataset.id} value={dataset.id}>
                      <Space>
                        <CloudUploadOutlined />
                        {dataset.name}
                        <Tag color="blue">{dataset.total_samples} 样本</Tag>
                      </Space>
                    </Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </div>
          )}

          {/* 步骤2：意图驱动配置 */}
          {current === 1 && (
            <div className="step-content">
              <Alert
                message="第二步：告诉我们您的训练意图"
                description="平台将根据您选择的复杂度自动配置所有LoRA参数"
                type="success"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form.Item
                label="训练意图描述"
                name="task_intent"
              >
                <TextArea
                  rows={4}
                  placeholder="请描述您希望模型学到什么能力，例如：&#10;- 我希望模型能够回答医疗领域的专业问题&#10;- 我希望模型的回复风格更加幽默&#10;- 我希望模型能够生成高质量的Python代码"
                />
              </Form.Item>

              <Form.Item
                label="任务复杂度"
                name="task_complexity"
                rules={[{ required: true }]}
              >
                <Radio.Group
                  onChange={(e) => setSelectedComplexity(e.target.value)}
                  style={{ width: '100%' }}
                >
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    {complexityConfigs.map((config) => (
                      <Card
                        key={config.level}
                        className={`complexity-card ${
                          selectedComplexity === config.level ? 'selected' : ''
                        }`}
                        onClick={() => {
                          form.setFieldsValue({ task_complexity: config.level });
                          setSelectedComplexity(config.level);
                        }}
                      >
                        <Radio value={config.level} style={{ width: '100%' }}>
                          <Row gutter={16} align="middle">
                            <Col>
                              <span className="complexity-icon">{config.icon}</span>
                            </Col>
                            <Col flex={1}>
                              <Title level={4} style={{ margin: 0 }}>
                                {config.label}
                              </Title>
                              <Paragraph type="secondary" style={{ margin: '8px 0' }}>
                                {config.description}
                              </Paragraph>
                              <Space wrap>
                                <Tag color={config.color}>Rank: {config.rank}</Tag>
                                <Tag>模块: {config.modules}</Tag>
                              </Space>
                              <div style={{ marginTop: 8 }}>
                                <Text type="secondary" strong>
                                  适用场景：
                                </Text>
                                {config.useCases.map((useCase, idx) => (
                                  <Tag key={idx} style={{ margin: '4px 4px 4px 0' }}>
                                    {useCase}
                                  </Tag>
                                ))}
                              </div>
                            </Col>
                          </Row>
                        </Radio>
                      </Card>
                    ))}
                  </Space>
                </Radio.Group>
              </Form.Item>
            </div>
          )}

          {/* 步骤3：高级设置 */}
          {current === 2 && (
            <div className="step-content">
              <Alert
                message="第三步：高级设置（可选）"
                description="对于大多数情况，默认值已经足够好了"
                type="warning"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Form.Item
                label="输出模型名称"
                name="output_model_name"
                rules={[{ required: true, message: '请输入输出模型名称' }]}
              >
                <Input placeholder="微调后的模型名称" size="large" />
              </Form.Item>

              <Form.Item
                label="训练轮数"
                name="num_epochs"
                tooltip="一般1-5轮即可，过多可能导致过拟合"
              >
                <Select size="large">
                  <Select.Option value={1}>1 轮（快速验证）</Select.Option>
                  <Select.Option value={2}>2 轮</Select.Option>
                  <Select.Option value={3}>3 轮（推荐）</Select.Option>
                  <Select.Option value={5}>5 轮</Select.Option>
                  <Select.Option value={10}>10 轮（深度训练）</Select.Option>
                </Select>
              </Form.Item>
            </div>
          )}

          {/* 步骤4：确认创建 */}
          {current === 3 && (
            <div className="step-content">
              <Alert
                message="准备就绪！"
                description="请确认以下配置，点击开始训练启动任务"
                type="success"
                showIcon
                style={{ marginBottom: 24 }}
              />

              <Card>
                <Title level={4}>任务配置总览</Title>
                <Divider />
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text strong>任务名称：</Text>
                    <br />
                    <Text>{form.getFieldValue('task_name')}</Text>
                  </Col>
                  <Col span={12}>
                    <Text strong>任务复杂度：</Text>
                    <br />
                    <Tag color={complexityConfigs.find((c) => c.level === selectedComplexity)?.color}>
                      {complexityConfigs.find((c) => c.level === selectedComplexity)?.label}
                    </Tag>
                  </Col>
                  <Col span={12}>
                    <Text strong>训练轮数：</Text>
                    <br />
                    <Text>{form.getFieldValue('num_epochs')} 轮</Text>
                  </Col>
                  <Col span={12}>
                    <Text strong>输出模型：</Text>
                    <br />
                    <Text>{form.getFieldValue('output_model_name')}</Text>
                  </Col>
                </Row>
              </Card>
            </div>
          )}
        </Form>

        <Divider />

        <div className="steps-action">
          {current > 0 && (
            <Button size="large" onClick={prev}>
              上一步
            </Button>
          )}
          {current < steps.length - 1 && (
            <Button type="primary" size="large" onClick={next}>
              下一步
            </Button>
          )}
          {current === steps.length - 1 && (
            <Button
              type="primary"
              size="large"
              icon={<RocketOutlined />}
              onClick={handleSubmit}
              loading={loading}
              className="gradient-button"
            >
              开始训练
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};

export default CreateTask;

