<template>
  <div class="page-container">
    <div class="content-wrapper">
      <div class="header-bar">
        <router-link to="/" class="back-btn">← 返回首页</router-link>
        <h1>制图检测系统</h1>
      </div>
      
      <div class="card">
        <h2>🔧 制图检测系统</h2>
        <p class="description">功能开发中...</p>
        <div class="placeholder">
          <div class="icon">🚧</div>
          <p>此页面正在开发中，敬请期待！</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.page-container {
  min-height: 100vh;
  padding: 20px;
}

.content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
}

.header-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.back-btn {
  padding: 10px 20px;
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  border-radius: 20px;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #667eea;
  color: white;
}

.header-bar h1 {
  color: white;
  font-size: 32px;
  margin: 0;
}

.card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.description {
  color: #666;
  font-size: 16px;
  margin: 20px 0;
}

.placeholder {
  text-align: center;
  padding: 60px 20px;
}

.placeholder .icon {
  font-size: 80px;
  margin-bottom: 20px;
}

.placeholder p {
  font-size: 18px;
  color: #999;
}
</style>
