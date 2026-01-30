/**
 * 履歷管理 Pinia Store
 * 對應 tasks.md T157: 建立履歷 Store
 *
 * 功能：
 * - 履歷列表管理（CRUD）
 * - 類型轉換
 * - 文件生成與下載
 * - 班表查詢
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { cloudApi } from '@/services/api'

// API 路徑
const API_BASE = '/profiles'

// 履歷類型定義
export const PROFILE_TYPES = {
  basic: { label: '基本履歷', color: 'info' },
  event_investigation: { label: '事件調查', color: 'warning' },
  personnel_interview: { label: '人員訪談', color: 'primary' },
  corrective_measures: { label: '矯正措施', color: 'danger' },
  assessment_notice: { label: '考核通知', color: 'success' }
}

// 轉換狀態定義
export const CONVERSION_STATUS = {
  pending: { label: '待處理', color: 'info' },
  converted: { label: '已轉換', color: 'warning' },
  completed: { label: '已完成', color: 'success' }
}

export const useProfilesStore = defineStore('profiles', () => {
  // ============================================================
  // State
  // ============================================================

  // 履歷列表
  const profiles = ref([])
  const total = ref(0)

  // 當前選中的履歷
  const currentProfile = ref(null)

  // 未結案統計
  const pendingStats = ref({ total: 0, by_type: {} })

  // 載入狀態
  const loading = ref(false)
  const saving = ref(false)
  const generating = ref(false)

  // 錯誤訊息
  const error = ref(null)

  // 篩選條件
  const filters = ref({
    department: null,
    profile_type: null,
    conversion_status: null,
    date_from: null,
    date_to: null,
    keyword: ''
  })

  // 分頁
  const pagination = ref({
    page: 1,
    pageSize: 20,
    skip: 0
  })

  // ============================================================
  // Getters
  // ============================================================

  const hasProfiles = computed(() => profiles.value.length > 0)
  const hasPending = computed(() => pendingStats.value.total > 0)

  // ============================================================
  // Actions
  // ============================================================

  /**
   * 載入履歷列表
   */
  async function fetchProfiles(options = {}) {
    loading.value = true
    error.value = null

    try {
      const params = {
        skip: pagination.value.skip,
        limit: pagination.value.pageSize,
        ...filters.value,
        ...options
      }

      // 移除空值
      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === '') {
          delete params[key]
        }
      })

      const response = await cloudApi.get(API_BASE, { params })
      profiles.value = response.data
      total.value = response.data.length
    } catch (err) {
      error.value = err.response?.data?.detail || '載入履歷失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 搜尋履歷
   */
  async function searchProfiles(params = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${API_BASE}/search`, { params })
      profiles.value = response.data
      total.value = response.data.length
    } catch (err) {
      error.value = err.response?.data?.detail || '搜尋履歷失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 取得單一履歷
   */
  async function fetchProfile(id) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${API_BASE}/${id}`)
      currentProfile.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入履歷失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 建立履歷
   */
  async function createProfile(data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(API_BASE, data)
      profiles.value.unshift(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '建立履歷失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 更新履歷
   */
  async function updateProfile(id, data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.put(`${API_BASE}/${id}`, data)
      const index = profiles.value.findIndex(p => p.id === id)
      if (index !== -1) {
        profiles.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '更新履歷失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 刪除履歷
   */
  async function deleteProfile(id) {
    saving.value = true
    error.value = null

    try {
      await cloudApi.delete(`${API_BASE}/${id}`)
      profiles.value = profiles.value.filter(p => p.id !== id)
    } catch (err) {
      error.value = err.response?.data?.detail || '刪除履歷失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 轉換履歷類型
   */
  async function convertProfile(id, targetType, subTableData = {}) {
    saving.value = true
    error.value = null

    try {
      const payload = {
        target_type: targetType,
        [targetType]: subTableData
      }
      const response = await cloudApi.post(`${API_BASE}/${id}/convert`, payload)
      const index = profiles.value.findIndex(p => p.id === id)
      if (index !== -1) {
        profiles.value[index] = response.data
      }
      currentProfile.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '轉換履歷失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 生成並下載文件
   */
  async function generateDocument(id) {
    generating.value = true
    error.value = null

    try {
      const response = await cloudApi.post(
        `${API_BASE}/${id}/generate-document`,
        {},
        { responseType: 'blob' }
      )

      // 從 Content-Disposition 取得檔名
      const contentDisposition = response.headers['content-disposition']
      let filename = `profile_${id}.docx`
      if (contentDisposition) {
        const match = contentDisposition.match(/filename\*?=(?:UTF-8'')?(.+)/)
        if (match) {
          filename = decodeURIComponent(match[1].replace(/['"]/g, ''))
        }
      }

      // 觸發下載
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = filename
      link.click()
      window.URL.revokeObjectURL(url)

      return true
    } catch (err) {
      error.value = err.response?.data?.detail || '文件生成失敗'
      throw err
    } finally {
      generating.value = false
    }
  }

  /**
   * 查詢班表
   */
  async function lookupSchedule(employeeId, eventDate) {
    try {
      const response = await cloudApi.get(`${API_BASE}/schedule-lookup`, {
        params: { employee_id: employeeId, event_date: eventDate }
      })
      return response.data
    } catch (err) {
      console.error('班表查詢失敗:', err)
      return null
    }
  }

  /**
   * 取得未結案列表
   */
  async function fetchPendingProfiles(params = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${API_BASE}/pending`, { params })
      profiles.value = response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入未結案列表失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 取得未結案統計
   */
  async function fetchPendingStats(department = null) {
    try {
      const params = department ? { department } : {}
      const response = await cloudApi.get(`${API_BASE}/pending/statistics`, { params })
      pendingStats.value = response.data
    } catch (err) {
      console.error('取得未結案統計失敗:', err)
    }
  }

  /**
   * 標記履歷為完成
   */
  async function markComplete(id, gdriveLink) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(
        `${API_BASE}/${id}/complete`,
        null,
        { params: { gdrive_link: gdriveLink } }
      )
      const index = profiles.value.findIndex(p => p.id === id)
      if (index !== -1) {
        profiles.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '標記完成失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 設定篩選條件並重新載入
   */
  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.skip = 0
    pagination.value.page = 1
    return fetchProfiles()
  }

  /**
   * 設定分頁並重新載入
   */
  function setPage(page) {
    pagination.value.page = page
    pagination.value.skip = (page - 1) * pagination.value.pageSize
    return fetchProfiles()
  }

  /**
   * 重置篩選條件
   */
  function resetFilters() {
    filters.value = {
      department: null,
      profile_type: null,
      conversion_status: null,
      date_from: null,
      date_to: null,
      keyword: ''
    }
    pagination.value.skip = 0
    pagination.value.page = 1
  }

  /**
   * 清除錯誤
   */
  function clearError() {
    error.value = null
  }

  return {
    // State
    profiles,
    total,
    currentProfile,
    pendingStats,
    loading,
    saving,
    generating,
    error,
    filters,
    pagination,

    // Getters
    hasProfiles,
    hasPending,

    // Actions
    fetchProfiles,
    searchProfiles,
    fetchProfile,
    createProfile,
    updateProfile,
    deleteProfile,
    convertProfile,
    generateDocument,
    lookupSchedule,
    fetchPendingProfiles,
    fetchPendingStats,
    markComplete,
    setFilters,
    setPage,
    resetFilters,
    clearError
  }
})
