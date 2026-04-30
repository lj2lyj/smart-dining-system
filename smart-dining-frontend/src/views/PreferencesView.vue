<template>
  <div class="preferences-view">
    <van-nav-bar 
      :title="isZh ? '个人偏好' : 'Preferences'"
      left-arrow
      @click-left="$router.back()"
    />

    <div class="page-content">
      <!-- 语言设置 -->
      <van-cell-group inset :title="isZh ? '语言' : 'Language'">
        <van-cell 
          :title="isZh ? '中文 / English' : 'English / 中文'"
          center
        >
          <template #right-icon>
            <van-switch 
              :model-value="settingsStore.language === 'en'"
              @change="toggleLanguage"
              size="24"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 语音设置 -->
      <van-cell-group inset :title="isZh ? '语音' : 'Voice'">
        <van-cell 
          :title="isZh ? '语音播报' : 'Voice Announcement'"
          :label="isZh ? '识别结果和结算时播报' : 'Announce recognition results'"
          center
        >
          <template #right-icon>
            <van-switch 
              v-model="settingsStore.voiceEnabled"
              size="24"
            />
          </template>
        </van-cell>
        
        <van-cell 
          v-if="settingsStore.voiceEnabled"
          :title="isZh ? '测试语音' : 'Test Voice'"
          is-link
          @click="testVoice"
        />
      </van-cell-group>

      <!-- 主题设置 -->
      <van-cell-group inset :title="isZh ? '主题' : 'Theme'">
        <van-cell 
          :title="isZh ? '深色模式' : 'Dark Mode'"
          center
        >
          <template #right-icon>
            <van-switch 
              :model-value="settingsStore.theme === 'dark'"
              @change="toggleTheme"
              size="24"
            />
          </template>
        </van-cell>
      </van-cell-group>

      <!-- 过敏原设置 -->
      <van-cell-group inset :title="isZh ? '过敏原' : 'Allergens'">
        <van-cell 
          :title="isZh ? '设置过敏原' : 'Set Allergens'"
          :value="allergensSummary"
          is-link
          @click="showAllergenPicker = true"
        />
      </van-cell-group>



      <!-- 关于 -->
      <van-cell-group inset :title="isZh ? '关于' : 'About'">
        <van-cell 
          :title="isZh ? '版本' : 'Version'"
          value="1.0.0"
        />
        <van-cell 
          :title="isZh ? '技术支持' : 'Support'"
          value="YOLOv13 + Vue 3"
        />
      </van-cell-group>
    </div>

    <!-- 过敏原选择器 -->
    <van-popup v-model:show="showAllergenPicker" position="bottom" round>
      <div class="allergen-picker">
        <div class="picker-header">
          <span>{{ isZh ? '选择过敏原' : 'Select Allergens' }}</span>
          <van-button type="primary" size="small" @click="saveAllergens">
            {{ isZh ? '确定' : 'Done' }}
          </van-button>
        </div>
        <van-checkbox-group v-model="selectedAllergens">
          <van-cell-group>
            <van-cell 
              v-for="item in allergenOptions" 
              :key="item.value"
              clickable 
              @click="toggleAllergen(item.value)"
            >
              <template #title>
                <span>{{ isZh ? item.label : item.labelEn }}</span>
              </template>
              <template #right-icon>
                <van-checkbox :name="item.value" />
              </template>
            </van-cell>
          </van-cell-group>
        </van-checkbox-group>
      </div>
    </van-popup>


  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useSettingsStore } from '../stores'
import { showToast } from 'vant'

const settingsStore = useSettingsStore()
const isZh = computed(() => settingsStore.language === 'zh')

const showAllergenPicker = ref(false)
const selectedAllergens = ref([...settingsStore.allergens])

const allergenOptions = [
  { value: '鸡蛋', label: '鸡蛋', labelEn: 'Eggs' },
  { value: '牛奶', label: '牛奶', labelEn: 'Milk' },
  { value: '花生', label: '花生', labelEn: 'Peanuts' },
  { value: '大豆', label: '大豆', labelEn: 'Soy' },
  { value: '小麦', label: '小麦', labelEn: 'Wheat' },
  { value: '海鲜', label: '海鲜', labelEn: 'Seafood' },
  { value: '坚果', label: '坚果', labelEn: 'Tree Nuts' },
  { value: '芝麻', label: '芝麻', labelEn: 'Sesame' }
]



const allergensSummary = computed(() => {
  if (settingsStore.allergens.length === 0) {
    return isZh.value ? '未设置' : 'Not set'
  }
  return settingsStore.allergens.join('、')
})

function toggleLanguage() {
  settingsStore.toggleLanguage()
}

function toggleTheme() {
  settingsStore.toggleTheme()
}

function toggleAllergen(value) {
  const index = selectedAllergens.value.indexOf(value)
  if (index > -1) {
    selectedAllergens.value.splice(index, 1)
  } else {
    selectedAllergens.value.push(value)
  }
}

function saveAllergens() {
  settingsStore.setAllergens(selectedAllergens.value)
  showAllergenPicker.value = false
  showToast(isZh.value ? '已保存' : 'Saved')
}



function testVoice() {
  settingsStore.speak(isZh.value ? '语音播报测试成功' : 'Voice test successful')
}
</script>

<style scoped>
.preferences-view {
  min-height: 100vh;
  background: var(--color-bg-primary);
}

.page-content {
  padding: var(--space-md);
}

.van-cell-group {
  margin-bottom: var(--space-md);
}

.allergen-picker {
  padding: var(--space-md);
}

.picker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
  font-weight: 600;
}
</style>
