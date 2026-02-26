/**
 * API 请求模块
 */
import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// 请求拦截器
api.interceptors.request.use(
    config => {
        const token = localStorage.getItem('admin_token')
        if (token) {
            config.headers.Authorization = `Bearer ${token}`
        }
        return config
    },
    error => Promise.reject(error)
)

// 响应拦截器
api.interceptors.response.use(
    response => response.data,
    error => {
        console.error('API 错误:', error)

        if (error.response?.status === 401) {
            localStorage.removeItem('admin_token')
            localStorage.removeItem('admin_user')
            window.location.href = '/admin'
        }

        return Promise.reject(error)
    }
)

// ============ 认证 API ============
export const authApi = {
    login: (username, password) =>
        api.post('/auth/login', { username, password }),

    getMe: () =>
        api.get('/auth/me'),

    logout: () =>
        api.post('/auth/logout'),

    changePassword: (oldPassword, newPassword) =>
        api.post('/auth/change-password', { old_password: oldPassword, new_password: newPassword })
}

// ============ 识别 API ============
export const recognitionApi = {
    recognize: (imageBase64) =>
        api.post('/recognition/recognize', { image: imageBase64 }),

    // 上传图片识别
    upload: (file) => {
        const formData = new FormData()
        formData.append('file', file)
        return api.post('/recognition/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            timeout: 60000
        })
    },

    getStatus: () =>
        api.get('/recognition/status')
}

// ============ 菜品 API ============
export const dishesApi = {
    getAll: (params) =>
        api.get('/dishes/', { params }),

    getYolo: () =>
        api.get('/dishes/yolo'),

    getManual: () =>
        api.get('/dishes/manual'),

    getById: (id) =>
        api.get(`/dishes/${id}`),

    create: (dish) =>
        api.post('/dishes/', dish),

    update: (id, updates) =>
        api.put(`/dishes/${id}`, updates),

    delete: (id) =>
        api.delete(`/dishes/${id}`),

    getCategories: () =>
        api.get('/dishes/categories/list')
}

// ============ 订单 API ============
export const ordersApi = {
    create: (order) =>
        api.post('/orders/', order),

    getAll: (params) =>
        api.get('/orders/', { params }),

    getToday: () =>
        api.get('/orders/today'),

    getById: (id) =>
        api.get(`/orders/${id}`)
}

// ============ 统计 API ============
export const statsApi = {
    getDashboard: () =>
        api.get('/stats/dashboard'),

    getSales: (days = 7) =>
        api.get('/stats/sales', { params: { days } }),

    getRecognitionLogs: (limit = 100) =>
        api.get('/stats/recognition-logs', { params: { limit } })
}

// ============ 库存 API ============
export const inventoryApi = {
    getAll: () =>
        api.get('/inventory/'),

    getLowStock: (threshold = 20) =>
        api.get('/inventory/low-stock', { params: { threshold } }),

    update: (dishId, quantity) =>
        api.put(`/inventory/${dishId}`, { quantity }),

    restock: (dishId, quantity) =>
        api.post(`/inventory/${dishId}/restock`, null, { params: { quantity } })
}

// ============ 促销 API ============
export const promotionsApi = {
    getAll: () =>
        api.get('/promotions/'),

    getActive: () =>
        api.get('/promotions/active'),

    create: (promo) =>
        api.post('/promotions/', promo),

    update: (id, updates) =>
        api.put(`/promotions/${id}`, updates),

    delete: (id) =>
        api.delete(`/promotions/${id}`)
}

// ============ 系统设置 API ============
export const settingsApi = {
    get: () =>
        api.get('/settings/'),

    update: (settings) =>
        api.put('/settings/', settings),

    getConfidenceThreshold: () =>
        api.get('/settings/confidence-threshold'),

    setConfidenceThreshold: (threshold) =>
        api.put('/settings/confidence-threshold', null, { params: { threshold } })
}

// ============ 支付 API ============
export const paymentApi = {
    // 获取可用支付方式
    getMethods: () =>
        api.get('/payment/methods'),

    // 创建支付订单
    create: (orderId, amount, subject, paymentMethod = 'alipay') =>
        api.post('/payment/create', {
            order_id: orderId,
            amount,
            subject,
            payment_method: paymentMethod
        }),

    // 查询支付状态
    query: (paymentId) =>
        api.get(`/payment/query/${paymentId}`),

    // 获取配置状态
    getConfigStatus: () =>
        api.get('/payment/config/status')
}

export default api

