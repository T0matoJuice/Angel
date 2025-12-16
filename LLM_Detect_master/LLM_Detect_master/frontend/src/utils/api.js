import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
    baseURL: '/',
    timeout: 300000, // 5分钟超时，因为 AI 处理可能需要较长时间
    headers: {
        'Content-Type': 'application/json'
    }
})

// 请求拦截器
api.interceptors.request.use(
    config => {
        // 可以在这里添加 token
        const token = localStorage.getItem('token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    error => {
        return Promise.reject(error)
    }
)

// 响应拦截器
api.interceptors.response.use(
    response => {
        return response.data
    },
    error => {
        // 统一错误处理
        if (error.response) {
            switch (error.response.status) {
                case 401:
                    // 未授权，跳转登录
                    localStorage.removeItem('token')
                    localStorage.removeItem('user')
                    window.location.href = '/auth/login'
                    break
                case 403:
                    console.error('没有权限访问')
                    break
                case 404:
                    console.error('请求的资源不存在')
                    break
                case 500:
                    console.error('服务器错误')
                    break
                default:
                    console.error('请求失败:', error.response.data.message || error.message)
            }
        }
        return Promise.reject(error)
    }
)

export default api
