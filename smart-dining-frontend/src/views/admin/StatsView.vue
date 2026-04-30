<template>
  <div class="stats-view">
    <van-nav-bar 
      :title="isZh ? '销售统计' : 'Statistics'"
      left-arrow
      @click-left="$router.back()"
    />

    <div class="page-content">
      <!-- 日期范围 -->
      <div class="date-range">
        <van-button v-for="d in [7, 14, 30]" :key="d" :type="days === d ? 'primary' : 'default'" size="small" round @click="days = d">
          {{ d }} {{ isZh ? '天' : 'Days' }}
        </van-button>
      </div>

      <!-- 总览卡片 -->
      <div class="summary-cards">
        <div class="summary-card">
          <span class="summary-value">{{ totalOrders }}</span>
          <span class="summary-label">{{ isZh ? '总订单' : 'Orders' }}</span>
        </div>
        <div class="summary-card">
          <span class="summary-value">¥{{ Number(totalRevenue || 0).toFixed(2) }}</span>
          <span class="summary-label">{{ isZh ? '总收入' : 'Revenue' }}</span>
        </div>
      </div>

      <!-- 每日数据 -->
      <h3 class="section-title">{{ isZh ? '每日数据（点击查看详情）' : 'Daily Data (tap for details)' }}</h3>
      <div class="daily-list">
        <div v-for="stat in salesStats" :key="stat.date" class="daily-wrapper">
          <div class="daily-item" :class="{ active: expandedDate === stat.date }" @click="toggleDate(stat.date)">
            <div class="daily-left">
              <span class="daily-date">{{ formatDate(stat.date) }}</span>
              <van-icon :name="expandedDate === stat.date ? 'arrow-down' : 'arrow'" size="12" color="var(--color-text-light)" />
            </div>
            <div class="daily-data">
              <span>{{ stat.total_orders }} {{ isZh ? '单' : 'orders' }}</span>
              <span class="daily-revenue">¥{{ Number(stat.total_revenue || 0).toFixed(2) }}</span>
            </div>
          </div>
          <!-- 展开详情 -->
          <Transition name="slide-fade">
            <div v-if="expandedDate === stat.date" class="daily-detail">
              <div v-if="(stat.top_dishes || []).length > 0" class="detail-dishes">
                <div class="detail-title">{{ isZh ? '当日菜品销量' : 'Dishes Sold' }}</div>
                <div v-for="dish in stat.top_dishes" :key="dish.name" class="detail-dish-row">
                  <span class="detail-dish-name">{{ dish.name }}</span>
                  <span class="detail-dish-count">x{{ dish.count }}</span>
                </div>
              </div>
              <div v-else class="detail-empty">{{ isZh ? '暂无菜品数据' : 'No dish data' }}</div>
            </div>
          </Transition>
        </div>
      </div>

      <!-- 热门菜品 -->
      <h3 class="section-title">{{ isZh ? '热门菜品' : 'Top Dishes' }}</h3>
      <div class="top-dishes">
        <div v-for="(dish, i) in topDishes" :key="dish.name" class="top-dish-item">
          <span class="rank">{{ i + 1 }}</span>
          <span class="top-name">{{ dish.name }}</span>
          <span class="top-count">{{ dish.count }} {{ isZh ? '份' : 'pcs' }}</span>
        </div>
        <van-empty v-if="topDishes.length === 0" :description="isZh ? '暂无数据' : 'No data'" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useSettingsStore } from '../../stores'
import { statsApi } from '../../api'

const settingsStore = useSettingsStore()
const isZh = computed(() => settingsStore.language === 'zh')

const days = ref(7)
const salesStats = ref([])
const expandedDate = ref(null)

function toggleDate(date) {
  expandedDate.value = expandedDate.value === date ? null : date
}

const totalOrders = computed(() => salesStats.value.reduce((s, d) => s + d.total_orders, 0))
const totalRevenue = computed(() => salesStats.value.reduce((s, d) => s + Number(d.total_revenue || 0), 0))
const topDishes = computed(() => {
  const all = salesStats.value.flatMap(s => s.top_dishes || [])
  const map = new Map()
  all.forEach(d => map.set(d.name, (map.get(d.name) || 0) + d.count))
  return Array.from(map.entries()).map(([name, count]) => ({ name, count })).sort((a, b) => b.count - a.count).slice(0, 5)
})

function formatDate(d) { return d ? d.slice(5) : '' }

async function loadStats() {
  try { salesStats.value = await statsApi.getSales(days.value) } catch {}
}

watch(days, () => { expandedDate.value = null; loadStats() })
onMounted(loadStats)
</script>

<style scoped>
.stats-view { min-height: 100vh; background: var(--color-bg-primary); }
.page-content { padding: var(--space-md); }
.date-range { display: flex; gap: var(--space-sm); margin-bottom: var(--space-lg); }
.summary-cards { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); margin-bottom: var(--space-xl); }
.summary-card { padding: var(--space-lg); background: var(--color-primary-gradient); color: white; border-radius: var(--radius-lg); text-align: center; }
.summary-value { display: block; font-size: var(--text-2xl); font-weight: 700; }
.summary-label { font-size: var(--text-sm); opacity: 0.9; }
.section-title { font-size: var(--text-lg); font-weight: 600; margin-bottom: var(--space-md); }

.daily-list { background: var(--color-bg-card); border-radius: var(--radius-lg); overflow: hidden; margin-bottom: var(--space-xl); }
.daily-wrapper { border-bottom: 1px solid var(--color-border); }
.daily-wrapper:last-child { border-bottom: none; }
.daily-item { display: flex; justify-content: space-between; align-items: center; padding: var(--space-md); cursor: pointer; transition: background var(--transition-fast); }
.daily-item:hover, .daily-item.active { background: rgba(255, 107, 53, 0.04); }
.daily-left { display: flex; align-items: center; gap: var(--space-xs); }
.daily-date { color: var(--color-text-secondary); font-weight: 500; }
.daily-data { display: flex; gap: var(--space-md); }
.daily-revenue { font-weight: 600; color: var(--color-primary); }

.daily-detail { padding: 0 var(--space-md) var(--space-md); }
.detail-title { font-size: var(--text-xs); color: var(--color-text-light); margin-bottom: var(--space-xs); font-weight: 500; }
.detail-dishes { background: var(--color-bg-secondary); border-radius: var(--radius-md); padding: var(--space-sm) var(--space-md); }
.detail-dish-row { display: flex; justify-content: space-between; padding: var(--space-xs) 0; font-size: var(--text-sm); }
.detail-dish-name { color: var(--color-text-primary); }
.detail-dish-count { color: var(--color-primary); font-weight: 600; }
.detail-empty { text-align: center; padding: var(--space-sm); color: var(--color-text-light); font-size: var(--text-sm); }

.slide-fade-enter-active { transition: all 0.2s ease; }
.slide-fade-leave-active { transition: all 0.15s ease; }
.slide-fade-enter-from, .slide-fade-leave-to { opacity: 0; transform: translateY(-6px); }

.top-dishes { background: var(--color-bg-card); border-radius: var(--radius-lg); overflow: hidden; }
.top-dish-item { display: flex; align-items: center; padding: var(--space-md); border-bottom: 1px solid var(--color-border); }
.top-dish-item:last-child { border-bottom: none; }
.rank { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: var(--color-primary); color: white; border-radius: 50%; font-size: var(--text-sm); font-weight: 600; margin-right: var(--space-md); }
.top-name { flex: 1; }
.top-count { color: var(--color-text-secondary); }
</style>
