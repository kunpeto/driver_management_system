/**
 * 應用程式入口
 */

import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import zhTw from 'element-plus/es/locale/lang/zh-tw'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import pinia from './stores'
import { setupErrorHandler } from './utils/errorHandler'

// 基礎樣式
import './style.css'
// 主題樣式（必須在 Element Plus 之後引入以覆蓋預設樣式）
import './styles/theme.css'

// 建立 Vue 應用
const app = createApp(App)

// 註冊 Element Plus 圖標
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhTw // 繁體中文
})

// 設定錯誤處理
setupErrorHandler(app)

// 掛載應用
app.mount('#app')
