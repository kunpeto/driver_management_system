/**
 * 全域錯誤處理器
 * 對應 tasks.md T030: 建立全域錯誤處理器
 *
 * 功能：
 * - Vue 應用錯誤處理
 * - 未處理的 Promise 錯誤
 * - 網路錯誤處理
 * - 使用者友善錯誤訊息
 */

import { ElMessage, ElNotification } from 'element-plus'

// ============================================================
// 錯誤類型
// ============================================================

/**
 * API 錯誤
 */
export class ApiError extends Error {
  constructor(message, status, code, details = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.details = details
  }
}

/**
 * 驗證錯誤
 */
export class ValidationError extends Error {
  constructor(message, errors = []) {
    super(message)
    this.name = 'ValidationError'
    this.errors = errors
  }
}

/**
 * 網路錯誤
 */
export class NetworkError extends Error {
  constructor(message = '網路連線失敗') {
    super(message)
    this.name = 'NetworkError'
  }
}

// ============================================================
// 錯誤處理函數
// ============================================================

/**
 * 處理 API 錯誤
 */
export function handleApiError(error) {
  // 已有使用者友善訊息
  if (error.userMessage) {
    showError(error.userMessage)
    return
  }

  // 根據錯誤類型處理
  if (error instanceof ApiError) {
    showError(error.message)
  } else if (error instanceof ValidationError) {
    showValidationErrors(error.errors)
  } else if (error instanceof NetworkError) {
    showError(error.message, '網路錯誤')
  } else if (error.response) {
    // Axios 錯誤
    const status = error.response.status
    const data = error.response.data

    if (status === 401) {
      showWarning('登入已過期，請重新登入')
    } else if (status === 403) {
      showError('權限不足，無法執行此操作')
    } else if (status === 422 && data?.error?.details?.errors) {
      showValidationErrors(data.error.details.errors)
    } else {
      showError(data?.error?.message || `請求失敗 (${status})`)
    }
  } else if (error.request) {
    // 請求已發送但無回應
    showError('伺服器無回應，請稍後再試', '連線錯誤')
  } else {
    // 其他錯誤
    showError(error.message || '發生未知錯誤')
  }
}

/**
 * 顯示驗證錯誤
 */
function showValidationErrors(errors) {
  if (!errors || errors.length === 0) {
    showError('資料驗證失敗')
    return
  }

  // 顯示第一個錯誤
  const firstError = errors[0]
  const field = firstError.field?.split('.').pop() || '欄位'
  const message = firstError.message || '格式錯誤'

  showError(`${field}: ${message}`, '驗證錯誤')
}

// ============================================================
// 通知函數
// ============================================================

/**
 * 顯示錯誤訊息
 */
export function showError(message, title = '錯誤') {
  ElNotification({
    title,
    message,
    type: 'error',
    duration: 5000,
    position: 'top-right'
  })
}

/**
 * 顯示警告訊息
 */
export function showWarning(message, title = '警告') {
  ElNotification({
    title,
    message,
    type: 'warning',
    duration: 4000,
    position: 'top-right'
  })
}

/**
 * 顯示成功訊息
 */
export function showSuccess(message, title = '成功') {
  ElNotification({
    title,
    message,
    type: 'success',
    duration: 3000,
    position: 'top-right'
  })
}

/**
 * 顯示資訊訊息
 */
export function showInfo(message, title = '提示') {
  ElNotification({
    title,
    message,
    type: 'info',
    duration: 3000,
    position: 'top-right'
  })
}

/**
 * 顯示簡短訊息（Message）
 */
export function showMessage(message, type = 'info') {
  ElMessage({
    message,
    type,
    duration: 3000
  })
}

// ============================================================
// Vue 應用程式錯誤處理
// ============================================================

/**
 * 設定 Vue 應用程式錯誤處理
 */
export function setupErrorHandler(app) {
  // Vue 元件錯誤處理
  app.config.errorHandler = (err, vm, info) => {
    console.error('[Vue Error]', err)
    console.error('[Error Info]', info)

    // 開發環境顯示詳細錯誤
    if (import.meta.env.DEV) {
      showError(`${err.message}\n\n${info}`, 'Vue 錯誤')
    } else {
      showError('頁面發生錯誤，請重新整理')
    }
  }

  // Vue 警告處理（僅開發環境）
  if (import.meta.env.DEV) {
    app.config.warnHandler = (msg, vm, trace) => {
      console.warn('[Vue Warning]', msg)
      console.warn('[Trace]', trace)
    }
  }

  // 未處理的 Promise 錯誤
  window.addEventListener('unhandledrejection', (event) => {
    console.error('[Unhandled Promise Rejection]', event.reason)

    // 不顯示 Axios 錯誤（已在攔截器處理）
    if (event.reason?.isAxiosError) {
      return
    }

    if (import.meta.env.DEV) {
      showError(event.reason?.message || '未處理的非同步錯誤')
    }
  })

  // 全域 JavaScript 錯誤
  window.addEventListener('error', (event) => {
    console.error('[Global Error]', event.error)

    // 忽略腳本載入錯誤（由 Router 處理）
    if (event.message?.includes('Loading chunk') ||
        event.message?.includes('Loading CSS chunk')) {
      return
    }

    if (import.meta.env.DEV) {
      showError(event.error?.message || '發生 JavaScript 錯誤')
    }
  })
}

// ============================================================
// 匯出
// ============================================================

export default {
  handleApiError,
  showError,
  showWarning,
  showSuccess,
  showInfo,
  showMessage,
  setupErrorHandler,
  ApiError,
  ValidationError,
  NetworkError
}
