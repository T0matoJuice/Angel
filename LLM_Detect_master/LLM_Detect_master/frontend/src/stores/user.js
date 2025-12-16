import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUserStore = defineStore('user', () => {
    const isAuthenticated = ref(false)
    const username = ref('')
    const userId = ref(null)

    function setUser(user) {
        isAuthenticated.value = true
        username.value = user.username
        userId.value = user.id
    }

    function clearUser() {
        isAuthenticated.value = false
        username.value = ''
        userId.value = null
    }

    function checkAuth() {
        // 这里可以调用后端 API 检查登录状态
        // 暂时从 localStorage 读取
        const user = localStorage.getItem('user')
        if (user) {
            const userData = JSON.parse(user)
            setUser(userData)
        }
    }

    return {
        isAuthenticated,
        username,
        userId,
        setUser,
        clearUser,
        checkAuth
    }
})
