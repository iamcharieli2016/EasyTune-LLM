/**
 * 模型管理页面
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  message,
  Space,
  Tag,
  Popconfirm,
  Descriptions,
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined,
} from '@ant-design/icons';
import { modelApi } from '../services/api';
import { Model, ModelType } from '../types';

const { TextArea } = Input;
const { Option } = Select;

const Models: React.FC = () => {
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [form] = Form.useForm();

  // 加载模型列表
  const loadModels = async () => {
    setLoading(true);
    try {
      const response = await modelApi.getModels();
      setModels(response.items || []);
    } catch (error: any) {
      message.error(error.response?.data?.message || '加载模型列表失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadModels();
  }, []);

  // 添加模型
  const handleAdd = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);
      
      // 处理自定义路径
      const modelPath = values.model_path === 'custom' 
        ? values.custom_path 
        : values.model_path;
      
      await modelApi.createModel({
        name: values.name,
        model_path: modelPath,
        model_type: ModelType.BASE,
        description: values.description,
        model_size: values.parameter_size,
      });
      
      message.success('模型添加成功！');
      setModalVisible(false);
      form.resetFields();
      loadModels();
    } catch (error: any) {
      message.error(error.response?.data?.message || '添加失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除模型
  const handleDelete = async (id: number) => {
    try {
      await modelApi.deleteModel(id);
      message.success('删除成功');
      loadModels();
    } catch (error: any) {
      message.error(error.response?.data?.message || '删除失败');
    }
  };

  // 查看详情
  const handleViewDetail = (model: Model) => {
    setSelectedModel(model);
    setDetailModalVisible(true);
  };

  // 预设的基座模型
  const baseModelOptions = [
    {
      label: 'Qwen/Qwen2-7B',
      value: 'Qwen/Qwen2-7B',
      params: '7B',
    },
    {
      label: 'Qwen/Qwen2-1.5B',
      value: 'Qwen/Qwen2-1.5B',
      params: '1.5B',
    },
    {
      label: 'THUDM/chatglm3-6b',
      value: 'THUDM/chatglm3-6b',
      params: '6B',
    },
    {
      label: 'baichuan-inc/Baichuan2-7B-Chat',
      value: 'baichuan-inc/Baichuan2-7B-Chat',
      params: '7B',
    },
    {
      label: 'meta-llama/Llama-2-7b-hf',
      value: 'meta-llama/Llama-2-7b-hf',
      params: '7B',
    },
    {
      label: '自定义模型路径',
      value: 'custom',
      params: '-',
    },
  ];

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '模型路径',
      dataIndex: 'model_path',
      key: 'model_path',
      ellipsis: true,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: ModelType) => {
        const typeMap: Record<ModelType, { text: string; color: string }> = {
          [ModelType.BASE]: { text: '基座模型', color: 'blue' },
          [ModelType.FINETUNED]: { text: '微调模型', color: 'green' },
          [ModelType.LORA_ADAPTER]: { text: 'LoRA适配器', color: 'purple' },
        };
        const config = typeMap[type] || { text: '未知', color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '参数量',
      dataIndex: 'parameter_size',
      key: 'parameter_size',
      render: (size: string) => size || '-',
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
      width: 200,
      render: (_: any, record: Model) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetail(record)}
          >
            详情
          </Button>
          {(record.model_type === ModelType.FINETUNED || record.model_type === ModelType.LORA_ADAPTER) && (
            <Button
              type="link"
              icon={<DownloadOutlined />}
            >
              下载
            </Button>
          )}
          <Popconfirm
            title="确定要删除这个模型吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Card
        title="模型管理"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setModalVisible(true)}
          >
            添加基座模型
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={models}
          rowKey="id"
          loading={loading}
          pagination={{
            total: models.length,
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个模型`,
          }}
        />
      </Card>

      {/* 添加模型模态框 */}
      <Modal
        title="添加基座模型"
        open={modalVisible}
        onOk={handleAdd}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        confirmLoading={loading}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="选择模型"
            name="model_path"
            rules={[{ required: true, message: '请选择或输入模型路径' }]}
          >
            <Select
              placeholder="请选择预设模型或自定义路径"
              showSearch
              optionFilterProp="label"
            >
              {baseModelOptions.map((option) => (
                <Option
                  key={option.value}
                  value={option.value}
                  label={option.label}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>{option.label}</span>
                    <Tag color="blue">{option.params}</Tag>
                  </div>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.model_path !== currentValues.model_path
            }
          >
            {({ getFieldValue }) =>
              getFieldValue('model_path') === 'custom' ? (
                <Form.Item
                  label="自定义模型路径"
                  name="custom_path"
                  rules={[{ required: true, message: '请输入模型路径' }]}
                >
                  <Input placeholder="例如: /path/to/model 或 huggingface/model-name" />
                </Form.Item>
              ) : null
            }
          </Form.Item>

          <Form.Item
            label="模型名称"
            name="name"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="为模型起个名字，便于识别" />
          </Form.Item>

          <Form.Item label="参数量" name="parameter_size">
            <Select placeholder="请选择参数量">
              <Option value="1.5B">1.5B</Option>
              <Option value="3B">3B</Option>
              <Option value="6B">6B</Option>
              <Option value="7B">7B</Option>
              <Option value="13B">13B</Option>
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea
              rows={3}
              placeholder="请输入模型描述（可选）"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title="模型详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={700}
      >
        {selectedModel && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="模型名称">
              {selectedModel.name}
            </Descriptions.Item>
            <Descriptions.Item label="模型路径">
              {selectedModel.model_path}
            </Descriptions.Item>
            <Descriptions.Item label="类型">
              {selectedModel.model_type === ModelType.BASE && '基座模型'}
              {selectedModel.model_type === ModelType.FINETUNED && '微调模型'}
              {selectedModel.model_type === ModelType.LORA_ADAPTER && 'LoRA适配器'}
            </Descriptions.Item>
            <Descriptions.Item label="描述">
              {selectedModel.description || '无'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {new Date(selectedModel.created_at).toLocaleString('zh-CN')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default Models;
