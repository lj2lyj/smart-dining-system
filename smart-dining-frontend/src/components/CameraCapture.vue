<template>
  <div class="camera-capture">
    <!-- 视频预览区域 -->
    <div class="camera-preview" :class="{ 'is-recognizing': isRecognizing }">
      <video 
        ref="videoRef" 
        autoplay 
        playsinline 
        muted
        class="camera-video"
      ></video>
      
      <!-- 识别边框动画 -->
      <div v-if="isRecognizing" class="recognition-overlay">
        <div class="scan-line"></div>
      </div>
      
      <!-- 无摄像头时的占位 -->
      <div v-if="!hasCamera" class="camera-placeholder">
        <van-icon name="photograph" size="48" />
        <p>{{ isZh ? '无法访问摄像头' : 'Camera Unavailable' }}</p>
        <van-button size="small" @click="initCamera">
          {{ isZh ? '重试' : 'Retry' }}
        </van-button>
      </div>
    </div>

    <!-- 拍照画布（隐藏） -->
    <canvas ref="canvasRef" class="capture-canvas"></canvas>

    <!-- 控制区域 -->
    <div class="camera-controls">
      <!-- 识别按钮 -->
      <button 
        class="recognize-btn" 
        :class="{ 'is-loading': isRecognizing }"
        :disabled="isRecognizing || !hasCamera"
        @click="captureAndRecognize"
      >
        <span v-if="!isRecognizing" class="btn-content">
          <van-icon name="scan" size="24" />
          <span>{{ isZh ? '识别菜品' : 'Recognize' }}</span>
        </span>
        <span v-else class="btn-content">
          <van-loading type="spinner" size="20" color="#fff" />
          <span>{{ isZh ? '识别中...' : 'Processing...' }}</span>
        </span>
      </button>

      <!-- 自动识别开关 -->
      <div class="auto-recognize" v-if="showAutoToggle">
        <span class="auto-label">{{ isZh ? '自动识别' : 'Auto' }}</span>
        <van-switch 
          v-model="autoEnabled" 
          size="20"
          @change="toggleAutoRecognize"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useSettingsStore } from '../stores/settings'

const props = defineProps({
  showAutoToggle: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['capture', 'recognize'])

const settingsStore = useSettingsStore()
const isZh = computed(() => settingsStore.language === 'zh')

// Refs
const videoRef = ref(null)
const canvasRef = ref(null)
const hasCamera = ref(false)
const isRecognizing = ref(false)
const autoEnabled = ref(settingsStore.autoRecognizeEnabled)
let stream = null
let autoTimer = null

// 初始化摄像头
async function initCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: {
        facingMode: 'environment', // 优先使用后置摄像头
        width: { ideal: 1280 },
        height: { ideal: 720 }
      },
      audio: false
    })
    
    if (videoRef.value) {
      videoRef.value.srcObject = stream
      hasCamera.value = true
    }
  } catch (error) {
    console.error('摄像头初始化失败:', error)
    hasCamera.value = false
  }
}

// 关闭摄像头
function stopCamera() {
  if (stream) {
    stream.getTracks().forEach(track => track.stop())
    stream = null
  }
}

// 截取当前帧
function captureFrame() {
  if (!videoRef.value || !canvasRef.value) return null
  
  const video = videoRef.value
  const canvas = canvasRef.value
  
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0)
  
  return canvas.toDataURL('image/jpeg', 0.8)
}

// 截取并识别
async function captureAndRecognize() {
  if (isRecognizing.value) return
  
  isRecognizing.value = true
  
  try {
    const imageBase64 = captureFrame()
    
    if (imageBase64) {
      emit('capture', imageBase64)
      emit('recognize', imageBase64)
    }
  } finally {
    isRecognizing.value = false
  }
}

// 切换自动识别
function toggleAutoRecognize(enabled) {
  settingsStore.autoRecognizeEnabled = enabled
  
  if (enabled) {
    startAutoRecognize()
  } else {
    stopAutoRecognize()
  }
}

// 开始自动识别
function startAutoRecognize() {
  if (autoTimer) return
  
  autoTimer = setInterval(() => {
    if (!isRecognizing.value && hasCamera.value) {
      captureAndRecognize()
    }
  }, settingsStore.autoRecognizeInterval)
}

// 停止自动识别
function stopAutoRecognize() {
  if (autoTimer) {
    clearInterval(autoTimer)
    autoTimer = null
  }
}

// 监听自动识别状态
watch(() => settingsStore.autoRecognizeEnabled, (enabled) => {
  autoEnabled.value = enabled
})

// 暴露方法给父组件
defineExpose({
  setRecognizing: (value) => { isRecognizing.value = value },
  captureFrame
})

onMounted(() => {
  initCamera()
  
  if (settingsStore.autoRecognizeEnabled) {
    startAutoRecognize()
  }
})

onUnmounted(() => {
  stopCamera()
  stopAutoRecognize()
})
</script>

<style scoped>
.camera-capture {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.camera-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: var(--color-secondary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-md);
}

.camera-preview.is-recognizing {
  animation: recognitionPulse 1.5s ease-out infinite;
}

.camera-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.recognition-overlay {
  position: absolute;
  inset: 0;
  border: 3px solid var(--color-primary);
  border-radius: inherit;
  pointer-events: none;
}

.scan-line {
  position: absolute;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    var(--color-primary) 50%,
    transparent 100%
  );
  animation: scanDown 1.5s ease-in-out infinite;
}

@keyframes scanDown {
  0%, 100% {
    top: 10%;
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    top: 90%;
    opacity: 0;
  }
}

.camera-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  background: var(--color-bg-secondary);
  color: var(--color-text-secondary);
}

.capture-canvas {
  display: none;
}

.camera-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-lg);
}

.recognize-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 140px;
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-primary-gradient);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-full);
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.recognize-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-float);
  transform: translateY(-2px);
}

.recognize-btn:active:not(:disabled) {
  transform: translateY(0);
}

.recognize-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.recognize-btn.is-loading {
  background: var(--color-primary-dark);
}

.btn-content {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.auto-recognize {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-card);
  border-radius: var(--radius-full);
  box-shadow: var(--shadow-sm);
}

.auto-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}
</style>
