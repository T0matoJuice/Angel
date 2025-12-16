<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-card">
        <h1 class="auth-title">📝 用户注册</h1>
        <p class="auth-subtitle">创建您的账号</p>
        
        <form @submit.prevent="handleRegister" class="auth-form">
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
          
          <div class="input-group">
            <label for="confirmPassword">确认密码</label>
            <input 
              type="password" 
              id="confirmPassword" 
              v-model="formData.confirmPassword" 
              placeholder="请再次输入密码"
              required
            />
          </div>
          
          <div class="error-message" v-if="errorMessage">
            {{ errorMessage }}
          </div>
          
          <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
            <span v-if="!loading">注册</span>
            <span v-else>注册中...</span>
          </button>
        </form>
        
        <div class="auth-footer">
          <p>已有账号？ <router-link to="/auth/login">立即登录</router-link></p>
          <router-link to="/" class="back-home">返回首页</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const formData = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const loading = ref(false)
const errorMessage = ref('')

const handleRegister = async () => {
  loading.value = true
  errorMessage.value = ''
  
  // 验证密码
  if (formData.value.password !== formData.value.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    loading.value = false
    return
  }
  
  try {
    // TODO: 调用后端注册 API
    // 暂时模拟注册
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 注册成功，跳转登录
    router.push('/auth/login')
  } catch (error) {
    errorMessage.value = '注册失败，请稍后重试'
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
