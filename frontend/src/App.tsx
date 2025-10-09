/**
 * 应用主组件
 */

import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';

// 页面组件
import LoginPage from './pages/Login';
import DashboardPage from './pages/Dashboard';
import ModelsPage from './pages/Models';
import DatasetsPage from './pages/Datasets';
import TasksPage from './pages/Tasks';
import TaskDetailPage from './pages/TaskDetail';
import CreateTaskPage from './pages/CreateTask';
import SettingsPage from './pages/Settings';
import MainLayout from './components/Layout/MainLayout';

// 样式
import './App.css';

// 路由保护组件
const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('access_token');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
};

const App: React.FC = () => {
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    // 从localStorage读取主题设置
    const savedTheme = localStorage.getItem('theme');
    setIsDarkMode(savedTheme === 'dark');
  }, []);

  const toggleTheme = () => {
    const newTheme = !isDarkMode;
    setIsDarkMode(newTheme);
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

  return (
    <ConfigProvider
      locale={zhCN}
      theme={{
        algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 8,
          fontSize: 14,
        },
      }}
    >
      <Router>
        <Routes>
          {/* 公开路由 */}
          <Route path="/login" element={<LoginPage />} />

          {/* 受保护的路由 */}
          <Route
            path="/"
            element={
              <PrivateRoute>
                <MainLayout isDarkMode={isDarkMode} toggleTheme={toggleTheme} />
              </PrivateRoute>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="models" element={<ModelsPage />} />
            <Route path="datasets" element={<DatasetsPage />} />
            <Route path="tasks" element={<TasksPage />} />
            <Route path="tasks/:id" element={<TaskDetailPage />} />
            <Route path="tasks/create" element={<CreateTaskPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>

          {/* 404 */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </ConfigProvider>
  );
};

export default App;

