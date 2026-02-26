<template>
  <div class="settings-view">
    <van-nav-bar :title="isZh ? '系统设置' : 'Settings'" left-arrow @click-left="$router.back()" />

    <div class="page-content">
      <van-cell-group inset :title="isZh ? '识别设置' : 'Recognition'">
        <van-cell :title="isZh ? '置信度阈值' : 'Confidence Threshold'" :value="(settings.confidence_threshold * 100).toFixed(0) + '%'" is-link @click="showThresholdPicker = true" />
        <van-cell :title="isZh ? '自动识别间隔' : 'Auto Interval'" :value="(settings.auto_recognize_interval / 1000) + 's'" is-link @click="showIntervalPicker = true" />
        <van-cell :title="isZh ? '识别日志' : 'Recognition Logs'" center>
          <template #right-icon><van-switch v-model="settings.enable_logging" @change="saveSettings" /></template>
        </van-cell>
      </van-cell-group>

      <van-cell-group inset :title="isZh ? '模型配置' : 'Model'">
        <van-cell :title="isZh ? '模型路径' : 'Model Path'" :value="settings.model_path || (isZh ? '未配置' : 'Not set')" />
        <van-cell :title="isZh ? '模型状态' : 'Status'">
          <template #right-icon>
            <van-tag :type="modelStatus.loaded ? 'success' : 'warning'">{{ modelStatus.loaded ? (isZh ? '已加载' : 'Loaded') : (isZh ? '模拟模式' : 'Simulation') }}</van-tag>
          </template>
        </van-cell>
      </van-cell-group>

      <van-cell-group inset :title="isZh ? '账户' : 'Account'">
        <van-cell :title="isZh ? '修改密码' : 'Change Password'" is-link @click="showPasswordDialog = true" />
      </van-cell-group>
    </div>

    <van-popup v-model:show="showThresholdPicker" position="bottom" round>
      <van-picker :columns="thresholdOptions" @confirm="onThresholdConfirm" @cancel="showThresholdPicker = false" />
    </van-popup>

    <van-popup v-model:show="showIntervalPicker" position="bottom" round>
      <van-picker :columns="intervalOptions" @confirm="onIntervalConfirm" @cancel="showIntervalPicker = false" />
    </van-popup>

    <van-dialog v-model:show="showPasswordDialog" :title="isZh ? '修改密码' : 'Change Password'" show-cancel-button @confirm="changePassword">
      <div style="padding:16px">
        <van-field v-model="oldPass" type="password" :placeholder="isZh ? '原密码' : 'Old password'" style="margin-bottom:8px" />
        <van-field v-model="newPass" type="password" :placeholder="isZh ? '新密码' : 'New password'" />
      </div>
    </van-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSettingsStore } from '../../stores'
import { settingsApi, recognitionApi, authApi } from '../../api'
import { showToast } from 'vant'

const settingsStore = useSettingsStore()
const isZh = computed(() => settingsStore.language === 'zh')
const settings = ref({ confidence_threshold: 0.7, auto_recognize_interval: 3000, enable_logging: true, model_path: null })
const modelStatus = ref({ loaded: false })
const showThresholdPicker = ref(false)
const showIntervalPicker = ref(false)
const showPasswordDialog = ref(false)
const oldPass = ref('')
const newPass = ref('')

const thresholdOptions = [{ text: '50%', value: 0.5 }, { text: '60%', value: 0.6 }, { text: '70%', value: 0.7 }, { text: '80%', value: 0.8 }, { text: '90%', value: 0.9 }]
const intervalOptions = [{ text: '2s', value: 2000 }, { text: '3s', value: 3000 }, { text: '5s', value: 5000 }]

async function loadSettings() {
  try {
    const [s, r] = await Promise.all([settingsApi.get(), recognitionApi.getStatus()])
    settings.value = s
    modelStatus.value = r.model
  } catch {}
}

async function saveSettings() {
  try { await settingsApi.update(settings.value); showToast({ message: isZh.value ? '已保存' : 'Saved', icon: 'success' }) } catch {}
}

function onThresholdConfirm({ selectedOptions }) {
  settings.value.confidence_threshold = selectedOptions[0].value
  showThresholdPicker.value = false
  saveSettings()
}

function onIntervalConfirm({ selectedOptions }) {
  settings.value.auto_recognize_interval = selectedOptions[0].value
  showIntervalPicker.value = false
  saveSettings()
}

async function changePassword() {
  try {
    await authApi.changePassword(oldPass.value, newPass.value)
    showToast({ message: isZh.value ? '已修改' : 'Changed', icon: 'success' })
    oldPass.value = newPass.value = ''
  } catch { showToast(isZh.value ? '修改失败' : 'Failed') }
}

onMounted(loadSettings)
</script>

<style scoped>
.settings-view { min-height: 100vh; background: var(--color-bg-primary); }
.page-content { padding: var(--space-md); }
.van-cell-group { margin-bottom: var(--space-md); }
</style>
