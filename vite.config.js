import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      // 代理 /api 请求到后端服务
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
        // 不重写路径，保持 /api 前缀
        // secure: false // 如果是 https 且证书自签名，可以开启此选项
      }
    }
  }
})
