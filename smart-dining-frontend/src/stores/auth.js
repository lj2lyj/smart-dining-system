/**
 * 管理员认证状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '../api'

export const useAuthStore = defineStore('auth', () => {
    // 状态
    const token = ref(localStorage.getItem('admin_token') || null)
    const user = ref(JSON.parse(localStorage.getItem('admin_user') || 'null'))

    // 计算属性
    const isLoggedIn = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')

    // 登录
    async function login(username, password) {
        try {
            const result = await authApi.login(username, password)

            if (result.success) {
                token.value = result.token
                user.value = result.user

                localStorage.setItem('admin_token', result.token)
                localStorage.setItem('admin_user', JSON.stringify(result.user))

                return { success: true }
            } else {
                return { success: false, message: result.message }
            }
        } catch (error) {
            return { success: false, message: '登录失败，请检查网络' }
        }
    }

    // 登出
    function logout() {
        token.value = null
        user.value = null
        localStorage.removeItem('admin_token')
        localStorage.removeItem('admin_user')
    }

    // 获取当前用户信息
    async function fetchUser() {
        if (!token.value) return null

        try {
            const userData = await authApi.getMe()
            user.value = userData
            localStorage.setItem('admin_user', JSON.stringify(userData))
            return userData
        } catch (error) {
            // Token 无效，清除状态
            logout()
            return null
        }
    }

    return {
        // 状态
        token,
        user,

        // 计算属性
        isLoggedIn,
        isAdmin,

        // 方法
        login,
        logout,
        fetchUser
    }
})
