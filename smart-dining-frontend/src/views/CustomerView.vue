<template>
  <div class="customer-view">
    <!-- 顶部导航 -->
    <van-nav-bar 
      :title="t('app.name', language)"
      :border="false"
    >
      <template #left>
        <div class="nav-logo">🍽️</div>
      </template>
      <template #right>
        <div class="nav-actions">
          <van-icon 
            name="clock-o" 
            size="22" 
            @click="$router.push('/history')"
          />
          <van-icon 
            name="setting-o" 
            size="22" 
            @click="$router.push('/preferences')"
          />
        </div>
      </template>
    </van-nav-bar>

    <!-- 紧凑欢迎区域 -->
    <div class="welcome-section">
      <span class="welcome-title">{{ t('app.slogan', language) }}</span>
      <span class="welcome-sep">·</span>
      <span class="welcome-subtitle">{{ isZh ? '将餐盘放在摄像头下' : 'Place tray under camera' }}</span>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 摄像头区域 -->
      <CameraCapture 
        ref="cameraRef"
        @recognize="handleRecognize"
      />

      <!-- 识别结果提示 -->
      <Transition name="fade">
        <div v-if="recognitionMessage" class="recognition-message" :class="messageType">
          <van-icon :name="messageIcon" />
          <span>{{ recognitionMessage }}</span>
        </div>
      </Transition>

      <!-- 结算面板 -->
      <SettlementPanel 
        @selectManual="showDishSelector = true"
        @paySuccess="handlePaySuccess"
      />

      <!-- 快捷添加按钮 -->
      <div class="quick-actions">
        <button class="quick-btn upload-btn" @click="triggerUpload">
          <van-icon name="photo-o" />
          <span>{{ isZh ? '上传图片识别' : 'Upload Photo' }}</span>
        </button>
        <button class="quick-btn" @click="showDishSelector = true">
          <van-icon name="plus" />
          <span>{{ isZh ? '手动添加' : 'Add Dish' }}</span>
        </button>
        <button class="quick-btn secondary" @click="$router.push('/admin')">
          <van-icon name="manager-o" />
          <span>{{ isZh ? '管理员' : 'Admin' }}</span>
        </button>
      </div>

      <!-- 隐藏的文件上传输入 -->
      <input
        ref="fileInputRef"
        type="file"
        accept="image/jpeg,image/png,image/webp,image/bmp"
        style="display: none"
        @change="handleFileUpload"
      />
    </div>

    <!-- 菜品选择器 -->
    <DishSelector 
      v-model:show="showDishSelector"
      :showManualOnly="dishesStore.hasUnrecognized"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { showToast, showSuccessToast } from 'vant'
import { useDishesStore, useSettingsStore } from '../stores'
import { t } from '../i18n'
import CameraCapture from '../components/CameraCapture.vue'
import SettlementPanel from '../components/SettlementPanel.vue'
import DishSelector from '../components/DishSelector.vue'

const dishesStore = useDishesStore()
const settingsStore = useSettingsStore()

const language = computed(() => settingsStore.language)
const isZh = computed(() => language.value === 'zh')

const cameraRef = ref(null)
const fileInputRef = ref(null)
const showDishSelector = ref(false)
const recognitionMessage = ref('')
const messageType = ref('success')
const messageIcon = computed(() => messageType.value === 'success' ? 'success' : 'warning-o')
const isUploading = ref(false)

// 处理识别结果
async function handleRecognize(imageBase64) {
  try {
    cameraRef.value?.setRecognizing(true)
    
    const result = await dishesStore.recognizeDishes(imageBase64)
    
    if (result.dishes.length > 0) {
      const names = result.dishes.map(d => d.name).join('、')
      recognitionMessage.value = isZh.value 
        ? `识别到：${names}` 
        : `Found: ${names}`
      messageType.value = 'success'
      
      // 语音播报
      settingsStore.speak(recognitionMessage.value)
    } else {
      recognitionMessage.value = isZh.value 
        ? '未识别到菜品，请手动添加' 
        : 'No dishes found, please add manually'
      messageType.value = 'warning'
    }
    
    if (result.unrecognized_count > 0) {
      showDishSelector.value = true
    }
    
    // 3秒后清除消息
    setTimeout(() => {
      recognitionMessage.value = ''
    }, 3000)
    
  } catch (error) {
    showToast(isZh.value ? '识别失败，请重试' : 'Recognition failed')
  } finally {
    cameraRef.value?.setRecognizing(false)
  }
}

// 触发文件上传
function triggerUpload() {
  fileInputRef.value?.click()
}

// 处理文件上传识别
async function handleFileUpload(event) {
  const file = event.target.files?.[0]
  if (!file) return

  // 重置 input 以便再次选择同一文件
  event.target.value = ''

  try {
    isUploading.value = true
    showToast({ message: isZh.value ? '正在识别...' : 'Recognizing...', type: 'loading', duration: 0 })

    const result = await dishesStore.recognizeFromUpload(file)

    // 关闭 loading toast
    showToast({ message: '', duration: 1 })

    if (result.dishes && result.dishes.length > 0) {
      const names = result.dishes.map(d => d.name).join('、')
      recognitionMessage.value = isZh.value
        ? `识别到：${names}`
        : `Found: ${names}`
      messageType.value = 'success'
      settingsStore.speak(recognitionMessage.value)
    } else {
      recognitionMessage.value = isZh.value
        ? '未识别到菜品，请手动添加'
        : 'No dishes found, please add manually'
      messageType.value = 'warning'
    }

    if (result.unrecognized_count > 0) {
      showDishSelector.value = true
    }

    setTimeout(() => {
      recognitionMessage.value = ''
    }, 3000)

  } catch (error) {
    showToast({ message: '', duration: 1 })
    showToast(isZh.value ? '图片识别失败，请重试' : 'Upload recognition failed')
  } finally {
    isUploading.value = false
  }
}

// 结算成功
function handlePaySuccess(order) {
  showSuccessToast({
    message: isZh.value ? '结算成功！' : 'Success!',
    duration: 2000
  })
}

// 加载菜品数据
onMounted(() => {
  dishesStore.loadDishes()
})
</script>

<style scoped>
.customer-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-primary);
  overflow: hidden;
}

.nav-logo {
  font-size: 20px;
}

.nav-actions {
  display: flex;
  gap: var(--space-md);
}

.welcome-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-primary-gradient);
  color: var(--color-text-inverse);
}

.welcome-title {
  font-family: var(--font-display);
  font-size: var(--text-base);
  font-weight: 600;
}

.welcome-sep {
  opacity: 0.6;
}

.welcome-subtitle {
  font-size: var(--text-sm);
  opacity: 0.85;
}

.main-content {
  flex: 1;
  padding: var(--space-sm) var(--space-md);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  overflow-y: auto;
}

.recognition-message {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  font-weight: 500;
  animation: fadeInUp 0.3s ease;
}

.recognition-message.success {
  background: rgba(0, 184, 148, 0.1);
  color: var(--color-success);
}

.recognition-message.warning {
  background: rgba(253, 203, 110, 0.2);
  color: #cc9800;
}

.quick-actions {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
}

.quick-btn {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-md);
  background: var(--color-bg-card);
  color: var(--color-text-primary);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-size: var(--text-base);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.quick-btn:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.quick-btn.upload-btn {
  border-color: var(--color-primary);
  background: var(--color-primary);
  color: #fff;
}

.quick-btn.upload-btn:hover {
  opacity: 0.9;
}

.quick-btn.secondary {
  background: transparent;
}
</style>
