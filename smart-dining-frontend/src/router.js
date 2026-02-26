/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    // 顾客端
    {
        path: '/',
        name: 'Home',
        component: () => import('./views/CustomerView.vue'),
        meta: { title: '智慧餐饮', transition: 'fade' }
    },
    {
        path: '/history',
        name: 'History',
        component: () => import('./views/HistoryView.vue'),
        meta: { title: '历史订单', transition: 'slide-left' }
    },
    {
        path: '/preferences',
        name: 'Preferences',
        component: () => import('./views/PreferencesView.vue'),
        meta: { title: '个人偏好', transition: 'slide-left' }
    },

    // 管理员端
    {
        path: '/admin',
        name: 'AdminLogin',
        component: () => import('./views/admin/LoginView.vue'),
        meta: { title: '管理员登录', transition: 'fade' }
    },
    {
        path: '/admin/dashboard',
        name: 'AdminDashboard',
        component: () => import('./views/admin/DashboardView.vue'),
        meta: { title: '管理后台', requiresAuth: true, transition: 'fade' }
    },
    {
        path: '/admin/dishes',
        name: 'AdminDishes',
        component: () => import('./views/admin/DishesView.vue'),
        meta: { title: '菜品管理', requiresAuth: true, transition: 'slide-left' }
    },
    {
        path: '/admin/inventory',
        name: 'AdminInventory',
        component: () => import('./views/admin/InventoryView.vue'),
        meta: { title: '库存管理', requiresAuth: true, transition: 'slide-left' }
    },
    {
        path: '/admin/stats',
        name: 'AdminStats',
        component: () => import('./views/admin/StatsView.vue'),
        meta: { title: '销售统计', requiresAuth: true, transition: 'slide-left' }
    },
    {
        path: '/admin/promotions',
        name: 'AdminPromotions',
        component: () => import('./views/admin/PromotionsView.vue'),
        meta: { title: '促销管理', requiresAuth: true, transition: 'slide-left' }
    },
    {
        path: '/admin/settings',
        name: 'AdminSettings',
        component: () => import('./views/admin/SettingsView.vue'),
        meta: { title: '系统设置', requiresAuth: true, transition: 'slide-left' }
    },

    // 404
    {
        path: '/:pathMatch(.*)*',
        redirect: '/'
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// 路由守卫 - 权限检查
router.beforeEach((to, from, next) => {
    // 更新页面标题
    document.title = to.meta.title ? `${to.meta.title} - 智慧餐饮` : '智慧餐饮结算系统'

    // 检查是否需要认证
    if (to.meta.requiresAuth) {
        const token = localStorage.getItem('admin_token')
        if (!token) {
            next({ name: 'AdminLogin', query: { redirect: to.fullPath } })
            return
        }
    }

    next()
})

export default router
