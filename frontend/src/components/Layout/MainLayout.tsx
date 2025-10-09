/**
 * 主布局组件
 */

import React, { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Switch,
  Space,
  Typography,
  Badge,
} from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  CloudUploadOutlined,
  ThunderboltOutlined,
  SettingOutlined,
  UserOutlined,
  LogoutOutlined,
  BulbOutlined,
  BulbFilled,
  BellOutlined,
} from '@ant-design/icons';
import { authApi } from '../../services/api';
import './MainLayout.css';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

interface MainLayoutProps {
  isDarkMode: boolean;
  toggleTheme: () => void;
}

const MainLayout: React.FC<MainLayoutProps> = ({ isDarkMode, toggleTheme }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    try {
      await authApi.logout();
      localStorage.clear();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
      localStorage.clear();
      navigate('/login');
    }
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
      onClick: () => navigate('/settings'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系统设置',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/models',
      icon: <DatabaseOutlined />,
      label: '模型管理',
    },
    {
      key: '/datasets',
      icon: <CloudUploadOutlined />,
      label: '数据集',
    },
    {
      key: '/tasks',
      icon: <ThunderboltOutlined />,
      label: '训练任务',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme={isDarkMode ? 'dark' : 'light'}
        style={{
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div className="logo">
          <ThunderboltOutlined style={{ fontSize: collapsed ? 24 : 32 }} />
          {!collapsed && (
            <Text strong style={{ marginLeft: 12, fontSize: 18 }}>
              EasyTune-LLM
            </Text>
          )}
        </div>
        <Menu
          theme={isDarkMode ? 'dark' : 'light'}
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>

      <Layout style={{ marginLeft: collapsed ? 80 : 200, transition: 'all 0.2s' }}>
        <Header
          style={{
            padding: '0 24px',
            background: isDarkMode ? '#001529' : '#fff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          }}
        >
          <Space size="large">
            <Text strong style={{ fontSize: 18 }}>
              大模型微调平台
            </Text>
          </Space>

          <Space size="large">
            {/* 主题切换 */}
            <Space>
              {isDarkMode ? <BulbFilled /> : <BulbOutlined />}
              <Switch checked={isDarkMode} onChange={toggleTheme} />
            </Space>

            {/* 通知 */}
            <Badge count={3} size="small">
              <BellOutlined style={{ fontSize: 18, cursor: 'pointer' }} />
            </Badge>

            {/* 用户菜单 */}
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <Text>管理员</Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>

        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: isDarkMode ? '#141414' : '#f0f2f5',
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;

