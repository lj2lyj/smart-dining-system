<template>
  <van-popup 
    v-model:show="visible" 
    position="bottom"
    round
    :style="{ maxHeight: '70vh' }"
  >
    <div class="dish-selector">
      <!-- 头部 -->
      <div class="selector-header">
        <h3>{{ isZh ? '手动选择菜品' : 'Select Dishes' }}</h3>
        <van-icon name="cross" size="20" @click="visible = false" />
      </div>

      <!-- 搜索栏 -->
      <div class="selector-search">
        <van-field 
          v-model="searchText"
          :placeholder="isZh ? '搜索菜品名称' : 'Search dishes'"
          left-icon="search"
          clearable
        />
      </div>

      <!-- 分类标签 -->
      <div class="category-tabs">
        <van-tabs v-model:active="activeCategory" shrink>
          <van-tab :title="isZh ? '全部' : 'All'" name="all" />
          <van-tab :title="isZh ? '主食' : 'Staple'" name="staple" />
          <van-tab :title="isZh ? '荤菜' : 'Meat'" name="meat" />
          <van-tab :title="isZh ? '素菜' : 'Vegetable'" name="vegetable" />
          <van-tab :title="isZh ? '汤类' : 'Soup'" name="soup" />
          <van-tab :title="isZh ? '饮品' : 'Drink'" name="drink" />
          <van-tab :title="isZh ? '其他' : 'Other'" name="other" />
        </van-tabs>
      </div>

      <!-- 菜品列表 -->
      <div class="dishes-list">
        <div 
          v-for="dish in filteredDishes" 
          :key="dish.id"
          class="dish-card"
          :class="{ 'is-unavailable': !dish.is_available || dish.stock <= 0 }"
          @click="selectDish(dish)"
        >
          <div class="dish-image">
            <van-image 
              v-if="dish.image_url"
              :src="dish.image_url" 
              width="60" 
              height="60"
              fit="cover"
              radius="8"
            />
            <div v-else class="dish-placeholder">
              <van-icon name="photo-o" size="24" />
            </div>
          </div>
          
          <div class="dish-info">
            <div class="dish-name">{{ dish.name }}</div>
            <div class="dish-meta">
              <span class="dish-price">¥{{ dish.price.toFixed(2) }}</span>
              <van-tag v-if="dish.source === 'manual'" type="primary" size="small">
                {{ isZh ? '手动库' : 'Manual' }}
              </van-tag>
              <van-tag v-if="dish.stock <= 10 && dish.stock > 0" type="warning" size="small">
                {{ isZh ? '库存紧张' : 'Low Stock' }}
              </van-tag>
              <van-tag v-if="dish.stock <= 0" type="danger" size="small">
                {{ isZh ? '已售罄' : 'Sold Out' }}
              </van-tag>
            </div>
            <!-- 过敏原警告 -->
            <div v-if="hasAllergenWarning(dish)" class="allergen-warning">
              <van-icon name="warning-o" color="var(--color-danger)" />
              <span>{{ isZh ? '含有您设置的过敏原' : 'Contains allergen' }}</span>
            </div>
          </div>
          
          <van-icon 
            v-if="dish.is_available && dish.stock > 0"
            name="add-o" 
            size="28" 
            color="var(--color-primary)"
            class="add-icon"
          />
        </div>

        <!-- 空状态 -->
        <van-empty 
          v-if="filteredDishes.length === 0"
          :description="isZh ? '没有找到菜品' : 'No dishes found'"
        />
      </div>
    </div>
  </van-popup>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useDishesStore, useSettingsStore } from '../stores'
import { showToast } from 'vant'

const props = defineProps({
  show: Boolean,
  showManualOnly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:show', 'select'])

const dishesStore = useDishesStore()
const settingsStore = useSettingsStore()

const isZh = computed(() => settingsStore.language === 'zh')
const visible = computed({
  get: () => props.show,
  set: (val) => emit('update:show', val)
})

const searchText = ref('')
const activeCategory = ref('all')

// 过滤菜品
const filteredDishes = computed(() => {
  let dishes = props.showManualOnly 
    ? dishesStore.manualDishes 
    : dishesStore.allDishes
  
  // 按分类筛选
  if (activeCategory.value !== 'all') {
    dishes = dishes.filter(d => d.category === activeCategory.value)
  }
  
  // 按搜索词筛选
  if (searchText.value) {
    const keyword = searchText.value.toLowerCase()
    dishes = dishes.filter(d => 
      d.name.toLowerCase().includes(keyword) ||
      (d.name_en && d.name_en.toLowerCase().includes(keyword))
    )
  }
  
  return dishes
})

// 检查过敏原
function hasAllergenWarning(dish) {
  if (!dish.allergens || dish.allergens.length === 0) return false
  
  const userAllergens = settingsStore.allergens
  return dish.allergens.some(a => userAllergens.includes(a))
}

// 选择菜品
function selectDish(dish) {
  if (!dish.is_available || dish.stock <= 0) {
    showToast(isZh.value ? '该菜品暂时不可用' : 'Dish unavailable')
    return
  }
  
  dishesStore.addManualDish(dish)
  
  // 语音播报
  settingsStore.speak(isZh.value ? `已添加${dish.name}` : `Added ${dish.name_en || dish.name}`)
  
  showToast({
    message: isZh.value ? `已添加 ${dish.name}` : `Added ${dish.name}`,
    icon: 'success'
  })
  
  emit('select', dish)
}

// 加载菜品数据
watch(visible, (val) => {
  if (val && dishesStore.allDishes.length === 0) {
    dishesStore.loadDishes()
  }
})
</script>

<style scoped>
.dish-selector {
  display: flex;
  flex-direction: column;
  max-height: 70vh;
}

.selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}

.selector-header h3 {
  font-size: var(--text-lg);
  font-weight: 600;
}

.selector-search {
  padding: var(--space-sm) var(--space-md);
}

.category-tabs {
  border-bottom: 1px solid var(--color-border);
}

.dishes-list {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-md);
}

.dish-card {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-sm);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.dish-card:hover:not(.is-unavailable) {
  background: var(--color-bg-card);
  box-shadow: var(--shadow-sm);
}

.dish-card.is-unavailable {
  opacity: 0.6;
  cursor: not-allowed;
}

.dish-image {
  flex-shrink: 0;
}

.dish-placeholder {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-border);
  border-radius: var(--radius-sm);
  color: var(--color-text-light);
}

.dish-info {
  flex: 1;
  min-width: 0;
}

.dish-name {
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: var(--space-xs);
}

.dish-meta {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  flex-wrap: wrap;
}

.dish-price {
  font-weight: 600;
  color: var(--color-primary);
}

.allergen-warning {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  margin-top: var(--space-xs);
  font-size: var(--text-xs);
  color: var(--color-danger);
}

.add-icon {
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.dish-card:hover .add-icon {
  transform: scale(1.1);
}
</style>
