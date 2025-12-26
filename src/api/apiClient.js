import axios from 'axios'

// 从 localStorage 获取 token
const getToken = () => {
  return localStorage.getItem('auth_token')
}

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：自动添加 token
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一错误处理
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response

      // 401: 未登录或 token 过期
      if (status === 401) {
        localStorage.removeItem('auth_token')
        window.location.href = '/login'
      }

      // 403: 无权限
      if (status === 403) {
        console.error('权限不足:', data.message)
      }

      // 404: 资源不存在
      if (status === 404) {
        console.error('资源不存在:', data.message)
      }

      // 500: 服务器错误
      if (status >= 500) {
        console.error('服务器错误:', data.message)
      }

      return Promise.reject(new Error(data.message || '请求失败'))
    } else if (error.request) {
      // 请求已发送但没有收到响应
      console.error('网络错误: 无法连接到服务器')
      return Promise.reject(new Error('网络错误: 无法连接到服务器'))
    } else {
      // 请求配置出错
      console.error('请求错误:', error.message)
      return Promise.reject(error)
    }
  }
)

export default apiClient
