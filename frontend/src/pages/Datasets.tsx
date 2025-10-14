/**
 * 数据集管理页面
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Upload,
  Modal,
  Form,
  Input,
  message,
  Space,
  Tag,
  Popconfirm,
} from 'antd';
import {
  UploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { datasetApi } from '../services/api';
import { Dataset } from '../types';

const { TextArea } = Input;
const { Dragger } = Upload;

const Datasets: React.FC = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadModalVisible, setUploadModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [form] = Form.useForm();
  const [fileList, setFileList] = useState<any[]>([]);

  // 加载数据集列表
  const loadDatasets = async () => {
    setLoading(true);
    try {
      const response = await datasetApi.getDatasets();
      setDatasets(response.items || []);
    } catch (error: any) {
      message.error(error.response?.data?.message || '加载数据集失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  // 上传配置
  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    maxCount: 1,
    accept: '.json,.jsonl,.csv,.txt',
    fileList,
    beforeUpload: (file) => {
      // 验证文件类型
      const isValidType = ['json', 'jsonl', 'csv', 'txt'].some(
        (ext) => file.name.toLowerCase().endsWith(ext)
      );
      if (!isValidType) {
        message.error('只支持 JSON、JSONL、CSV、TXT 格式的文件！');
        return false;
      }
      
      // 验证文件大小（最大100MB）
      const isLt100M = file.size / 1024 / 1024 < 100;
      if (!isLt100M) {
        message.error('文件大小不能超过 100MB！');
        return false;
      }

      setFileList([file]);
      return false; // 阻止自动上传
    },
    onRemove: () => {
      setFileList([]);
    },
  };

  // 处理上传
  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.error('请选择要上传的文件');
      return;
    }

    try {
      const values = await form.validateFields();
      
      setLoading(true);
      await datasetApi.uploadDataset(
        fileList[0],
        values.name,
        values.description,
        'instruction'
      );
      message.success('数据集上传成功！');
      
      setUploadModalVisible(false);
      form.resetFields();
      setFileList([]);
      loadDatasets();
    } catch (error: any) {
      message.error(error.response?.data?.message || '上传失败');
    } finally {
      setLoading(false);
    }
  };

  // 删除数据集
  const handleDelete = async (id: number) => {
    try {
      await datasetApi.deleteDataset(id);
      message.success('删除成功');
      loadDatasets();
    } catch (error: any) {
      message.error(error.response?.data?.message || '删除失败');
    }
  };

  // 预览数据集
  const handlePreview = async (dataset: Dataset) => {
    try {
      // 这里可以调用API获取数据集详情
      setPreviewData(dataset);
      setPreviewModalVisible(true);
    } catch (error: any) {
      message.error('预览失败');
    }
  };

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: '数据集名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '样本数量',
      dataIndex: 'total_samples',
      key: 'total_samples',
      render: (count: number) => (
        <Tag color="blue">{count || 0} 条</Tag>
      ),
    },
    {
      title: '文件类型',
      dataIndex: 'file_format',
      key: 'file_format',
      render: (format: string) => (
        <Tag color="green">{format?.toUpperCase() || '-'}</Tag>
      ),
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
      render: (_: any, record: Dataset) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => handlePreview(record)}
          >
            预览
          </Button>
          <Popconfirm
            title="确定要删除这个数据集吗？"
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
        title="数据集管理"
        extra={
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setUploadModalVisible(true)}
          >
            上传数据集
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={datasets}
          rowKey="id"
          loading={loading}
          pagination={{
            total: datasets.length,
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个数据集`,
          }}
        />
      </Card>

      {/* 上传数据集模态框 */}
      <Modal
        title="上传数据集"
        open={uploadModalVisible}
        onOk={handleUpload}
        onCancel={() => {
          setUploadModalVisible(false);
          form.resetFields();
          setFileList([]);
        }}
        confirmLoading={loading}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            label="数据集名称"
            name="name"
            rules={[{ required: true, message: '请输入数据集名称' }]}
          >
            <Input placeholder="请输入数据集名称" />
          </Form.Item>

          <Form.Item label="描述" name="description">
            <TextArea
              rows={3}
              placeholder="请输入数据集描述（可选）"
            />
          </Form.Item>

          <Form.Item label="上传文件" required>
            <Dragger {...uploadProps}>
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持 JSON、JSONL、CSV、TXT 格式<br />
                文件大小不超过 100MB<br />
                <br />
                <strong>JSON 格式示例：</strong><br />
                {'['}
                  {'{'}
                    "instruction": "问题描述",
                    "input": "输入内容",
                    "output": "期望输出"
                  {'}'}
                {']'}
              </p>
            </Dragger>
          </Form.Item>
        </Form>
      </Modal>

      {/* 预览模态框 */}
      <Modal
        title="数据集详情"
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={null}
        width={800}
      >
        {previewData && (
          <div>
            <p><strong>名称：</strong>{previewData.name}</p>
            <p><strong>描述：</strong>{previewData.description || '无'}</p>
            <p><strong>样本数量：</strong>{previewData.total_samples || 0} 条</p>
            <p><strong>文件类型：</strong>{previewData.file_format?.toUpperCase() || '-'}</p>
            <p><strong>数据集类型：</strong>{previewData.dataset_type || '-'}</p>
            <p><strong>是否已验证：</strong>{previewData.is_validated ? '✅ 是' : '❌ 否'}</p>
            <p><strong>文件路径：</strong>{previewData.dataset_path}</p>
            <p><strong>创建时间：</strong>{new Date(previewData.created_at).toLocaleString('zh-CN')}</p>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Datasets;
