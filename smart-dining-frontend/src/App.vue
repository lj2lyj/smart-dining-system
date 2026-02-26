<template>
  <div id="app" :data-theme="settingsStore.theme">
    <!-- 全局加载遮罩 -->
    <Transition name="fade">
      <div v-if="isLoading" class="global-loading">
        <div class="loading-content">
          <div class="loading-spinner"></div>
          <p class="loading-text">加载中...</p>
        </div>
      </div>
    </Transition>

    <!-- 主内容区 -->
    <RouterView v-slot="{ Component, route }">
      <Transition :name="route.meta.transition || 'fade'" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </RouterView>
  </div>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue'
import { useSettingsStore } from './stores/settings'

const settingsStore = useSettingsStore()
const isLoading = ref(true)

// 应用初始化
onMounted(async () => {
  // 模拟加载完成
  setTimeout(() => {
    isLoading.value = false
  }, 500)
})

// 提供全局方法
provide('showLoading', () => { isLoading.value = true })
provide('hideLoading', () => { isLoading.value = false })
</script>

<style>
/* 全局过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-left-enter-from {
  transform: translateX(30px);
  opacity: 0;
}

.slide-left-leave-to {
  transform: translateX(-30px);
  opacity: 0;
}

.slide-right-enter-from {
  transform: translateX(-30px);
  opacity: 0;
}

.slide-right-leave-to {
  transform: translateX(30px);
  opacity: 0;
}

/* 全局加载遮罩 */
.global-loading {
  position: fixed;
  inset: 0;
  background: var(--color-bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.loading-content {
  text-align: center;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-bg-secondary);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto var(--space-md);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}
</style>
