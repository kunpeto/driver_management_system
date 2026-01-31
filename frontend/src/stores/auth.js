/**
 * 認證 Store
 * 對應 tasks.md T068: 建立認證 Store
 *
 * 管理使用者登入狀態、Token、權限資訊
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/utils/api'

// Token 儲存鍵名
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'user'

export const useAuthStore = defineStore('auth', () => {
  // ==================== State ====================

  // 使用者資訊
  const user = ref(null)

  // Token
  const accessToken = ref(null)
  const refreshToken = ref(null)

  // 載入狀態
  const loading = ref(false)

  // 錯誤訊息
  const error = ref(null)

  // 是否已初始化（從 localStorage 載入）
  const initialized = ref(false)

  // ==================== Getters ====================

  // 是否已登入
  const isLoggedIn = computed(() => !!accessToken.value && !!user.value)

  // 使用者角色
  const userRole = computed(() => user.value?.role || null)

  // 使用者部門
  const userDepartment = computed(() => user.value?.department || null)

  // 是否為管理員
  const isAdmin = computed(() => userRole.value === 'admin')

  // 是否為主管
  const isManager = computed(() => userRole.value === 'manager')

  // 是否為值班台人員
  const isStaff = computed(() => userRole.value === 'staff')

  // 是否為主管或管理員
  const isManagerOrAdmin = computed(() => isAdmin.value || isManager.value)

  // 顯示名稱
  const displayName = computed(() => user.value?.display_name || user.value?.username || '')

  // ==================== Actions ====================

  /**
   * 初始化 Store（從 localStorage 載入）
   */
  function init() {
    if (initialized.value) return

    try {
      const storedToken = localStorage.getItem(ACCESS_TOKEN_KEY)
      const storedRefresh = localStorage.getItem(REFRESH_TOKEN_KEY)
      const storedUser = localStorage.getItem(USER_KEY)

      if (storedToken) {
        accessToken.value = storedToken
      }

      if (storedRefresh) {
        refreshToken.value = storedRefresh
      }

      if (storedUser) {
        user.value = JSON.parse(storedUser)
      }

      // 設定 API 的 Authorization header
      if (accessToken.value) {
        api.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`
      }

    } catch (err) {
      console.error('載入認證資訊失敗:', err)
      clearAuth()
    }

    initialized.value = true
  }

  /**
   * 登入
   * @param {string} username 使用者名稱
   * @param {string} password 密碼
   * @param {boolean} remember 是否記住登入
   */
  async function login(username, password, remember = false) {
    loading.value = true
    error.value = null

    try {
      const response = await api.post('/api/auth/login', {
        username,
        password
      })

      const data = response.data

      // 儲存 Token
      accessToken.value = data.access_token
      refreshToken.value = data.refresh_token
      user.value = data.user

      // 設定 API header
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

      // 儲存到 localStorage
      if (remember) {
        localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
        localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
        localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      } else {
        // 僅使用 sessionStorage（關閉瀏覽器後失效）
        sessionStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
        sessionStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
        sessionStorage.setItem(USER_KEY, JSON.stringify(data.user))
      }

      return data

    } catch (err) {
      console.error('登入失敗:', err)
      error.value = err.response?.data?.detail || '登入失敗，請檢查帳號密碼'
      throw err

    } finally {
      loading.value = false
    }
  }

  /**
   * 登出
   */
  async function logout() {
    try {
      // 呼叫後端登出 API（可選）
      if (accessToken.value) {
        await api.post('/api/auth/logout').catch(() => {})
      }
    } finally {
      clearAuth()
    }
  }

  /**
   * 刷新 Token
   */
  async function refreshAccessToken() {
    if (!refreshToken.value) {
      throw new Error('沒有 Refresh Token')
    }

    try {
      const response = await api.post('/api/auth/refresh', {
        refresh_token: refreshToken.value
      })

      const data = response.data

      // 更新 Access Token
      accessToken.value = data.access_token

      // 更新 API header
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`

      // 更新儲存
      if (localStorage.getItem(ACCESS_TOKEN_KEY)) {
        localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
      } else {
        sessionStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
      }

      return data.access_token

    } catch (err) {
      console.error('刷新 Token 失敗:', err)
      // Token 刷新失敗，清除認證並重新登入
      clearAuth()
      throw err
    }
  }

  /**
   * 取得當前使用者資訊
   */
  async function fetchCurrentUser() {
    if (!accessToken.value) {
      throw new Error('未登入')
    }

    loading.value = true

    try {
      const response = await api.get('/api/auth/me')
      user.value = response.data

      // 更新儲存
      if (localStorage.getItem(USER_KEY)) {
        localStorage.setItem(USER_KEY, JSON.stringify(response.data))
      } else {
        sessionStorage.setItem(USER_KEY, JSON.stringify(response.data))
      }

      return response.data

    } catch (err) {
      console.error('取得使用者資訊失敗:', err)
      throw err

    } finally {
      loading.value = false
    }
  }

  /**
   * 變更密碼
   * @param {string} oldPassword 舊密碼
   * @param {string} newPassword 新密碼
   */
  async function changePassword(oldPassword, newPassword) {
    loading.value = true

    try {
      await api.post('/api/auth/change-password', null, {
        params: {
          old_password: oldPassword,
          new_password: newPassword
        }
      })

    } finally {
      loading.value = false
    }
  }

  /**
   * 清除認證資訊
   */
  function clearAuth() {
    accessToken.value = null
    refreshToken.value = null
    user.value = null

    // 清除 API header
    delete api.defaults.headers.common['Authorization']

    // 清除儲存
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    sessionStorage.removeItem(ACCESS_TOKEN_KEY)
    sessionStorage.removeItem(REFRESH_TOKEN_KEY)
    sessionStorage.removeItem(USER_KEY)
  }

  /**
   * 檢查是否可以編輯指定部門
   * @param {string} department 部門
   */
  function canEditDepartment(department) {
    if (!user.value) return false

    if (user.value.role === 'admin' || user.value.role === 'manager') {
      return true
    }

    return user.value.department === department
  }

  /**
   * 取得使用者可編輯的部門列表
   */
  function getEditableDepartments() {
    if (!user.value) return []

    if (user.value.role === 'admin' || user.value.role === 'manager') {
      return ['淡海', '安坑']
    }

    return user.value.department ? [user.value.department] : []
  }

  /**
   * 取得使用者預設部門篩選
   */
  function getDefaultDepartment() {
    if (!user.value) return null

    if (user.value.role === 'admin' || user.value.role === 'manager') {
      return null // 顯示全部
    }

    return user.value.department
  }

  return {
    // State
    user,
    accessToken,
    refreshToken,
    loading,
    error,
    initialized,

    // Getters
    isLoggedIn,
    userRole,
    userDepartment,
    isAdmin,
    isManager,
    isStaff,
    isManagerOrAdmin,
    displayName,

    // Actions
    init,
    login,
    logout,
    refreshAccessToken,
    fetchCurrentUser,
    changePassword,
    clearAuth,
    canEditDepartment,
    getEditableDepartments,
    getDefaultDepartment
  }
})
