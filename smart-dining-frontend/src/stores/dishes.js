/**
 * 菜品状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { dishesApi, recognitionApi } from '../api'

export const useDishesStore = defineStore('dishes', () => {
    // 状态
    const allDishes = ref([])
    const cartItems = ref([])
    const recognitionResult = ref(null)
    const isRecognizing = ref(false)
    const lastRecognitionLogId = ref(null)

    // 计算属性
    const yoloDishes = computed(() =>
        allDishes.value.filter(d => d.source === 'yolo')
    )

    const manualDishes = computed(() =>
        allDishes.value.filter(d => d.source === 'manual')
    )

    const cartTotal = computed(() =>
        cartItems.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
    )

    const cartItemCount = computed(() =>
        cartItems.value.reduce((sum, item) => sum + item.quantity, 0)
    )

    const hasUnrecognized = computed(() =>
        recognitionResult.value?.unrecognized_count > 0
    )

    // 加载所有菜品
    async function loadDishes() {
        try {
            const data = await dishesApi.getAll()
            allDishes.value = data
        } catch (error) {
            console.error('加载菜品失败:', error)
        }
    }

    // 识别图像中的菜品
    async function recognizeDishes(imageBase64) {
        isRecognizing.value = true
        recognitionResult.value = null

        try {
            const result = await recognitionApi.recognize(imageBase64)
            recognitionResult.value = result
            lastRecognitionLogId.value = result.log_id

            // 自动将识别到的菜品添加到购物车（每种只加1份，跳过已有的）
            if (result.dishes && result.dishes.length > 0) {
                for (const dish of result.dishes) {
                    const existing = cartItems.value.find(i => i.dish_id === dish.dish_id)
                    if (!existing) {
                        addToCart({
                            dish_id: dish.dish_id,
                            name: dish.name,
                            price: dish.price,
                            quantity: 1,
                            confidence: dish.confidence,
                            is_manual: false
                        })
                    }
                }
            }

            return result
        } catch (error) {
            console.error('识别失败:', error)
            throw error
        } finally {
            isRecognizing.value = false
        }
    }

    // 上传图片识别菜品
    async function recognizeFromUpload(file) {
        isRecognizing.value = true
        recognitionResult.value = null

        try {
            const result = await recognitionApi.upload(file)
            recognitionResult.value = result
            lastRecognitionLogId.value = result.log_id

            // 自动将识别到的菜品添加到购物车（每种只加1份，跳过已有的）
            if (result.dishes && result.dishes.length > 0) {
                for (const dish of result.dishes) {
                    const existing = cartItems.value.find(i => i.dish_id === dish.dish_id)
                    if (!existing) {
                        addToCart({
                            dish_id: dish.dish_id,
                            name: dish.name,
                            price: dish.price,
                            quantity: 1,
                            confidence: dish.confidence,
                            is_manual: false
                        })
                    }
                }
            }

            return result
        } catch (error) {
            console.error('上传识别失败:', error)
            throw error
        } finally {
            isRecognizing.value = false
        }
    }

    // 添加到购物车
    function addToCart(item) {
        const existing = cartItems.value.find(i => i.dish_id === item.dish_id)

        if (existing) {
            existing.quantity += item.quantity || 1
        } else {
            cartItems.value.push({
                dish_id: item.dish_id,
                name: item.name,
                price: item.price,
                quantity: item.quantity || 1,
                confidence: item.confidence,
                is_manual: item.is_manual || false
            })
        }
    }

    // 从购物车移除
    function removeFromCart(dishId) {
        const index = cartItems.value.findIndex(i => i.dish_id === dishId)
        if (index > -1) {
            cartItems.value.splice(index, 1)
        }
    }

    // 更新购物车数量
    function updateCartQuantity(dishId, quantity) {
        const item = cartItems.value.find(i => i.dish_id === dishId)
        if (item) {
            if (quantity <= 0) {
                removeFromCart(dishId)
            } else {
                item.quantity = quantity
            }
        }
    }

    // 清空购物车
    function clearCart() {
        cartItems.value = []
        recognitionResult.value = null
    }

    // 手动添加菜品
    function addManualDish(dish) {
        addToCart({
            dish_id: dish.id,
            name: dish.name,
            price: dish.price,
            quantity: 1,
            is_manual: true
        })
    }

    return {
        // 状态
        allDishes,
        cartItems,
        recognitionResult,
        isRecognizing,
        lastRecognitionLogId,

        // 计算属性
        yoloDishes,
        manualDishes,
        cartTotal,
        cartItemCount,
        hasUnrecognized,

        // 方法
        loadDishes,
        recognizeDishes,
        recognizeFromUpload,
        addToCart,
        removeFromCart,
        updateCartQuantity,
        clearCart,
        addManualDish
    }
})
