<template>
  <div class="promotions-view">
    <van-nav-bar :title="isZh ? '促销管理' : 'Promotions'" left-arrow @click-left="$router.back()">
      <template #right><van-icon name="plus" size="20" @click="showAdd = true" /></template>
    </van-nav-bar>

    <div class="page-content">
      <van-pull-refresh v-model="refreshing" @refresh="load">
        <div v-for="p in promotions" :key="p.id" class="promo-card">
          <div class="promo-header">
            <span class="promo-name">{{ p.name }}</span>
            <van-tag :type="p.is_active ? 'success' : 'default'" size="small">{{ p.is_active ? (isZh ? '进行中' : 'Active') : (isZh ? '已停用' : 'Inactive') }}</van-tag>
          </div>
          <div class="promo-info">
            <span>{{ p.type === 'discount' ? (isZh ? '折扣:' : 'Discount:') : (isZh ? '减价:' : 'Off:') }} {{ p.type === 'discount' ? (p.value * 10) + '折' : '¥' + p.value }}</span>
          </div>
          <div class="promo-actions">
            <van-button size="small" plain @click="toggleActive(p)">{{ p.is_active ? (isZh ? '停用' : 'Disable') : (isZh ? '启用' : 'Enable') }}</van-button>
            <van-button size="small" plain type="danger" @click="remove(p)">{{ isZh ? '删除' : 'Delete' }}</van-button>
          </div>
        </div>
        <van-empty v-if="promotions.length === 0" :description="isZh ? '暂无促销' : 'No promotions'" />
      </van-pull-refresh>
    </div>

    <van-popup v-model:show="showAdd" position="bottom" round>
      <div class="add-form">
        <h3>{{ isZh ? '添加促销' : 'Add Promotion' }}</h3>
        <van-form @submit="save">
          <van-cell-group inset>
            <van-field v-model="form.name" :label="isZh ? '名称' : 'Name'" required />
            <van-field :label="isZh ? '类型' : 'Type'" :model-value="form.type === 'discount' ? (isZh ? '折扣' : 'Discount') : (isZh ? '减价' : 'Fixed')" is-link readonly @click="showTypePicker = true" />
            <van-field v-model="form.value" type="number" :label="form.type === 'discount' ? (isZh ? '折扣(0-1)' : 'Discount(0-1)') : (isZh ? '金额' : 'Amount')" required />
          </van-cell-group>
          <div style="padding:16px"><van-button block type="primary" native-type="submit">{{ isZh ? '保存' : 'Save' }}</van-button></div>
        </van-form>
      </div>
    </van-popup>

    <van-popup v-model:show="showTypePicker" position="bottom" round>
      <van-picker :columns="[{text:isZh?'折扣':'Discount',value:'discount'},{text:isZh?'减价':'Fixed',value:'fixed'}]" @confirm="({selectedOptions})=>{form.type=selectedOptions[0].value;showTypePicker=false}" @cancel="showTypePicker=false" />
    </van-popup>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../../stores'
import { promotionsApi } from '../../api'
import { showToast, showConfirmDialog } from 'vant'

const settingsStore = useSettingsStore()
const isZh = computed(() => settingsStore.language === 'zh')
const promotions = ref([])
const refreshing = ref(false)
const showAdd = ref(false)
const showTypePicker = ref(false)
const form = ref({ name: '', type: 'discount', value: '' })

async function load() { try { promotions.value = await promotionsApi.getAll() } finally { refreshing.value = false } }
async function save() {
  try {
    await promotionsApi.create({ ...form.value, value: parseFloat(form.value.value), is_active: true })
    showToast({ message: isZh.value ? '已添加' : 'Added', icon: 'success' })
    showAdd.value = false
    form.value = { name: '', type: 'discount', value: '' }
    load()
  } catch { showToast(isZh.value ? '失败' : 'Failed') }
}
async function toggleActive(p) {
  try { await promotionsApi.update(p.id, { is_active: !p.is_active }); load() } catch {}
}
async function remove(p) {
  try { await showConfirmDialog({ title: isZh.value ? '确认删除' : 'Delete?' }); await promotionsApi.delete(p.id); load() } catch {}
}
onMounted(load)
</script>

<style scoped>
.promotions-view { min-height: 100vh; background: var(--color-bg-primary); }
.page-content { padding: var(--space-md); }
.promo-card { background: var(--color-bg-card); border-radius: var(--radius-lg); padding: var(--space-md); margin-bottom: var(--space-md); }
.promo-header { display: flex; justify-content: space-between; margin-bottom: var(--space-sm); }
.promo-name { font-weight: 600; }
.promo-info { color: var(--color-text-secondary); margin-bottom: var(--space-md); }
.promo-actions { display: flex; gap: var(--space-sm); }
.add-form { padding: var(--space-lg); }
.add-form h3 { margin-bottom: var(--space-md); }
</style>
