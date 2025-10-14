/**
 * 统一错误处理工具
 */

/**
 * 格式化API错误信息
 * @param error axios错误对象
 * @param defaultMsg 默认错误消息
 * @returns 格式化后的错误消息字符串
 */
export function formatApiError(error: any, defaultMsg: string = '操作失败'): string {
  if (!error) return defaultMsg;

  // 检查是否有响应数据
  if (error.response?.data) {
    const { detail } = error.response.data;
    
    // 处理422验证错误（FastAPI格式）
    if (Array.isArray(detail)) {
      // 字段名映射（中文显示）
      const fieldNameMap: Record<string, string> = {
        'task_name': '任务名称',
        'base_model_id': '基座模型',
        'dataset_id': '训练数据集',
        'task_complexity': '任务复杂度',
        'output_model_name': '输出模型名称',
        'num_epochs': '训练轮数',
        'task_intent': '训练意图',
        'description': '任务描述',
      };

      const errors = detail.map((err: any) => {
        if (err.loc && Array.isArray(err.loc) && err.msg) {
          // loc 格式: ["body", "field_name"]
          const fieldName = err.loc[err.loc.length - 1];
          const displayName = fieldNameMap[fieldName] || fieldName;
          return `${displayName}: ${err.msg}`;
        }
        if (err.msg) return err.msg;
        return JSON.stringify(err);
      });

      return errors.join('\n');
    }
    
    // 处理字符串格式的detail
    if (typeof detail === 'string') {
      return detail;
    }
    
    // 处理对象格式的detail
    if (typeof detail === 'object' && detail.message) {
      return detail.message;
    }
    
    // 其他情况
    if (error.response.data.message) {
      return error.response.data.message;
    }
  }
  
  // 处理网络错误
  if (error.message) {
    return error.message;
  }
  
  return defaultMsg;
}

/**
 * 提取验证错误的字段信息
 * @param error axios错误对象
 * @returns 字段错误映射 {field: errorMessage}
 */
export function extractValidationErrors(error: any): Record<string, string> {
  const errors: Record<string, string> = {};
  
  if (error.response?.data?.detail && Array.isArray(error.response.data.detail)) {
    error.response.data.detail.forEach((err: any) => {
      if (err.loc && err.msg) {
        // loc 通常是 ["body", "field_name"] 格式
        const field = Array.isArray(err.loc) ? err.loc[err.loc.length - 1] : err.loc;
        errors[field] = err.msg;
      }
    });
  }
  
  return errors;
}

