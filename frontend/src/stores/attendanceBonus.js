/**
 * 差勤加分 Pinia Store
 * 對應 tasks.md T205: 建立差勤加分 Store
 * 對應 spec.md: User Story 10 - 差勤加分自動處理
 *
 * 功能：
 * - 差勤加分處理（執行/預覽）
 * - 處理歷史查詢
 * - 月度統計查詢
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { cloudApi } from '@/services/api'

// API 路徑
const API_BASE = '/api/attendance-bonus'

export const useAttendanceBonusStore = defineStore('attendanceBonus', () => {
  // ============================================================
  // State
  // ============================================================

  // 處理結果
  const lastResult = ref(null)

  // 處理歷史
  const history = ref([])

  // 月度統計
  const monthStats = ref({})

  // 載入狀態
  const loading = ref(false)

  // ============================================================
  // Actions
  // ============================================================

  /**
   * 執行差勤加分處理
   *
   * @param {Object} params - { year, month, department }
   * @returns {Object} 處理結果
   */
  async function processBonus(params) {
    loading.value = true
    try {
      const response = await cloudApi.post(`${API_BASE}/process`, params)
      lastResult.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  /**
   * 預覽差勤加分處理
   *
   * @param {Object} params - { year, month, department }
   * @returns {Object} 預覽結果
   */
  async function previewBonus(params) {
    loading.value = true
    try {
      const response = await cloudApi.post(`${API_BASE}/preview`, params)
      lastResult.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  /**
   * 查詢處理歷史
   *
   * @param {Object} params - { year?, department?, limit? }
   * @returns {Array} 歷史記錄列表
   */
  async function fetchHistory(params = {}) {
    loading.value = true
    try {
      const queryParams = new URLSearchParams()
      if (params.year) queryParams.append('year', params.year)
      if (params.department) queryParams.append('department', params.department)
      if (params.limit) queryParams.append('limit', params.limit)

      const url = queryParams.toString()
        ? `${API_BASE}/history?${queryParams.toString()}`
        : `${API_BASE}/history`

      const response = await cloudApi.get(url)
      history.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  /**
   * 查詢月度加分統計
   *
   * @param {number} year - 年度
   * @param {number} month - 月份
   * @param {string} department - 部門（可選）
   * @returns {Object} 統計資料
   */
  async function fetchMonthStats(year, month, department = null) {
    loading.value = true
    try {
      let url = `${API_BASE}/results/${year}/${month}`
      if (department) {
        url += `?department=${encodeURIComponent(department)}`
      }

      const response = await cloudApi.get(url)
      monthStats.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  /**
   * 清除處理結果
   */
  function clearResult() {
    lastResult.value = null
  }

  // ============================================================
  // Return
  // ============================================================

  return {
    // State
    lastResult,
    history,
    monthStats,
    loading,

    // Actions
    processBonus,
    previewBonus,
    fetchHistory,
    fetchMonthStats,
    clearResult
  }
})
