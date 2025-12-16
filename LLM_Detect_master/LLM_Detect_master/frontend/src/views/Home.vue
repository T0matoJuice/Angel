<template>
  <div class="home-page">
    <div class="main-container">
      <!-- 用户信息栏 -->
      <div class="user-info">
        <template v-if="userStore.isAuthenticated">
          <span class="user-name">👤 {{ userStore.username }}</span>
          <button @click="handleLogout" class="btn-logout">登出</button>
        </template>
        <template v-else>
          <router-link to="/auth/login" class="btn-login">登录</router-link>
          <router-link to="/auth/register" class="btn-logout">注册</router-link>
        </template>
      </div>

      <div class="header">
        <h1 class="title">🤖 大模型智能检测系统</h1>
        <p class="subtitle">
          智能化检测平台，集成制图规范检测和质量工单数据处理<br>
          提供专业的大模型驱动分析服务
        </p>
      </div>

      <div class="systems-container">
        <router-link to="/drawing" class="system-card drawing-card">
          <span class="system-icon">🔧</span>
          <h3 class="system-title">制图检测系统</h3>
          <p class="system-description">
            基于大模型技术的智能制图规范检测平台，提供专业的机械制图标准化检测分析服务
          </p>
          <ul class="system-features">
            <li>PDF制图文件上传</li>
            <li>智能规范检测分析</li>
            <li>详细检测报告生成</li>
            <li>标准工图参考</li>
          </ul>
        </router-link>

        <router-link to="/excel" class="system-card excel-card">
          <span class="system-icon">📊</span>
          <h3 class="system-title">质量工单检测系统</h3>
          <p class="system-description">
            基于大模型的质量工单数据处理系统，自动推理填充规则并进行数据自动填充
          </p>
          <ul class="system-features">
            <li>工单文件智能处理</li>
            <li>大模型规则学习推理</li>
            <li>自动数据填充</li>
            <li>结果对比展示</li>
          </ul>
        </router-link>
      </div>

      <div class="footer">
        <p>🎯 专业 · 智能 · 高效</p>
        <p class="version">Version 2.0 (Vue 3) | Powered by Jiaoyunhuizhi Technology</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useUserStore } from '../stores/user'
import { useRouter } from 'vue-router'

const userStore = useUserStore()
const router = useRouter()

const handleLogout = () => {
  userStore.clearUser()
  localStorage.removeItem('user')
  localStorage.removeItem('token')
  router.push('/auth/login')
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.main-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
  padding: 60px 50px;
  text-align: center;
  max-width: 900px;
  width: 100%;
  animation: fadeInUp 0.8s ease-out;
  position: relative;
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

.header {
  margin-bottom: 50px;
}

.title {
  font-size: 42px;
  font-weight: 800;
  color: #333;
  margin-bottom: 15px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
  background: linear-gradient(45deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 18px;
  color: #666;
  font-weight: 400;
  line-height: 1.6;
}

.systems-container {
  display: flex;
  gap: 30px;
  margin-top: 40px;
  justify-content: center;
}

.system-card {
  background: white;
  border-radius: 20px;
  padding: 40px 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  text-decoration: none;
  color: inherit;
  flex: 1;
  max-width: 350px;
  position: relative;
  overflow: hidden;
}

.system-card:before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
  transition: left 0.5s;
}

.system-card:hover:before {
  left: 100%;
}

.system-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.15);
}

.system-icon {
  font-size: 64px;
  margin-bottom: 20px;
  display: block;
}

.drawing-card {
  border-top: 4px solid #667eea;
}

.drawing-card:hover {
  border-top-color: #5a6fd8;
}

.excel-card {
  border-top: 4px solid #28a745;
}

.excel-card:hover {
  border-top-color: #218838;
}

.system-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 15px;
  color: #333;
}

.system-description {
  font-size: 14px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
}

.system-features {
  list-style: none;
  text-align: left;
  font-size: 13px;
  color: #888;
}

.system-features li {
  margin-bottom: 8px;
  position: relative;
  padding-left: 20px;
}

.system-features li:before {
  content: '✓';
  position: absolute;
  left: 0;
  color: #28a745;
  font-weight: bold;
}

.footer {
  margin-top: 50px;
  padding-top: 30px;
  border-top: 1px solid #e0e0e0;
  color: #999;
  font-size: 14px;
}

.version {
  margin-top: 10px;
  font-size: 12px;
  color: #ccc;
}

/* 用户信息栏样式 */
.user-info {
  position: absolute;
  top: 20px;
  right: 30px;
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-name {
  color: #333;
  font-weight: 600;
  font-size: 14px;
}

.btn-logout {
  padding: 8px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
}

.btn-logout:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
}

.btn-login {
  padding: 8px 20px;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  text-decoration: none;
  display: inline-block;
}

.btn-login:hover {
  background: #667eea;
  color: white;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .main-container {
    padding: 40px 30px;
  }

  .title {
    font-size: 32px;
  }

  .subtitle {
    font-size: 16px;
  }

  .systems-container {
    flex-direction: column;
    gap: 20px;
  }

  .system-card {
    max-width: none;
    padding: 30px 25px;
  }

  .system-icon {
    font-size: 48px;
  }

  .system-title {
    font-size: 20px;
  }

  .user-info {
    position: static;
    justify-content: center;
    margin-bottom: 30px;
  }
}

@media (max-width: 480px) {
  .main-container {
    padding: 30px 20px;
  }

  .title {
    font-size: 28px;
  }

  .system-card {
    padding: 25px 20px;
  }
}
</style>
