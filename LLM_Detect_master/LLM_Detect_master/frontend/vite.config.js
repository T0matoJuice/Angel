import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      // 代理 API 请求到 Flask 后端
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/drawing': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      },
      '/excel': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  }
})
