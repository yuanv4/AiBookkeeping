/**
 * 全局错误处理中心
 * 职责: 错误归一化,返回用户友好的消息
 * ⚠️ 不直接调用 notificationStore,由调用方负责显示
 */

const ERROR_MESSAGES = {
  QUOTA_EXCEEDED: '存储空间不足,请清理数据或导出备份',
  WRITE_FAILED: '数据保存失败,请重试',
  READ_FAILED: '数据读取失败',
  KEY_NOT_FOUND: '数据不存在'
}

export const errorHandler = {
  /**
   * 处理存储错误,返回用户友好的消息
   * @returns {{ message: string, type: 'error' | 'warning' }}
   */
  normalizeStorageError(error) {
    const message = ERROR_MESSAGES[error.code] || error.message || '存储操作失败'
    const type = error.code === 'QUOTA_EXCEEDED' ? 'warning' : 'error'
    console.error('存储错误:', error)
    return { message, type }
  },

  /**
   * 处理 AI 服务错误
   * @returns {{ message: string, type: 'error' | 'warning' }}
   */
  normalizeAIError(error) {
    console.error('AI 错误:', error)
    return { message: 'AI 服务异常,请检查配置', type: 'error' }
  }
}

/**
 * Vue 错误捕获器
 * ⚠️ 必须在 app.mount() 之前注册,此时 Pinia 已初始化
 */
export function registerGlobalErrorHandler(app, notificationStore) {
  app.config.errorHandler = (err, instance, info) => {
    console.error('Vue 错误:', err, info)
    // 通过参数传入 notificationStore,避免循环依赖
    notificationStore?.show?.(`程序异常: ${err.message}`, 'error')
  }
}
