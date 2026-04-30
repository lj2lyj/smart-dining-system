import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Vant UI (在使用 unplugin-vue-components 时，需要单独引入 API 组件样式)
import 'vant/es/toast/style'
import 'vant/es/dialog/style'
import 'vant/es/notify/style'
import 'vant/es/image-preview/style'
import {
    Button, NavBar, Icon, Tabbar, TabbarItem,
    Cell, CellGroup, Field, Form,
    Dialog, Toast, Notify,
    List, PullRefresh,
    Tab, Tabs,
    Popup, Picker,
    Badge, Tag, Stepper,
    Empty, Loading, Skeleton,
    Image as VanImage,
    Grid, GridItem,
    Divider, Space,
    ActionSheet, SwipeCell
} from 'vant'

// 自定义样式
import './styles/theme.css'

// 路由和状态
import router from './router'
import App from './App.vue'

// 创建应用
const app = createApp(App)

// 使用 Pinia 状态管理
app.use(createPinia())

// 使用路由
app.use(router)

// 注册 Vant 组件
const vantComponents = [
    Button, NavBar, Icon, Tabbar, TabbarItem,
    Cell, CellGroup, Field, Form,
    Dialog, Toast, Notify,
    List, PullRefresh,
    Tab, Tabs,
    Popup, Picker,
    Badge, Tag, Stepper,
    Empty, Loading, Skeleton,
    VanImage,
    Grid, GridItem,
    Divider, Space,
    ActionSheet, SwipeCell
]

vantComponents.forEach(component => {
    app.use(component)
})

// 挂载应用
app.mount('#app')
