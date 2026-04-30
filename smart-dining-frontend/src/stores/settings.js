/**
 * 系统设置状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
    // 主题
    const theme = ref(localStorage.getItem('theme') || 'light')

    // 语言
    const language = ref(localStorage.getItem('language') || 'zh')

    // 语音播报
    const voiceEnabled = ref(localStorage.getItem('voiceEnabled') !== 'false')

    // 用户偏好
    const allergens = ref(JSON.parse(localStorage.getItem('allergens') || '[]'))
    const dietaryRestrictions = ref(JSON.parse(localStorage.getItem('dietaryRestrictions') || '[]'))



    // 计算属性
    const isDarkMode = computed(() => theme.value === 'dark')
    const isChineseLanguage = computed(() => language.value === 'zh')

    // 切换主题
    function toggleTheme() {
        theme.value = theme.value === 'light' ? 'dark' : 'light'
    }

    // 切换语言
    function toggleLanguage() {
        language.value = language.value === 'zh' ? 'en' : 'zh'
    }

    // 设置语言
    function setLanguage(lang) {
        language.value = lang
    }

    // 切换语音
    function toggleVoice() {
        voiceEnabled.value = !voiceEnabled.value
    }

    // 设置过敏原
    function setAllergens(items) {
        allergens.value = items
    }

    // 设置饮食限制
    function setDietaryRestrictions(items) {
        dietaryRestrictions.value = items
    }



    // 语音播报函数
    function speak(text) {
        if (!voiceEnabled.value) return

        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text)
            utterance.lang = language.value === 'zh' ? 'zh-CN' : 'en-US'
            utterance.rate = 1.0
            utterance.pitch = 1.0
            window.speechSynthesis.speak(utterance)
        }
    }

    // 监听变化并持久化
    watch(theme, (val) => localStorage.setItem('theme', val))
    watch(language, (val) => localStorage.setItem('language', val))
    watch(voiceEnabled, (val) => localStorage.setItem('voiceEnabled', val))
    watch(allergens, (val) => localStorage.setItem('allergens', JSON.stringify(val)), { deep: true })
    watch(dietaryRestrictions, (val) => localStorage.setItem('dietaryRestrictions', JSON.stringify(val)), { deep: true })


    return {
        // 状态
        theme,
        language,
        voiceEnabled,
        allergens,
        dietaryRestrictions,


        // 计算属性
        isDarkMode,
        isChineseLanguage,

        // 方法
        toggleTheme,
        toggleLanguage,
        setLanguage,
        toggleVoice,
        setAllergens,
        setDietaryRestrictions,
        speak
    }
})
