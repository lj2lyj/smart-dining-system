<template>
  <div class="dashboard-view">
    <!-- 顶部导航 -->
    <van-nav-bar 
      :title="isZh ? '管理后台' : 'Dashboard'"
    >
      <template #left>
        <div class="nav-user">
          <van-icon name="manager" size="20" />
          <span>{{ authStore.user?.name }}</span>
        </div>
      </template>
      <template #right>
        <van-icon name="arrow-left" size="20" @click="$router.push('/')" />
      </template>
    </van-nav-bar>

    <div class="page-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card animate-fade-in-up stagger-1">
          <div class="stat-icon orders">
            <van-icon name="orders-o" />
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.today_orders }}</span>
            <span class="stat-label">{{ isZh ? '今日订单' : 'Today Orders' }}</span>
          </div>
        </div>
        
        <div class="stat-card animate-fade-in-up stagger-2">
          <div class="stat-icon revenue">
            <van-icon name="gold-coin-o" />
          </div>
          <div class="stat-info">
            <span class="stat-value">¥{{ Number(stats.today_revenue || 0).toFixed(2) }}</span>
            <span class="stat-label">{{ isZh ? '今日收入' : 'Revenue' }}</span>
          </div>
        </div>
        
        <div class="stat-card animate-fade-in-up stagger-3">
          <div class="stat-icon dishes">
            <van-icon name="shop-o" />
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.total_dishes }}</span>
            <span class="stat-label">{{ isZh ? '菜品总数' : 'Total Dishes' }}</span>
          </div>
        </div>
        
        <div class="stat-card animate-fade-in-up stagger-4" :class="{ 'warning': stats.low_stock_count > 0 }">
          <div class="stat-icon stock">
            <van-icon name="warning-o" />
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.low_stock_count }}</span>
            <span class="stat-label">{{ isZh ? '库存预警' : 'Low Stock' }}</span>
          </div>
        </div>
      </div>

      <!-- 快捷入口 -->
      <h2 class="section-title">{{ isZh ? '快捷管理' : 'Quick Access' }}</h2>
      <div class="menu-grid">
        <div 
          v-for="menu in menuItems" 
          :key="menu.route"
          class="menu-card"
          @click="$router.push(menu.route)"
        >
          <van-icon :name="menu.icon" size="32" :color="menu.color" />
          <span class="menu-label">{{ isZh ? menu.label : menu.labelEn }}</span>
        </div>
      </div>

      <!-- 模型状态 -->
      <h2 class="section-title">{{ isZh ? '系统状态' : 'System Status' }}</h2>
      <div class="model-status card">
        <div class="status-row">
          <span class="status-label">{{ isZh ? 'YOLOv13 模型' : 'YOLOv13 Model' }}</span>
          <van-tag :type="modelStatus.loaded ? 'success' : 'warning'">
            {{ modelStatus.loaded ? (isZh ? '已加载' : 'Loaded') : (isZh ? '模拟模式' : 'Simulation') }}
          </van-tag>
        </div>
        <p class="status-message">{{ modelStatus.message }}</p>
        <van-button 
          v-if="!modelStatus.loaded"
          type="primary" 
          size="small" 
          plain
          @click="showModelInfo = true"
        >
          {{ isZh ? '了解更多' : 'Learn More' }}
        </van-button>
      </div>

      <!-- 登出按钮 -->
      <van-button 
        type="default" 
        block 
        round 
        class="logout-btn"
        @click="handleLogout"
      >
        {{ isZh ? '退出登录' : 'Logout' }}
      </van-button>
    </div>

    <!-- 模型信息弹窗 -->
    <van-dialog 
      v-model:show="showModelInfo"
      :title="isZh ? 'YOLOv13 模型' : 'YOLOv13 Model'"
      :confirm-button-text="isZh ? '知道了' : 'Got it'"
    >
      <div class="model-dialog-content">
        <p>{{ isZh 
          ? '当前系统使用模拟识别模式进行开发测试。真实模型训练完成后，请按以下步骤集成：' 
          : 'Currently using simulation mode. After training, follow these steps:'
        }}</p>
        <ol>
          <li>{{ isZh ? '将训练好的模型文件放到后端项目中' : 'Place model file in backend project' }}</li>
          <li>{{ isZh ? '修改 services/yolo_service.py 中的 MODEL_PATH' : 'Update MODEL_PATH in yolo_service.py' }}</li>
          <li>{{ isZh ? '取消相关代码注释' : 'Uncomment related code' }}</li>
          <li>{{ isZh ? '重启后端服务' : 'Restart backend service' }}</li>
        </ol>
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useSettingsStore } from '../../stores'
import { statsApi, recognitionApi } from '../../api'
import { showConfirmDialog } from 'vant'

const router = useRouter()
const authStore = useAuthStore()
const settingsStore = useSettingsStore()

const isZh = computed(() => settingsStore.language === 'zh')
const showModelInfo = ref(false)

const stats = ref({
  today_orders: 0,
  today_revenue: 0,
  total_dishes: 0,
  low_stock_count: 0
})

const modelStatus = ref({
  loaded: false,
  message: ''
})

const menuItems = [
  { route: '/admin/dishes', icon: 'apps-o', color: '#ff6b35', label: '菜品管理', labelEn: 'Dishes' },
  { route: '/admin/inventory', icon: 'balance-list-o', color: '#00b894', label: '库存管理', labelEn: 'Inventory' },
  { route: '/admin/stats', icon: 'chart-trending-o', color: '#6c5ce7', label: '销售统计', labelEn: 'Statistics' },
  { route: '/history', icon: 'clock-o', color: '#0984e3', label: '历史订单', labelEn: 'Orders' },
  { route: '/admin/promotions', icon: 'coupon-o', color: '#fdcb6e', label: '促销管理', labelEn: 'Promotions' },
  { route: '/admin/settings', icon: 'setting-o', color: '#636e72', label: '系统设置', labelEn: 'Settings' }
]

// 加载数据
async function loadData() {
  try {
    const [dashboardData, recognitionStatus] = await Promise.all([
      statsApi.getDashboard(),
      recognitionApi.getStatus()
    ])
    
    stats.value = dashboardData
    modelStatus.value = recognitionStatus.model
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

// 登出
async function handleLogout() {
  try {
    await showConfirmDialog({
      title: isZh.value ? '确认登出' : 'Confirm Logout',
      message: isZh.value ? '确定要退出登录吗？' : 'Are you sure?'
    })
    
    authStore.logout()
    router.push('/admin')
  } catch {
    // 用户取消
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.dashboard-view {
  min-height: 100vh;
  background: var(--color-bg-primary);
}

.nav-user {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-sm);
}

.page-content {
  padding: var(--space-md);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.stat-card.warning {
  border-left: 3px solid var(--color-danger);
}

.stat-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  font-size: 24px;
}

.stat-icon.orders { background: rgba(255, 107, 53, 0.1); color: var(--color-primary); }
.stat-icon.revenue { background: rgba(0, 184, 148, 0.1); color: var(--color-success); }
.stat-icon.dishes { background: rgba(108, 92, 231, 0.1); color: #6c5ce7; }
.stat-icon.stock { background: rgba(214, 48, 49, 0.1); color: var(--color-danger); }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text-primary);
}

.stat-label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.section-title {
  font-size: var(--text-lg);
  font-weight: 600;
  margin-bottom: var(--space-md);
  color: var(--color-text-primary);
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.menu-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-lg);
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.menu-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.menu-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.model-status {
  margin-bottom: var(--space-xl);
}

.status-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.status-label {
  font-weight: 500;
}

.status-message {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-md);
}

.logout-btn {
  margin-top: var(--space-lg);
}

.model-dialog-content {
  padding: var(--space-md);
  font-size: var(--text-sm);
  line-height: 1.6;
}

.model-dialog-content ol {
  padding-left: var(--space-lg);
  margin-top: var(--space-md);
}

.model-dialog-content li {
  margin-bottom: var(--space-sm);
}
</style>
