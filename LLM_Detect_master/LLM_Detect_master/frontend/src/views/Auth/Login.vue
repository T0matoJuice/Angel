<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <h1 class="auth-title">🔐 用户登录</h1>
        <p class="auth-subtitle">登录大模型智能检测系统</p>
        
        <form @submit.prevent="handleLogin" class="auth-form">
          <div class="input-group">
            <label for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              v-model="formData.username" 
              placeholder="请输入用户名"
              required
            />
          </div>
          
          <div class="input-group">
            <label for="password">密码</label>
            <input 
              type="password" 
              id="password" 
              v-model="formData.password" 
              placeholder="请输入密码"
              required
            />
          </div>
          
          <div class="error-message" v-if="errorMessage">
            {{ errorMessage }}
          </div>
          
          <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
            <span v-if="!loading">登录</span>
            <span v-else>登录中...</span>
          </button>
        </form>
        
        <div class="auth-footer">
          <p>还没有账号？ <router-link to="/auth/register">立即注册</router-link></p>
          <router-link to="/" class="back-home">返回首页</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'

const router = useRouter()
const userStore = useUserStore()

const formData = ref({
  username: '',
  password: ''
})

const loading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  
  try {
    // TODO: 调用后端登录 API
    // 暂时模拟登录
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟登录成功
    const user = {
      id: 1,
      username: formData.value.username
    }
    
    userStore.setUser(user)
    localStorage.setItem('user', JSON.stringify(user))
    
    router.push('/')
  } catch (error) {
    errorMessage.value = '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.auth-container {
  width: 100%;
  max-width: 450px;
}

.auth-card {
  background: white;
  border-radius: 20px;
  padding: 50px 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.auth-title {
  font-size: 32px;
  font-weight: 800;
  color: #333;
  margin-bottom: 10px;
  text-align: center;
}

.auth-subtitle {
  font-size: 16px;
  color: #666;
  text-align: center;
  margin-bottom: 40px;
}

.auth-form {
  margin-bottom: 30px;
}

.btn-block {
  width: 100%;
  margin-top: 20px;
}

.error-message {
  background: #fee;
  color: #c33;
  padding: 12px;
  border-radius: 8px;
  margin-top: 15px;
  font-size: 14px;
  text-align: center;
}

.auth-footer {
  text-align: center;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.auth-footer p {
  color: #666;
  font-size: 14px;
  margin-bottom: 15px;
}

.auth-footer a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
}

.auth-footer a:hover {
  text-decoration: underline;
}

.back-home {
  display: inline-block;
  padding: 8px 20px;
  background: #f5f5f5;
  border-radius: 15px;
  transition: all 0.3s;
}

.back-home:hover {
  background: #e0e0e0;
  text-decoration: none !important;
}
</style>
