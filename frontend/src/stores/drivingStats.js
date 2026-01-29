/**
 * 駕駛時數統計 Pinia Store
 * 對應 tasks.md T117: 建立駕駛時數 Store
 *
 * 功能：
 * - 勤務標準時間管理
 * - 每日駕駛時數統計
 * - 季度競賽排名查詢
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { cloudApi } from '@/services/api'

export const useDrivingStatsStore = defineStore('drivingStats', () => {
  // ============================================================
  // State
  // ============================================================

  // 勤務標準時間
  const routeStandardTimes = ref([])
  const routeStandardTimesTotal = ref(0)

  // 每日統計
  const dailyStats = ref([])
  const dailyStatsTotal = ref(0)

  // 季度統計
  const quarterStats = ref(null)
  const departmentQuarterStats = ref(null)

  // 競賽排名
  const competitionRanking = ref(null)
  const employeeHistory = ref([])
  const bonusTiers = ref(null)

  // 載入狀態
  const loading = ref(false)
  const saving = ref(false)

  // 錯誤訊息
  const error = ref(null)

  // 篩選條件
  const filters = ref({
    department: null,
    year: new Date().getFullYear(),
    quarter: Math.ceil((new Date().getMonth() + 1) / 3),
    employeeId: null,
    startDate: null,
    endDate: null
  })

  // ============================================================
  // Computed
  // ============================================================

  const currentQuarterLabel = computed(() => {
    return `${filters.value.year} Q${filters.value.quarter}`
  })

  // ============================================================
  // 勤務標準時間 API
  // ============================================================

  /**
   * 載入勤務標準時間列表
   */
  async function loadRouteStandardTimes(params = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get('/routes', {
        params: {
          department: params.department || filters.value.department,
          search: params.search,
          include_inactive: params.includeInactive || false,
          skip: params.skip || 0,
          limit: params.limit || 100
        }
      })

      routeStandardTimes.value = response.data.items
      routeStandardTimesTotal.value = response.data.total

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入勤務標準時間失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 建立勤務標準時間
   */
  async function createRouteStandardTime(data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post('/routes', data)
      routeStandardTimes.value.unshift(response.data)
      routeStandardTimesTotal.value++
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '建立勤務標準時間失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 更新勤務標準時間
   */
  async function updateRouteStandardTime(id, data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.put(`/routes/${id}`, data)
      const index = routeStandardTimes.value.findIndex(r => r.id === id)
      if (index !== -1) {
        routeStandardTimes.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '更新勤務標準時間失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 刪除勤務標準時間
   */
  async function deleteRouteStandardTime(id) {
    saving.value = true
    error.value = null

    try {
      await cloudApi.delete(`/routes/${id}`)
      const index = routeStandardTimes.value.findIndex(r => r.id === id)
      if (index !== -1) {
        routeStandardTimes.value.splice(index, 1)
        routeStandardTimesTotal.value--
      }
    } catch (err) {
      error.value = err.response?.data?.detail || '刪除勤務標準時間失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 匯入勤務標準時間
   */
  async function importRouteStandardTimes(file, department, updateExisting = true) {
    saving.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await cloudApi.post('/routes/import-excel', formData, {
        params: { department, update_existing: updateExisting },
        headers: { 'Content-Type': 'multipart/form-data' }
      })

      // 重新載入列表
      await loadRouteStandardTimes({ department })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '匯入失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  // ============================================================
  // 每日統計 API
  // ============================================================

  /**
   * 載入每日統計
   */
  async function loadDailyStats(params = {}) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get('/driving/stats', {
        params: {
          employee_id: params.employeeId || filters.value.employeeId,
          department: params.department || filters.value.department,
          start_date: params.startDate || filters.value.startDate,
          end_date: params.endDate || filters.value.endDate,
          skip: params.skip || 0,
          limit: params.limit || 100
        }
      })

      dailyStats.value = response.data.items
      dailyStatsTotal.value = response.data.total

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入每日統計失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 載入員工季度統計
   */
  async function loadQuarterStats(employeeId, year, quarter) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get('/driving/stats/quarter', {
        params: { employee_id: employeeId, year, quarter }
      })

      quarterStats.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入季度統計失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 載入部門季度統計
   */
  async function loadDepartmentQuarterStats(department, year, quarter, includeResigned = false) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get('/driving/stats/quarter/department', {
        params: { department, year, quarter, include_resigned: includeResigned }
      })

      departmentQuarterStats.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入部門季度統計失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // 競賽排名 API
  // ============================================================

  /**
   * 載入季度競賽排名
   */
  async function loadCompetitionRanking(year, quarter, department = null) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get('/driving/competition', {
        params: { year, quarter, department }
      })

      competitionRanking.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入競賽排名失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 載入員工競賽歷史
   */
  async function loadEmployeeHistory(employeeId, limit = 8) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`/driving/competition/employee/${employeeId}`, {
        params: { limit }
      })

      employeeHistory.value = response.data.history
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入員工歷史失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 手動計算競賽排名
   */
  async function calculateRanking(year, quarter) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post('/driving/competition/calculate', null, {
        params: { year, quarter }
      })

      // 重新載入排名
      await loadCompetitionRanking(year, quarter)

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '計算排名失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 載入獎金階層設定
   */
  async function loadBonusTiers() {
    try {
      const response = await cloudApi.get('/driving/competition/bonus-tiers')
      bonusTiers.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入獎金設定失敗'
      throw err
    }
  }

  // ============================================================
  // 輔助方法
  // ============================================================

  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }

  function clearError() {
    error.value = null
  }

  function reset() {
    routeStandardTimes.value = []
    routeStandardTimesTotal.value = 0
    dailyStats.value = []
    dailyStatsTotal.value = 0
    quarterStats.value = null
    departmentQuarterStats.value = null
    competitionRanking.value = null
    employeeHistory.value = []
    error.value = null
  }

  // ============================================================
  // Return
  // ============================================================

  return {
    // State
    routeStandardTimes,
    routeStandardTimesTotal,
    dailyStats,
    dailyStatsTotal,
    quarterStats,
    departmentQuarterStats,
    competitionRanking,
    employeeHistory,
    bonusTiers,
    loading,
    saving,
    error,
    filters,

    // Computed
    currentQuarterLabel,

    // Actions - 勤務標準時間
    loadRouteStandardTimes,
    createRouteStandardTime,
    updateRouteStandardTime,
    deleteRouteStandardTime,
    importRouteStandardTimes,

    // Actions - 每日統計
    loadDailyStats,
    loadQuarterStats,
    loadDepartmentQuarterStats,

    // Actions - 競賽排名
    loadCompetitionRanking,
    loadEmployeeHistory,
    calculateRanking,
    loadBonusTiers,

    // Actions - 輔助
    setFilters,
    clearError,
    reset
  }
})
