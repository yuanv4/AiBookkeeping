import apiClient from './apiClient.js'

/**
 * 认证相关 API
 */
export const authApi = {
  /**
   * 用户登录
   * @param {string} username - 用户名
   * @param {string} password - 密码
   * @returns {Promise<{token: string, user: object}>}
   */
  async login(username, password) {
    const response = await apiClient.post('/auth/login', { username, password })

    // 后端返回格式: { success: true, data: { token, user } }
    const { data } = response.data
    const { token, user } = data

    // 保存 token 到 localStorage
    localStorage.setItem('auth_token', token)
    localStorage.setItem('user_info', JSON.stringify(user))

    return { token, user }
  },

  /**
   * 用户登出
   */
  async logout() {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      // 无论后端响应如何，都清除本地 token
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_info')
    }
  },

  /**
   * 获取当前用户信息
   * @returns {Promise<object>}
   */
  async getMe() {
    const response = await apiClient.get('/auth/me')
    return response.data
  },

  /**
   * 修改密码
   * @param {string} oldPassword - 旧密码
   * @param {string} newPassword - 新密码
   * @returns {Promise<{message: string}>}
   */
  async changePassword(oldPassword, newPassword) {
    const response = await apiClient.post('/auth/change-password', {
      oldPassword,
      newPassword
    })
    return response.data
  },

  /**
   * 检查是否已登录
   * @returns {boolean}
   */
  isAuthenticated() {
    return !!localStorage.getItem('auth_token')
  },

  /**
   * 获取本地存储的用户信息
   * @returns {object|null}
   */
  getLocalUser() {
    const userInfo = localStorage.getItem('user_info')
    return userInfo ? JSON.parse(userInfo) : null
  }
}
