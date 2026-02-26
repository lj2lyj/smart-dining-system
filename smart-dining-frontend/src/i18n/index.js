/**
 * 国际化语言包
 */
export const messages = {
    zh: {
        // 通用
        app: {
            name: '智慧餐饮',
            slogan: '智能识别，轻松结算'
        },
        common: {
            confirm: '确认',
            cancel: '取消',
            save: '保存',
            delete: '删除',
            edit: '编辑',
            add: '添加',
            search: '搜索',
            loading: '加载中...',
            success: '操作成功',
            error: '操作失败',
            retry: '重试',
            back: '返回',
            next: '下一步',
            done: '完成',
            close: '关闭',
            more: '更多',
            noData: '暂无数据'
        },

        // 顾客端
        customer: {
            recognize: '识别菜品',
            recognizing: '识别中...',
            settlement: '结算',
            total: '合计',
            payNow: '立即结算',
            addDish: '添加菜品',
            manualSelect: '手动选择',
            unrecognized: '有未识别菜品',
            selectFromList: '请从列表中选择',
            orderSuccess: '结算成功',
            orderHistory: '历史订单',
            preferences: '个人偏好'
        },

        // 菜品
        dish: {
            name: '菜品名称',
            price: '价格',
            category: '分类',
            stock: '库存',
            calories: '卡路里',
            protein: '蛋白质',
            carbs: '碳水',
            fat: '脂肪',
            allergens: '过敏原',
            nutrition: '营养信息',
            lowStock: '库存不足',
            soldOut: '已售罄'
        },

        // 分类
        category: {
            staple: '主食',
            meat: '荤菜',
            vegetable: '素菜',
            soup: '汤类',
            drink: '饮品',
            dessert: '甜点',
            other: '其他'
        },

        // 管理员
        admin: {
            login: '管理员登录',
            logout: '退出登录',
            dashboard: '控制台',
            dishes: '菜品管理',
            inventory: '库存管理',
            stats: '销售统计',
            promotions: '促销管理',
            settings: '系统设置',
            todayOrders: '今日订单',
            todayRevenue: '今日收入',
            lowStockAlert: '库存预警'
        },

        // 设置
        settings: {
            theme: '主题',
            language: '语言',
            voice: '语音播报',
            allergens: '过敏原设置',
            autoRecognize: '自动识别',
            confidenceThreshold: '置信度阈值'
        }
    },

    en: {
        // Common
        app: {
            name: 'Smart Dining',
            slogan: 'AI Recognition, Easy Settlement'
        },
        common: {
            confirm: 'Confirm',
            cancel: 'Cancel',
            save: 'Save',
            delete: 'Delete',
            edit: 'Edit',
            add: 'Add',
            search: 'Search',
            loading: 'Loading...',
            success: 'Success',
            error: 'Error',
            retry: 'Retry',
            back: 'Back',
            next: 'Next',
            done: 'Done',
            close: 'Close',
            more: 'More',
            noData: 'No Data'
        },

        // Customer
        customer: {
            recognize: 'Recognize',
            recognizing: 'Recognizing...',
            settlement: 'Checkout',
            total: 'Total',
            payNow: 'Pay Now',
            addDish: 'Add Dish',
            manualSelect: 'Manual Select',
            unrecognized: 'Unrecognized Items',
            selectFromList: 'Select from list',
            orderSuccess: 'Order Completed',
            orderHistory: 'Order History',
            preferences: 'Preferences'
        },

        // Dish
        dish: {
            name: 'Name',
            price: 'Price',
            category: 'Category',
            stock: 'Stock',
            calories: 'Calories',
            protein: 'Protein',
            carbs: 'Carbs',
            fat: 'Fat',
            allergens: 'Allergens',
            nutrition: 'Nutrition',
            lowStock: 'Low Stock',
            soldOut: 'Sold Out'
        },

        // Category
        category: {
            staple: 'Staple',
            meat: 'Meat',
            vegetable: 'Vegetable',
            soup: 'Soup',
            drink: 'Drink',
            dessert: 'Dessert',
            other: 'Other'
        },

        // Admin
        admin: {
            login: 'Admin Login',
            logout: 'Logout',
            dashboard: 'Dashboard',
            dishes: 'Dishes',
            inventory: 'Inventory',
            stats: 'Statistics',
            promotions: 'Promotions',
            settings: 'Settings',
            todayOrders: 'Today\'s Orders',
            todayRevenue: 'Today\'s Revenue',
            lowStockAlert: 'Low Stock Alert'
        },

        // Settings
        settings: {
            theme: 'Theme',
            language: 'Language',
            voice: 'Voice',
            allergens: 'Allergens',
            autoRecognize: 'Auto Recognize',
            confidenceThreshold: 'Confidence Threshold'
        }
    }
}

/**
 * 获取翻译文本
 */
export function t(key, lang = 'zh') {
    const keys = key.split('.')
    let value = messages[lang]

    for (const k of keys) {
        if (value && typeof value === 'object') {
            value = value[k]
        } else {
            return key
        }
    }

    return value || key
}

export default { messages, t }
