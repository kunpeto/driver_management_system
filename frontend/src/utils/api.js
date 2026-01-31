/**
 * Axios 實例配置
 * 對應 tasks.md T029: 設定 Axios 實例
 *
 * 功能：
 * - 雲端 API 與本機 API 實例
 * - 請求攔截器（Token 附加）
 * - 回應攔截器（錯誤處理）
 */

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// ============================================================
// 環境變數
// ============================================================

// 雲端 API URL（Render 部署）
// 優先使用環境變數，提高部署靈活性
const CLOUD_API_URL =
  import.meta.env.VITE_CLOUD_API_URL ||
  (import.meta.env.MODE === 'production'
    ? 'https://driver-management-system-jff0.onrender.com'
    : 'http://localhost:8000')

// 本機 API URL（桌面應用）
const LOCAL_API_URL = import.meta.env.VITE_LOCAL_API_URL || 'http://127.0.0.1:8001'

// ============================================================
// 雲端 API 實例
// ============================================================

const cloudApi = axios.create({
  baseURL: CLOUD_API_URL,
  timeout: 30000, // 30 秒超時
  headers: {
    'Content-Type': 'application/json'
  }
})

// 請求攔截器：附加 JWT Token
cloudApi.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()

    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }

    // 添加請求 ID 用於追蹤
    config.headers['X-Request-ID'] = generateRequestId()

    return config
  },
  (error) => {
    console.error('[Cloud API] Request Error:', error)
    return Promise.reject(error)
  }
)

// 回應攔截器：處理錯誤
cloudApi.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    return handleApiError(error, 'cloud')
  }
)

// ============================================================
// 本機 API 實例
// ============================================================

const localApi = axios.create({
  baseURL: LOCAL_API_URL,
  timeout: 60000, // 60 秒超時（檔案處理可能較久）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 請求攔截器
localApi.interceptors.request.use(
  (config) => {
    config.headers['X-Request-ID'] = generateRequestId()
    return config
  },
  (error) => {
    console.error('[Local API] Request Error:', error)
    return Promise.reject(error)
  }
)

// 回應攔截器
localApi.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    return handleApiError(error, 'local')
  }
)

// ============================================================
// 工具函數
// ============================================================

/**
 * 生成請求 ID
 */
function generateRequestId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 統一處理 API 錯誤
 */
function handleApiError(error, source) {
  const authStore = useAuthStore()

  // 無回應（網路錯誤或超時）
  if (!error.response) {
    console.error(`[${source} API] Network Error:`, error.message)

    // 本機 API 無法連線的特殊處理
    if (source === 'local') {
      error.userMessage = '無法連線到本機 API，請確認桌面應用程式已啟動'
    } else {
      error.userMessage = '網路連線失敗，請檢查網路狀態'
    }

    return Promise.reject(error)
  }

  const { status, data } = error.response

  // 根據狀態碼處理
  switch (status) {
    case 401:
      // Token 過期或無效
      console.warn(`[${source} API] Unauthorized`)
      authStore.clearAuth()
      router.push({
        name: 'login',
        query: { redirect: router.currentRoute.value.fullPath }
      })
      error.userMessage = '登入已過期，請重新登入'
      break

    case 403:
      // 權限不足
      console.warn(`[${source} API] Forbidden`)
      error.userMessage = '權限不足，無法執行此操作'
      break

    case 404:
      // 資源不存在
      error.userMessage = data?.error?.message || '找不到請求的資源'
      break

    case 422:
      // 資料驗證錯誤
      error.userMessage = data?.error?.message || '資料格式錯誤'
      error.validationErrors = data?.error?.details?.errors
      break

    case 500:
      // 伺服器錯誤
      console.error(`[${source} API] Server Error:`, data)
      error.userMessage = '伺服器發生錯誤，請稍後再試'
      break

    default:
      error.userMessage = data?.error?.message || `請求失敗 (${status})`
  }

  return Promise.reject(error)
}

/**
 * 檢查本機 API 是否可用
 */
export async function checkLocalApiHealth() {
  try {
    const response = await localApi.get('/health', { timeout: 5000 })
    return {
      available: true,
      data: response.data
    }
  } catch (error) {
    return {
      available: false,
      error: error.message
    }
  }
}

/**
 * 檢查雲端 API 是否可用
 */
export async function checkCloudApiHealth() {
  try {
    const response = await cloudApi.get('/health', { timeout: 10000 })
    return {
      available: true,
      data: response.data
    }
  } catch (error) {
    return {
      available: false,
      error: error.message
    }
  }
}

// ============================================================
// 匯出
// ============================================================

export { cloudApi, localApi }
export default cloudApi
