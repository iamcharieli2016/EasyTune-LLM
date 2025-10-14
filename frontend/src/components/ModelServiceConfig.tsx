/**
 * 模型服务配置组件
 */
import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  InputNumber,
  Radio,
  Space,
  Button,
  Alert,
  Tabs,
  Card,
  message,
  Progress,
} from 'antd';
import {
  CloudDownloadOutlined,
  RocketOutlined,
  ApiOutlined,
} from '@ant-design/icons';

const { TabPane } = Tabs;

interface ModelServiceConfigProps {
  visible: boolean;
  modelId: number;
  modelName: string;
  onClose: () => void;
  onSuccess: () => void;
}

enum ModelSource {
  HUGGINGFACE = 'huggingface',
  MODELSCOPE = 'modelscope',
  LOCAL = 'local',
  REMOTE_API = 'remote_api',
}

enum ServiceType {
  LOCAL_VLLM = 'local_vllm',
  LOCAL_TRANSFORMERS = 'local_transformers',
  REMOTE_OPENAI = 'remote_openai',
  REMOTE_CUSTOM = 'remote_custom',
}

const ModelServiceConfig: React.FC<ModelServiceConfigProps> = ({
  visible,
  modelId,
  modelName,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<ModelSource>(ModelSource.HUGGINGFACE);
  const [downloadProgress, setDownloadProgress] = useState(0);

  const handleDownload = async (values: any) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/model-service/${modelId}/download`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          model_id: values.model_id,
          source: activeTab,
          token: values.token,
        }),
      });

      if (response.ok) {
        message.success('模型下载已在后台启动');
        // 轮询下载状态
        pollDownloadStatus();
      } else {
        message.error('启动下载失败');
      }
    } catch (error) {
      message.error('请求失败');
    } finally {
      setLoading(false);
    }
  };

  const pollDownloadStatus = () => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/model-service/${modelId}/download/status`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        });
        const data = await response.json();

        if (data.complete) {
          setDownloadProgress(100);
          clearInterval(interval);
          message.success('模型下载完成！');
          onSuccess();
        }
      } catch (error) {
        clearInterval(interval);
      }
    }, 5000);
  };

  const handleConfigureService = async (values: any) => {
    setLoading(true);
    try {
      const config = {
        source: activeTab,
        service_type: values.service_type,
        model_path: values.model_path,
        service_config: {
          port: values.port,
          gpu_memory_utilization: values.gpu_memory_utilization,
          max_model_len: values.max_model_len,
        },
        api_config: {
          type: values.api_type,
          base_url: values.base_url,
          api_key: values.api_key,
          model_name: values.remote_model_name,
        },
      };

      const response = await fetch(`/api/v1/model-service/${modelId}/configure`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        message.success('服务配置成功');
        onSuccess();
        onClose();
      } else {
        message.error('配置失败');
      }
    } catch (error) {
      message.error('请求失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title={`配置模型服务 - ${modelName}`}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
    >
      <Tabs activeKey={activeTab} onChange={(key) => setActiveTab(key as ModelSource)}>
        {/* HuggingFace下载 */}
        <TabPane
          tab={
            <span>
              <CloudDownloadOutlined /> HuggingFace
            </span>
          }
          key={ModelSource.HUGGINGFACE}
        >
          <Card>
            <Form form={form} layout="vertical" onFinish={handleDownload}>
              <Alert
                message="从HuggingFace Hub下载模型"
                description="支持所有开源模型，需要稳定的网络连接"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Form.Item
                label="模型ID"
                name="model_id"
                rules={[{ required: true, message: '请输入模型ID' }]}
              >
                <Input placeholder="例如: Qwen/Qwen-7B-Chat" />
              </Form.Item>

              <Form.Item label="访问令牌" name="token">
                <Input.Password placeholder="私有模型需要（可选）" />
              </Form.Item>

              {downloadProgress > 0 && (
                <Progress percent={downloadProgress} status="active" />
              )}

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  开始下载
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* ModelScope下载 */}
        <TabPane
          tab={
            <span>
              <CloudDownloadOutlined /> ModelScope
            </span>
          }
          key={ModelSource.MODELSCOPE}
        >
          <Card>
            <Form form={form} layout="vertical" onFinish={handleDownload}>
              <Alert
                message="从ModelScope下载模型（国内镜像）"
                description="适合国内用户，下载速度更快"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Form.Item
                label="模型ID"
                name="model_id"
                rules={[{ required: true, message: '请输入模型ID' }]}
              >
                <Input placeholder="例如: qwen/Qwen-7B-Chat" />
              </Form.Item>

              {downloadProgress > 0 && (
                <Progress percent={downloadProgress} status="active" />
              )}

              <Form.Item>
                <Button type="primary" htmlType="submit" loading={loading} block>
                  开始下载
                </Button>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* 本地服务 */}
        <TabPane
          tab={
            <span>
              <RocketOutlined /> 本地服务
            </span>
          }
          key={ModelSource.LOCAL}
        >
          <Card>
            <Form form={form} layout="vertical" onFinish={handleConfigureService}>
              <Alert
                message="配置本地模型服务"
                description="使用vLLM或Transformers启动本地模型服务"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Form.Item
                label="服务类型"
                name="service_type"
                initialValue={ServiceType.LOCAL_TRANSFORMERS}
              >
                <Radio.Group>
                  <Radio value={ServiceType.LOCAL_VLLM}>vLLM（高性能推理）</Radio>
                  <Radio value={ServiceType.LOCAL_TRANSFORMERS}>Transformers（直接加载）</Radio>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                label="模型路径"
                name="model_path"
                rules={[{ required: true, message: '请输入模型路径' }]}
              >
                <Input placeholder="./models/Qwen-7B-Chat" />
              </Form.Item>

              <Form.Item label="服务端口" name="port" initialValue={8001}>
                <InputNumber min={8000} max={9999} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item
                label="GPU内存使用率"
                name="gpu_memory_utilization"
                initialValue={0.9}
              >
                <InputNumber min={0.1} max={1.0} step={0.1} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item label="最大序列长度" name="max_model_len" initialValue={4096}>
                <InputNumber min={512} max={32768} style={{ width: '100%' }} />
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    配置并启动
                  </Button>
                  <Button>测试配置</Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>

        {/* 远程API */}
        <TabPane
          tab={
            <span>
              <ApiOutlined /> 远程API
            </span>
          }
          key={ModelSource.REMOTE_API}
        >
          <Card>
            <Form form={form} layout="vertical" onFinish={handleConfigureService}>
              <Alert
                message="配置远程模型API"
                description="连接到已部署的模型服务（OpenAI兼容API）"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />

              <Form.Item
                label="API类型"
                name="api_type"
                initialValue={ServiceType.REMOTE_OPENAI}
              >
                <Radio.Group>
                  <Radio value={ServiceType.REMOTE_OPENAI}>OpenAI兼容</Radio>
                  <Radio value={ServiceType.REMOTE_CUSTOM}>自定义API</Radio>
                </Radio.Group>
              </Form.Item>

              <Form.Item
                label="API地址"
                name="base_url"
                rules={[{ required: true, message: '请输入API地址' }]}
              >
                <Input placeholder="https://api.example.com/v1" />
              </Form.Item>

              <Form.Item
                label="API密钥"
                name="api_key"
                rules={[{ required: true, message: '请输入API密钥' }]}
              >
                <Input.Password placeholder="sk-..." />
              </Form.Item>

              <Form.Item
                label="模型名称"
                name="remote_model_name"
                rules={[{ required: true, message: '请输入模型名称' }]}
              >
                <Input placeholder="gpt-4" />
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    保存配置
                  </Button>
                  <Button>测试连接</Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </TabPane>
      </Tabs>
    </Modal>
  );
};

export default ModelServiceConfig;

