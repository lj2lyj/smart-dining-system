<template>
  <div class="login-view">
    <!-- 背景装饰 -->
    <div class="login-bg">
      <div class="bg-circle bg-circle-1"></div>
      <div class="bg-circle bg-circle-2"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card animate-fade-in-up">
      <div class="login-header">
        <div class="login-logo">🍽️</div>
        <h1 class="login-title">{{ isZh ? '管理后台' : 'Admin Panel' }}</h1>
        <p class="login-subtitle">{{ isZh ? '智慧餐饮结算系统' : 'Smart Dining System' }}</p>
      </div>

      <van-form @submit="handleLogin" class="login-form">
        <van-cell-group inset>
          <van-field
            v-model="username"
            name="username"
            :placeholder="isZh ? '用户名' : 'Username'"
            left-icon="user-o"
            :rules="[{ required: true, message: isZh ? '请输入用户名' : 'Username required' }]"
          />
          <van-field
            v-model="password"
            type="password"
            name="password"
            :placeholder="isZh ? '密码' : 'Password'"
            left-icon="lock"
            :rules="[{ required: true, message: isZh ? '请输入密码' : 'Password required' }]"
          />
        </van-cell-group>

        <div class="login-actions">
          <van-button 
            type="primary" 
            native-type="submit" 
            block 
            round
            :loading="loading"
          >
            {{ isZh ? '登录' : 'Login' }}
          </van-button>
        </div>
      </van-form>

      <!-- 返回按钮 -->
      <button class="back-btn" @click="$router.push('/')">
        <van-icon name="arrow-left" />
        <span>{{ isZh ? '返回顾客端' : 'Back to Customer' }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore, useSettingsStore } from '../../stores'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const isZh = computed(() => settingsStore.language === 'zh')

const username = ref('')
const password = ref('')
const loading = ref(false)

async function handleLogin() {
  loading.value = true
  
  try {
    const result = await authStore.login(username.value, password.value)
    
    if (result.success) {
      showToast({ message: isZh.value ? '登录成功' : 'Login successful', icon: 'success' })
      
      // 跳转到目标页面或仪表盘
      const redirect = route.query.redirect || '/admin/dashboard'
      router.push(redirect)
    } else {
      showToast({ message: result.message, icon: 'fail' })
    }
  } catch (error) {
    showToast(isZh.value ? '登录失败' : 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-view {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
  background: var(--color-bg-primary);
  position: relative;
  overflow: hidden;
}

.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  background: var(--color-primary-gradient);
  opacity: 0.1;
}

.bg-circle-1 {
  width: 400px;
  height: 400px;
  top: -150px;
  right: -100px;
}

.bg-circle-2 {
  width: 300px;
  height: 300px;
  bottom: -100px;
  left: -100px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: var(--color-bg-card);
  border-radius: var(--radius-xl);
  padding: var(--space-2xl);
  box-shadow: var(--shadow-xl);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.login-logo {
  font-size: 48px;
  margin-bottom: var(--space-md);
}

.login-title {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  color: var(--color-text-primary);
  margin-bottom: var(--space-xs);
}

.login-subtitle {
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
}

.login-form {
  margin-bottom: var(--space-lg);
}

.login-actions {
  margin-top: var(--space-xl);
}

.login-hint {
  margin-top: var(--space-md);
  text-align: center;
  font-size: var(--text-xs);
  color: var(--color-text-light);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-xs);
  width: 100%;
  padding: var(--space-md);
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--text-sm);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.back-btn:hover {
  color: var(--color-primary);
}
</style>
