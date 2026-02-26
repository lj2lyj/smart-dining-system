<template>
  <div class="inventory-view">
    <van-nav-bar 
      :title="isZh ? '库存管理' : 'Inventory'"
      left-arrow
      @click-left="$router.back()"
    />

    <div class="page-content">
      <!-- 低库存预警 -->
      <div v-if="lowStockItems.length > 0" class="low-stock-alert">
        <van-icon name="warning-o" color="var(--color-danger)" />
        <span>{{ lowStockItems.length }} {{ isZh ? '个菜品库存不足' : 'items low stock' }}</span>
      </div>

      <!-- 库存列表 -->
      <van-pull-refresh v-model="refreshing" @refresh="loadInventory">
        <div class="inventory-list">
          <div 
            v-for="item in inventory" 
            :key="item.id"
            class="inventory-item"
            :class="{ 'low-stock': item.stock < 20 }"
          >
            <div class="item-info">
              <span class="item-name">{{ item.name }}</span>
              <van-tag v-if="item.stock < 10" type="danger" size="small">
                {{ isZh ? '紧急' : 'Critical' }}
              </van-tag>
              <van-tag v-else-if="item.stock < 20" type="warning" size="small">
                {{ isZh ? '偏低' : 'Low' }}
              </van-tag>
            </div>
            
            <div class="item-actions">
              <span class="item-stock">{{ item.stock }}</span>
              <div class="action-buttons">
                <van-button 
                  size="small" 
                  type="primary"
                  plain
                  @click="quickRestock(item, 10)"
                >
                  +10
                </van-button>
                <van-button 
                  size="small" 
                  type="primary"
                  plain
                  @click="quickRestock(item, 50)"
                >
                  +50
                </van-button>
                <van-button 
                  size="small"
                  @click="showCustomRestock(item)"
                >
                  {{ isZh ? '自定义' : 'Custom' }}
                </van-button>
              </div>
            </div>
          </div>
        </div>
      </van-pull-refresh>
    </div>

    <!-- 自定义补货弹窗 -->
    <van-dialog
      v-model:show="showRestockDialog"
      :title="isZh ? '补货' : 'Restock'"
      show-cancel-button
      @confirm="confirmRestock"
    >
      <div class="restock-content">
        <p>{{ restockItem?.name }}</p>
        <van-stepper v-model="restockAmount" min="1" max="999" />
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../../stores'
import { inventoryApi } from '../../api'
import { showToast } from 'vant'

const settingsStore = useSettingsStore()
const isZh = computed(() => settingsStore.language === 'zh')

const inventory = ref([])
const refreshing = ref(false)
const showRestockDialog = ref(false)
const restockItem = ref(null)
const restockAmount = ref(10)

const lowStockItems = computed(() => inventory.value.filter(i => i.stock < 20))

async function loadInventory() {
  try {
    inventory.value = await inventoryApi.getAll()
  } catch (error) {
    showToast(isZh.value ? '加载失败' : 'Load failed')
  } finally {
    refreshing.value = false
  }
}

async function quickRestock(item, amount) {
  try {
    await inventoryApi.restock(item.id, amount)
    showToast({ message: `+${amount}`, icon: 'success' })
    loadInventory()
  } catch (error) {
    showToast(isZh.value ? '补货失败' : 'Restock failed')
  }
}

function showCustomRestock(item) {
  restockItem.value = item
  restockAmount.value = 10
  showRestockDialog.value = true
}

async function confirmRestock() {
  if (restockItem.value) {
    await quickRestock(restockItem.value, restockAmount.value)
  }
}

onMounted(() => { loadInventory() })
</script>

<style scoped>
.inventory-view { min-height: 100vh; background: var(--color-bg-primary); }
.page-content { padding: var(--space-md); }
.low-stock-alert { display: flex; align-items: center; gap: var(--space-sm); padding: var(--space-md); background: rgba(214, 48, 49, 0.1); border-radius: var(--radius-md); margin-bottom: var(--space-md); color: var(--color-danger); }
.inventory-item { display: flex; justify-content: space-between; align-items: center; padding: var(--space-md); background: var(--color-bg-card); border-radius: var(--radius-md); margin-bottom: var(--space-sm); }
.inventory-item.low-stock { border-left: 3px solid var(--color-warning); }
.item-info { display: flex; align-items: center; gap: var(--space-sm); }
.item-name { font-weight: 500; }
.item-actions { display: flex; align-items: center; gap: var(--space-md); }
.item-stock { font-size: var(--text-xl); font-weight: 700; color: var(--color-primary); min-width: 40px; text-align: center; }
.action-buttons { display: flex; gap: var(--space-xs); }
.restock-content { padding: var(--space-lg); text-align: center; }
.restock-content p { margin-bottom: var(--space-md); font-weight: 500; }
</style>
