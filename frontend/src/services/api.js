import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 雲端 API 實例（Render）
const cloudApi = axios.create({
  baseURL: import.meta.env.VITE_CLOUD_API_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 本機 API 實例
const localApi = axios.create({
  baseURL: import.meta.env.VITE_LOCAL_API_URL || 'http://localhost:8001',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 雲端 API 請求攔截器：附加 JWT Token
cloudApi.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 雲端 API 響應攔截器：處理 401 錯誤
cloudApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.clearAuth()
      router.push({ name: 'login' })
    }
    return Promise.reject(error)
  }
)

export { cloudApi, localApi }
