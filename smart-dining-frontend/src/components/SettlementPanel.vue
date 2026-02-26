<template>
  <div class="settlement-panel">
    <!-- 面板头部 -->
    <div class="panel-header">
      <h3 class="panel-title">
        <van-icon name="cart-o" />
        <span>{{ isZh ? '待结算' : 'Cart' }}</span>
        <van-badge v-if="cartItemCount > 0" :content="cartItemCount" />
      </h3>
      <button 
        v-if="cartItemCount > 0" 
        class="clear-btn"
        @click="handleClear"
      >
        {{ isZh ? '清空' : 'Clear' }}
      </button>
    </div>

    <!-- 购物车列表 -->
    <div v-if="cartItemCount > 0" class="cart-list">
      <TransitionGroup name="cart-item">
        <div 
          v-for="item in cartItems" 
          :key="item.dish_id"
          class="cart-item"
          :class="{ 'low-confidence': item.confidence && item.confidence < 0.8 }"
        >
          <div class="item-info">
            <span class="item-name">{{ item.name }}</span>
            <div class="item-meta">
              <span class="item-price">¥{{ item.price.toFixed(2) }}</span>
              <van-tag 
                v-if="item.confidence && item.confidence < 0.8" 
                type="warning" 
                size="small"
              >
                {{ isZh ? '请确认' : 'Confirm' }}
              </van-tag>
              <van-tag 
                v-if="item.is_manual" 
                type="primary" 
                size="small"
              >
                {{ isZh ? '手动添加' : 'Manual' }}
              </van-tag>
            </div>
          </div>
          
          <div class="item-actions">
            <van-stepper 
              :model-value="item.quantity"
              @change="(val) => updateQuantity(item.dish_id, val)"
              theme="round"
              button-size="24"
              min="0"
            />
            <span class="item-subtotal">
              ¥{{ (item.price * item.quantity).toFixed(2) }}
            </span>
          </div>
        </div>
      </TransitionGroup>
    </div>

    <!-- 空状态 -->
    <div v-else class="cart-empty">
      <van-icon name="shopping-cart-o" size="48" color="var(--color-text-light)" />
      <p>{{ isZh ? '请先识别或添加菜品' : 'Scan or add dishes' }}</p>
    </div>

    <!-- 未识别菜品提示 -->
    <Transition name="slide-up">
      <div v-if="hasUnrecognized" class="unrecognized-alert" @click="$emit('selectManual')">
        <van-icon name="warning-o" color="var(--color-warning)" />
        <span>{{ isZh ? '有未识别菜品，点击手动选择' : 'Unrecognized items, tap to select' }}</span>
        <van-icon name="arrow" />
      </div>
    </Transition>

    <!-- 营养信息摘要 -->
    <Transition name="fade">
      <div v-if="cartItemCount > 0 && showNutrition" class="nutrition-summary">
        <div class="nutrition-item">
          <span class="nutrition-value">{{ totalNutrition.calories }}</span>
          <span class="nutrition-label">{{ isZh ? '卡路里' : 'kcal' }}</span>
        </div>
        <div class="nutrition-item">
          <span class="nutrition-value">{{ totalNutrition.protein }}g</span>
          <span class="nutrition-label">{{ isZh ? '蛋白质' : 'Protein' }}</span>
        </div>
        <div class="nutrition-item">
          <span class="nutrition-value">{{ totalNutrition.carbs }}g</span>
          <span class="nutrition-label">{{ isZh ? '碳水' : 'Carbs' }}</span>
        </div>
        <div class="nutrition-item">
          <span class="nutrition-value">{{ totalNutrition.fat }}g</span>
          <span class="nutrition-label">{{ isZh ? '脂肪' : 'Fat' }}</span>
        </div>
      </div>
    </Transition>

    <!-- 结算区域 -->
    <div class="settlement-footer">
      <div class="total-section">
        <span class="total-label">{{ isZh ? '合计' : 'Total' }}</span>
        <span class="total-amount">
          <span class="currency">¥</span>
          <span class="amount">{{ cartTotal.toFixed(2) }}</span>
        </span>
      </div>
      
      <button 
        class="pay-btn"
        :disabled="cartItemCount === 0"
        @click="showPaymentDialog = true"
      >
        <span>{{ isZh ? '立即结算' : 'Pay Now' }}</span>
        <van-icon name="arrow" />
      </button>
    </div>

    <!-- 支付方式弹窗 -->
    <van-popup v-model:show="showPaymentDialog" position="bottom" round>
      <div class="payment-dialog">
        <h3 class="payment-title">{{ isZh ? '选择支付方式' : 'Select Payment' }}</h3>
        
        <div class="payment-methods">
          <div 
            v-for="method in paymentMethods" 
            :key="method.id"
            class="payment-method"
            :class="{ active: selectedMethod === method.id }"
            @click="selectedMethod = method.id"
          >
            <div class="method-icon" :class="method.id">
              <span v-if="method.id === 'alipay'">💱</span>
              <span v-else>📱</span>
            </div>
            <div class="method-info">
              <span class="method-name">{{ isZh ? method.name : method.name_en }}</span>
              <van-tag v-if="method.mock" type="warning" size="small">模拟</van-tag>
            </div>
            <van-icon v-if="selectedMethod === method.id" name="success" color="var(--color-primary)" />
          </div>
        </div>
        
        <div class="payment-actions">
          <van-button block type="primary" :loading="paying" @click="confirmPay">
            {{ isZh ? `支付 ¥${cartTotal.toFixed(2)}` : `Pay ¥${cartTotal.toFixed(2)}` }}
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- 二维码弹窗 -->
    <van-popup v-model:show="showQrCode" :close-on-click-overlay="false">
      <div class="qrcode-dialog">
        <h3>{{ isZh ? '请扫码支付' : 'Scan to Pay' }}</h3>
        <div class="qrcode-wrapper">
          <img v-if="qrCodeDataUrl" :src="qrCodeDataUrl" alt="QR Code" />
          <van-loading v-else type="spinner" />
        </div>
        <p class="qrcode-amount">¥{{ cartTotal.toFixed(2) }}</p>
        <p class="qrcode-hint">{{ isZh ? '支付完成后自动跳转' : 'Auto redirect after payment' }}</p>
        <van-button plain size="small" @click="cancelPayment">
          {{ isZh ? '取消支付' : 'Cancel' }}
        </van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onUnmounted } from 'vue'
import { useDishesStore, useSettingsStore } from '../stores'
import { showConfirmDialog, showSuccessToast, showToast } from 'vant'
import { ordersApi, paymentApi } from '../api'

const props = defineProps({
  showNutrition: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['selectManual', 'paySuccess'])

const dishesStore = useDishesStore()
const settingsStore = useSettingsStore()

const isZh = computed(() => settingsStore.language === 'zh')
const cartItems = computed(() => dishesStore.cartItems)
const cartTotal = computed(() => dishesStore.cartTotal)
const cartItemCount = computed(() => dishesStore.cartItemCount)
const hasUnrecognized = computed(() => dishesStore.hasUnrecognized)

// 支付相关状态
const showPaymentDialog = ref(false)
const showQrCode = ref(false)
const paying = ref(false)
const selectedMethod = ref('alipay')
const qrCodeDataUrl = ref('')
const currentPaymentId = ref('')
let pollTimer = null

// 支付方式（默认模拟）
const paymentMethods = ref([
  { id: 'alipay', name: '支付宝', name_en: 'Alipay', mock: true },
  { id: 'wechat', name: '微信支付', name_en: 'WeChat Pay', mock: true }
])

// 加载真实支付方式配置
async function loadPaymentMethods() {
  try {
    const res = await paymentApi.getMethods()
    if (res.methods) {
      paymentMethods.value = res.methods
    }
  } catch (e) {
    console.log('使用默认支付方式')
  }
}

// 计算总营养
const totalNutrition = computed(() => {
  const totals = { calories: 0, protein: 0, carbs: 0, fat: 0 }
  
  for (const item of cartItems.value) {
    const dish = dishesStore.allDishes.find(d => d.id === item.dish_id)
    if (dish?.nutrition) {
      totals.calories += (dish.nutrition.calories || 0) * item.quantity
      totals.protein += (dish.nutrition.protein || 0) * item.quantity
      totals.carbs += (dish.nutrition.carbohydrates || 0) * item.quantity
      totals.fat += (dish.nutrition.fat || 0) * item.quantity
    }
  }
  
  return {
    calories: Math.round(totals.calories),
    protein: Math.round(totals.protein),
    carbs: Math.round(totals.carbs),
    fat: Math.round(totals.fat)
  }
})

// 更新数量
function updateQuantity(dishId, quantity) {
  dishesStore.updateCartQuantity(dishId, quantity)
}

// 清空购物车
async function handleClear() {
  try {
    await showConfirmDialog({
      title: isZh.value ? '确认清空' : 'Clear Cart',
      message: isZh.value ? '确定要清空所有菜品吗？' : 'Clear all items?'
    })
    dishesStore.clearCart()
  } catch {
    // 用户取消
  }
}

// 确认支付
async function confirmPay() {
  if (cartItemCount.value === 0) return
  
  paying.value = true
  
  try {
    // 1. 先创建业务订单
    const order = await ordersApi.create({
      items: cartItems.value,
      total_amount: cartTotal.value,
      recognition_log_id: dishesStore.lastRecognitionLogId
    })
    
    // 2. 创建支付订单
    const payResult = await paymentApi.create(
      order.id,
      cartTotal.value,
      isZh.value ? '智慧餐饮订单' : 'Smart Dining Order',
      selectedMethod.value
    )
    
    if (payResult.success) {
      showPaymentDialog.value = false
      currentPaymentId.value = payResult.payment_id
      
      // 3. 生成二维码
      await generateQrCode(payResult.qr_code || payResult.code_url)
      showQrCode.value = true
      
      // 4. 开始轮询支付状态
      startPolling(order)
    } else {
      showToast(payResult.message || (isZh.value ? '创建支付失败' : 'Payment failed'))
    }
    
  } catch (error) {
    console.error('支付失败:', error)
    showToast(isZh.value ? '支付失败，请重试' : 'Payment failed')
  } finally {
    paying.value = false
  }
}

// 生成二维码
async function generateQrCode(content) {
  // 使用在线服务生成二维码（生产环境建议使用 qrcode 库）
  qrCodeDataUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(content)}`
}

// 开始轮询支付状态
function startPolling(order) {
  pollTimer = setInterval(async () => {
    try {
      const result = await paymentApi.query(currentPaymentId.value)
      
      if (result.status === 'paid') {
        stopPolling()
        handlePaymentSuccess(order)
      }
    } catch (e) {
      console.error('查询支付状态失败:', e)
    }
  }, 2000) // 每2秒查询一次
}

// 停止轮询
function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// 支付成功处理
function handlePaymentSuccess(order) {
  showQrCode.value = false
  
  // 语音播报
  settingsStore.speak(
    isZh.value 
      ? `支付成功，共${cartTotal.value.toFixed(2)}元` 
      : `Payment complete, total ${cartTotal.value.toFixed(2)} yuan`
  )
  
  showSuccessToast(isZh.value ? '支付成功' : 'Payment Complete')
  
  // 清空购物车
  dishesStore.clearCart()
  
  emit('paySuccess', order)
}

// 取消支付
function cancelPayment() {
  stopPolling()
  showQrCode.value = false
  currentPaymentId.value = ''
  qrCodeDataUrl.value = ''
}

// 组件卸载时清理
onUnmounted(() => {
  stopPolling()
})

// 初始化
loadPaymentMethods()
</script>

<style scoped>
.settlement-panel {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  flex: 1;
  min-height: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--color-border);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-primary);
}

.clear-btn {
  padding: var(--space-xs) var(--space-md);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.clear-btn:hover {
  color: var(--color-danger);
  border-color: var(--color-danger);
}

.cart-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-xs);
}

.cart-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  margin-bottom: var(--space-xs);
  transition: all var(--transition-fast);
}

.cart-item.low-confidence {
  border-left: 3px solid var(--color-warning);
}

.cart-item:last-child {
  margin-bottom: 0;
}

.item-info {
  flex: 1;
}

.item-name {
  font-weight: 500;
  color: var(--color-text-primary);
}

.item-meta {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
}

.item-price {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.item-actions {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.item-subtotal {
  min-width: 60px;
  text-align: right;
  font-weight: 600;
  color: var(--color-primary);
}

.cart-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  padding: var(--space-lg);
  color: var(--color-text-light);
  flex: 1;
}

.unrecognized-alert {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: rgba(253, 203, 110, 0.15);
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.unrecognized-alert:hover {
  background: rgba(253, 203, 110, 0.25);
}

.nutrition-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-sm);
  padding: var(--space-md) var(--space-lg);
  background: var(--color-bg-secondary);
  border-top: 1px solid var(--color-border);
}

.nutrition-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.nutrition-value {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-primary);
}

.nutrition-label {
  font-size: var(--text-xs);
  color: var(--color-text-secondary);
}

.settlement-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-sm) var(--space-md);
  background: var(--color-bg-primary);
  border-top: 1px solid var(--color-border);
}

.total-section {
  display: flex;
  flex-direction: column;
}

.total-label {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.total-amount {
  font-family: var(--font-display);
  color: var(--color-primary);
}

.total-amount .currency {
  font-size: var(--text-lg);
}

.total-amount .amount {
  font-size: var(--text-xl);
  font-weight: 700;
}

.pay-btn {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-sm) var(--space-lg);
  background: var(--color-primary-gradient);
  color: var(--color-text-inverse);
  border: none;
  border-radius: var(--radius-full);
  font-size: var(--text-base);
  font-weight: 600;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
}

.pay-btn:hover:not(:disabled) {
  box-shadow: var(--shadow-float);
  transform: translateY(-2px);
}

.pay-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 过渡动画 */
.cart-item-enter-active,
.cart-item-leave-active {
  transition: all 0.3s ease;
}

.cart-item-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.cart-item-leave-to {
  opacity: 0;
  transform: translateX(20px);
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
