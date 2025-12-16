import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
    {
        path: '/',
        name: 'Home',
        component: Home,
        meta: { title: '大模型智能检测系统' }
    },
    {
        path: '/drawing',
        name: 'Drawing',
        component: () => import('../views/Drawing/DrawingIndex.vue'),
        meta: { title: '制图检测系统' }
    },
    {
        path: '/drawing/detection',
        name: 'DrawingDetection',
        component: () => import('../views/Drawing/DrawingDetection.vue'),
        meta: { title: '制图检测' }
    },
    {
        path: '/drawing/history',
        name: 'DrawingHistory',
        component: () => import('../views/Drawing/DrawingHistory.vue'),
        meta: { title: '检测历史' }
    },
    {
        path: '/excel',
        name: 'Excel',
        component: () => import('../views/Excel/ExcelIndex.vue'),
        meta: { title: 'Excel工单检测系统' }
    },
    {
        path: '/excel/quality',
        name: 'ExcelQuality',
        component: () => import('../views/Excel/ExcelQuality.vue'),
        meta: { title: '质量工单检测' }
    },
    {
        path: '/excel/standard',
        name: 'ExcelStandard',
        component: () => import('../views/Excel/ExcelStandard.vue'),
        meta: { title: '工单问题点检测' }
    },
    {
        path: '/auth/login',
        name: 'Login',
        component: () => import('../views/Auth/Login.vue'),
        meta: { title: '登录' }
    },
    {
        path: '/auth/register',
        name: 'Register',
        component: () => import('../views/Auth/Register.vue'),
        meta: { title: '注册' }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, from, next) => {
    document.title = to.meta.title || '大模型智能检测系统'
    next()
})

export default router
