/**
 * 训练日志查看器组件
 */
import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Space, message, Spin, Alert, Switch } from 'antd';
import {
  ReloadOutlined,
  DownloadOutlined,
  CloseOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
} from '@ant-design/icons';
import { logApi } from '../services/logApi';

interface TrainingLogViewerProps {
  visible: boolean;
  taskId: number;
  taskName: string;
  onClose: () => void;
}

const TrainingLogViewer: React.FC<TrainingLogViewerProps> = ({
  visible,
  taskId,
  taskName,
  onClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [logContent, setLogContent] = useState<string>('');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const autoScrollRef = useRef<boolean>(true);

  // 加载日志
  const loadLog = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      const data = await logApi.getLog(taskId);
      setLogContent(data.content || '暂无日志内容');
      
      // 自动滚动到底部
      if (autoScrollRef.current && logContainerRef.current) {
        setTimeout(() => {
          if (logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
          }
        }, 100);
      }
    } catch (error: any) {
      if (error.response?.status === 404) {
        setLogContent('日志文件尚未生成，请等待任务开始执行...');
      } else {
        message.error('加载日志失败');
        console.error('Failed to load log:', error);
      }
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  // 下载日志
  const handleDownload = () => {
    const downloadUrl = logApi.downloadLog(taskId);
    window.open(downloadUrl, '_blank');
    message.success('开始下载日志文件');
  };

  // 切换全屏
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // 监听滚动，判断是否在底部
  const handleScroll = () => {
    if (logContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = logContainerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      autoScrollRef.current = isAtBottom;
    }
  };

  // 初始加载和自动刷新
  useEffect(() => {
    if (!visible) return;
    
    loadLog();
    
    if (autoRefresh) {
      const interval = setInterval(() => {
        loadLog(false); // 自动刷新时不显示loading
      }, 3000); // 每3秒刷新一次
      
      return () => clearInterval(interval);
    }
    
    return undefined; // 显式返回 undefined
  }, [visible, taskId, autoRefresh]);

  return (
    <Modal
      title={
        <Space>
          <span>📋 训练日志 - {taskName}</span>
          <span style={{ fontSize: 12, color: '#999' }}>任务ID: {taskId}</span>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={isFullscreen ? '95%' : '80%'}
      style={isFullscreen ? { top: 20 } : {}}
      footer={[
        <Space key="actions">
          <Switch
            checked={autoRefresh}
            onChange={setAutoRefresh}
            checkedChildren="自动刷新"
            unCheckedChildren="手动刷新"
          />
          <Button icon={<ReloadOutlined />} onClick={() => loadLog()}>
            刷新
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleDownload}>
            下载
          </Button>
          <Button
            icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
            onClick={toggleFullscreen}
          >
            {isFullscreen ? '退出全屏' : '全屏'}
          </Button>
          <Button icon={<CloseOutlined />} onClick={onClose}>
            关闭
          </Button>
        </Space>,
      ]}
    >
      <Spin spinning={loading}>
        <div style={{ marginBottom: 12 }}>
          <Alert
            message={
              <Space>
                <span>
                  {autoRefresh ? '🔄 自动刷新已启用（每3秒）' : '⏸️ 自动刷新已暂停'}
                </span>
                {autoScrollRef.current && <span>| 📍 自动滚动到底部</span>}
              </Space>
            }
            type="info"
            showIcon
          />
        </div>
        
        <div
          ref={logContainerRef}
          onScroll={handleScroll}
          style={{
            backgroundColor: '#1e1e1e',
            color: '#d4d4d4',
            padding: '16px',
            borderRadius: '4px',
            fontFamily: 'Monaco, Menlo, "Ubuntu Mono", Consolas, monospace',
            fontSize: '12px',
            lineHeight: '1.6',
            overflowY: 'auto',
            height: isFullscreen ? 'calc(95vh - 200px)' : '500px',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
          }}
        >
          {logContent}
        </div>
        
        <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
          <Space>
            <span>📊 总行数: {logContent.split('\n').length}</span>
            <span>📦 大小: {(new Blob([logContent]).size / 1024).toFixed(2)} KB</span>
            <span>⏰ 最后更新: {new Date().toLocaleTimeString('zh-CN')}</span>
          </Space>
        </div>
      </Spin>
    </Modal>
  );
};

export default TrainingLogViewer;

