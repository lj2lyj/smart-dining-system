<template>
  <div class="history-view">
    <van-nav-bar 
      :title="isZh ? '历史订单' : 'Order History'"
      left-arrow
      @click-left="$router.back()"
    />

    <div class="page-content">
      <!-- 日期筛选 -->
      <div class="date-filter">
        <van-button 
          v-for="option in dateOptions" 
          :key="option.value"
          :type="selectedDate === option.value ? 'primary' : 'default'"
          size="small"
          round
          @click="selectedDate = option.value"
        >
          {{ option.label }}
        </van-button>
      </div>

      <!-- 订单列表 -->
      <van-pull-refresh v-model="refreshing" @refresh="loadOrders">
        <van-list
          v-model:loading="loading"
          :finished="finished"
          :finished-text="isZh ? '没有更多了' : 'No more'"
          @load="loadOrders"
        >
          <div 
            v-for="order in orders" 
            :key="order.id"
            class="order-card animate-fade-in-up"
          >
            <div class="order-header">
              <span class="order-time">
                {{ formatTime(order.created_at) }}
              </span>
              <span class="order-id">{{ order.id.slice(-8) }}</span>
            </div>

            <div class="order-items">
              <div 
                v-for="item in order.items" 
                :key="item.dish_id"
                class="order-item"
              >
                <span class="item-name">{{ item.name }}</span>
                <span class="item-quantity">x{{ item.quantity }}</span>
                <span class="item-price">¥{{ (item.price * item.quantity).toFixed(2) }}</span>
              </div>
            </div>

            <div class="order-footer">
              <span class="order-total-label">{{ isZh ? '合计' : 'Total' }}</span>
              <span class="order-total">¥{{ order.total_amount.toFixed(2) }}</span>
            </div>
          </div>
        </van-list>

        <!-- 空状态 -->
        <van-empty 
          v-if="!loading && orders.length === 0"
          :description="isZh ? '暂无订单记录' : 'No orders yet'"
        />
      </van-pull-refresh>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useSettingsStore } from '../stores'
import { ordersApi } from '../api'

const settingsStore = useSettingsStore()
const isZh = computed(() => settingsStore.language === 'zh')

const orders = ref([])
const loading = ref(false)
const finished = ref(false)
const refreshing = ref(false)
const selectedDate = ref('today')

const dateOptions = computed(() => [
  { value: 'today', label: isZh.value ? '今天' : 'Today' },
  { value: 'week', label: isZh.value ? '本周' : 'Week' },
  { value: 'all', label: isZh.value ? '全部' : 'All' }
])

// 加载订单
async function loadOrders() {
  if (loading.value) return
  
  loading.value = true
  
  try {
    let data
    
    if (selectedDate.value === 'today') {
      data = await ordersApi.getToday()
    } else {
      data = await ordersApi.getAll({ limit: 100 })
    }
    
    orders.value = data
    finished.value = true
    
  } catch (error) {
    console.error('加载订单失败:', error)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 格式化时间
function formatTime(isoString) {
  const date = new Date(isoString)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  
  return `${month}/${day} ${hours}:${minutes}`
}

// 监听日期变化
watch(selectedDate, () => {
  orders.value = []
  finished.value = false
  loadOrders()
})

onMounted(() => {
  loadOrders()
})
</script>

<style scoped>
.history-view {
  min-height: 100vh;
  background: var(--color-bg-primary);
}

.page-content {
  padding: var(--space-md);
}

.date-filter {
  display: flex;
  gap: var(--space-sm);
  margin-bottom: var(--space-lg);
}

.order-card {
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
  box-shadow: var(--shadow-card);
}

.order-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--space-md);
  padding-bottom: var(--space-sm);
  border-bottom: 1px solid var(--color-border);
}

.order-time {
  font-weight: 500;
  color: var(--color-text-primary);
}

.order-id {
  font-size: var(--text-sm);
  color: var(--color-text-light);
}

.order-items {
  margin-bottom: var(--space-md);
}

.order-item {
  display: flex;
  align-items: center;
  padding: var(--space-xs) 0;
}

.item-name {
  flex: 1;
  color: var(--color-text-secondary);
}

.item-quantity {
  margin-right: var(--space-md);
  color: var(--color-text-light);
}

.item-price {
  font-weight: 500;
  color: var(--color-text-primary);
}

.order-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border);
}

.order-total-label {
  color: var(--color-text-secondary);
}

.order-total {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-primary);
}
</style>
