import React from 'react';
import { Card, Descriptions } from 'antd';

const TaskDetail: React.FC = () => {
  return (
    <Card title="任务详情">
      <Descriptions>
        <Descriptions.Item label="任务名称">示例任务</Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default TaskDetail;

