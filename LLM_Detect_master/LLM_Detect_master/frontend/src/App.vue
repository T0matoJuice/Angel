<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from './stores/user'

const userStore = useUserStore()

onMounted(() => {
  // 检查用户登录状态
  userStore.checkAuth()
})
</script>

<style scoped>
#app {
  width: 100%;
  min-height: 100vh;
}
</style>
