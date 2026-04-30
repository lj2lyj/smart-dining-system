<template>
  <div class="dishes-view">
    <van-nav-bar 
      :title="isZh ? '菜品管理' : 'Dish Management'"
      left-arrow
      @click-left="$router.back()"
    >
      <template #right>
        <van-icon name="plus" size="20" @click="showAddDialog = true" />
      </template>
    </van-nav-bar>

    <div class="page-content">
      <!-- 分类筛选 -->
      <van-tabs v-model:active="activeSource" shrink>
        <van-tab :title="isZh ? '全部' : 'All'" name="all" />
        <van-tab :title="isZh ? 'YOLO识别' : 'YOLO'" name="yolo" />
        <van-tab :title="isZh ? '手动库' : 'Manual'" name="manual" />
      </van-tabs>

      <!-- 菜品列表 -->
      <van-pull-refresh v-model="refreshing" @refresh="loadDishes">
        <div class="dishes-list">
          <van-swipe-cell 
            v-for="dish in filteredDishes" 
            :key="dish.id"
          >
            <div class="dish-item" @click="editDish(dish)">
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
                  <span class="dish-price">¥{{ Number(dish.price || 0).toFixed(2) }}</span>
                  <van-tag :type="dish.source === 'yolo' ? 'success' : 'primary'" size="small">
                    {{ dish.source === 'yolo' ? 'YOLO' : (isZh ? '手动' : 'Manual') }}
                  </van-tag>
                  <van-tag v-if="dish.stock <= 10" type="warning" size="small">
                    {{ isZh ? '库存:' : 'Stock:' }}{{ dish.stock }}
                  </van-tag>
                </div>
              </div>
              
              <van-button
                v-if="dish.source === 'manual'"
                type="danger"
                size="small"
                plain
                icon="delete-o"
                @click.stop="deleteDish(dish)"
              >
                {{ isZh ? '删除' : 'Delete' }}
              </van-button>
              <van-icon v-else name="arrow" color="var(--color-text-light)" />
            </div>
            
            <template #right>
              <van-button 
                square 
                type="danger" 
                text="删除"
                class="swipe-btn"
                @click="deleteDish(dish)"
              />
            </template>
          </van-swipe-cell>

          <van-empty 
            v-if="filteredDishes.length === 0 && !loading"
            :description="isZh ? '暂无菜品' : 'No dishes'"
          />
        </div>
      </van-pull-refresh>
    </div>

    <!-- 添加/编辑对话框 -->
    <van-popup 
      v-model:show="showAddDialog" 
      position="bottom" 
      round
      :style="{ maxHeight: '80vh' }"
    >
      <div class="dish-form">
        <div class="form-header">
          <h3>{{ editingDish ? (isZh ? '编辑菜品' : 'Edit Dish') : (isZh ? '添加菜品' : 'Add Dish') }}</h3>
          <van-icon name="cross" @click="closeForm" />
        </div>

        <van-form @submit="saveDish">
          <van-cell-group inset>
            <van-field
              v-model="formData.name"
              :label="isZh ? '名称' : 'Name'"
              :placeholder="isZh ? '请输入菜品名称' : 'Dish name'"
              required
              :rules="[{ required: true }]"
            />
            <van-field
              v-model="formData.name_en"
              :label="isZh ? '英文名' : 'English'"
              :placeholder="isZh ? '可选' : 'Optional'"
            />
            <van-field
              v-model="formData.price"
              type="number"
              :label="isZh ? '价格' : 'Price'"
              placeholder="0.00"
              required
              :rules="[{ required: true }]"
            />
            <van-field
              :label="isZh ? '分类' : 'Category'"
              :model-value="getCategoryLabel(formData.category)"
              is-link
              readonly
              @click="showCategoryPicker = true"
            />
            <van-field
              v-model="formData.description"
              type="textarea"
              :label="isZh ? '描述' : 'Description'"
              rows="2"
              :placeholder="isZh ? '可选' : 'Optional'"
            />
            <van-field
              v-model="formData.stock"
              type="digit"
              :label="isZh ? '库存' : 'Stock'"
              placeholder="100"
            />
          </van-cell-group>

          <!-- 营养信息 -->
          <h4 class="form-section-title">{{ isZh ? '营养信息（可选）' : 'Nutrition (Optional)' }}</h4>
          <van-cell-group inset>
            <van-field v-model="formData.nutrition.calories" type="number" :label="isZh ? '卡路里' : 'Calories'" />
            <van-field v-model="formData.nutrition.protein" type="number" :label="isZh ? '蛋白质(g)' : 'Protein(g)'" />
            <van-field v-model="formData.nutrition.carbohydrates" type="number" :label="isZh ? '碳水(g)' : 'Carbs(g)'" />
            <van-field v-model="formData.nutrition.fat" type="number" :label="isZh ? '脂肪(g)' : 'Fat(g)'" />
          </van-cell-group>

          <div class="form-actions">
            <van-button block type="primary" native-type="submit" :loading="saving">
              {{ isZh ? '保存' : 'Save' }}
            </van-button>
          </div>
        </van-form>
      </div>
    </van-popup>

    <!-- 分类选择器 -->
    <van-popup v-model:show="showCategoryPicker" position="bottom" round>
      <van-picker
        :columns="categoryColumns"
        @confirm="onCategoryConfirm"
        @cancel="showCategoryPicker = false"
      />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../../stores'
import { dishesApi } from '../../api'
import { showToast, showConfirmDialog } from 'vant'

const settingsStore = useSettingsStore()
const isZh = computed(() => settingsStore.language === 'zh')

const dishes = ref([])
const loading = ref(false)
const refreshing = ref(false)
const saving = ref(false)
const activeSource = ref('all')
const showAddDialog = ref(false)
const showCategoryPicker = ref(false)
const editingDish = ref(null)

const defaultFormData = {
  name: '',
  name_en: '',
  price: '',
  category: 'other',
  description: '',
  stock: 100,
  nutrition: { calories: '', protein: '', carbohydrates: '', fat: '' }
}

const formData = ref({ ...defaultFormData })

const categoryColumns = [
  { text: '主食', value: 'staple' },
  { text: '荤菜', value: 'meat' },
  { text: '素菜', value: 'vegetable' },
  { text: '汤类', value: 'soup' },
  { text: '饮品', value: 'drink' },
  { text: '甜点', value: 'dessert' },
  { text: '其他', value: 'other' }
]

const filteredDishes = computed(() => {
  if (activeSource.value === 'all') return dishes.value
  return dishes.value.filter(d => d.source === activeSource.value)
})

// 获取分类标签
function getCategoryLabel(value) {
  const item = categoryColumns.find(c => c.value === value)
  return item?.text || '其他'
}

// 加载菜品
async function loadDishes() {
  loading.value = true
  try {
    dishes.value = await dishesApi.getAll()
  } catch (error) {
    showToast(isZh.value ? '加载失败' : 'Load failed')
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

// 编辑菜品
function editDish(dish) {
  editingDish.value = dish
  formData.value = {
    name: dish.name,
    name_en: dish.name_en || '',
    price: dish.price.toString(),
    category: dish.category || 'other',
    description: dish.description || '',
    stock: dish.stock || 100,
    nutrition: dish.nutrition || { calories: '', protein: '', carbohydrates: '', fat: '' }
  }
  showAddDialog.value = true
}

// 关闭表单
function closeForm() {
  showAddDialog.value = false
  editingDish.value = null
  formData.value = { ...defaultFormData }
}

// 保存菜品
async function saveDish() {
  saving.value = true
  try {
    const data = {
      ...formData.value,
      price: parseFloat(formData.value.price),
      stock: parseInt(formData.value.stock) || 100
    }
    
    if (editingDish.value) {
      await dishesApi.update(editingDish.value.id, data)
      showToast({ message: isZh.value ? '更新成功' : 'Updated', icon: 'success' })
    } else {
      await dishesApi.create(data)
      showToast({ message: isZh.value ? '添加成功' : 'Added', icon: 'success' })
    }
    
    closeForm()
    loadDishes()
  } catch (error) {
    showToast(isZh.value ? '保存失败' : 'Save failed')
  } finally {
    saving.value = false
  }
}

// 删除菜品
async function deleteDish(dish) {
  try {
    await showConfirmDialog({
      title: isZh.value ? '确认删除' : 'Confirm Delete',
      message: isZh.value ? `确定删除 ${dish.name} 吗？` : `Delete ${dish.name}?`
    })
    
    await dishesApi.delete(dish.id)
    showToast({ message: isZh.value ? '已删除' : 'Deleted', icon: 'success' })
    loadDishes()
  } catch {
    // 用户取消
  }
}

// 分类选择
function onCategoryConfirm({ selectedOptions }) {
  formData.value.category = selectedOptions[0].value
  showCategoryPicker.value = false
}

onMounted(() => {
  loadDishes()
})
</script>

<style scoped>
.dishes-view {
  min-height: 100vh;
  background: var(--color-bg-primary);
}

.page-content {
  padding: var(--space-md);
}

.dishes-list {
  margin-top: var(--space-md);
}

.dish-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-bg-card);
  margin-bottom: var(--space-sm);
  border-radius: var(--radius-md);
}

.dish-placeholder {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-secondary);
  border-radius: var(--radius-sm);
  color: var(--color-text-light);
}

.dish-info {
  flex: 1;
}

.dish-name {
  font-weight: 500;
  margin-bottom: var(--space-xs);
}

.dish-meta {
  display: flex;
  gap: var(--space-xs);
  align-items: center;
}

.dish-price {
  font-weight: 600;
  color: var(--color-primary);
}

.swipe-btn {
  height: 100%;
}

.dish-form {
  max-height: 80vh;
  overflow-y: auto;
  padding-bottom: var(--space-xl);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}

.form-header h3 {
  font-size: var(--text-lg);
  font-weight: 600;
}

.form-section-title {
  padding: var(--space-md) var(--space-lg) var(--space-sm);
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
}

.form-actions {
  padding: var(--space-lg);
}
</style>
