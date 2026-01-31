/**
 * 考核系統 Pinia Store
 * 對應 tasks.md T191: 建立考核 Store
 * 對應 spec.md: User Story 9 - 考核系統
 *
 * 功能：
 * - 考核標準管理（CRUD）
 * - 考核記錄管理（CRUD）
 * - R02-R05 責任判定支援
 * - 月度獎勵計算
 * - 年度摘要查詢
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { cloudApi } from '@/services/api'

// API 路徑
const STANDARDS_API = '/api/assessment-standards'
const RECORDS_API = '/api/assessment-records'

// 考核類別定義
export const ASSESSMENT_CATEGORIES = {
  // 扣分類
  D: { label: '服勤類', color: 'info', type: 'deduction' },
  W: { label: '酒測類', color: 'danger', type: 'deduction' },
  O: { label: '其他類', color: 'secondary', type: 'deduction' },
  S: { label: '行車類', color: 'warning', type: 'deduction' },
  R: { label: '責任類', color: 'danger', type: 'deduction' },
  // 加分類
  '+M': { label: '月度獎勵', color: 'success', type: 'bonus' },
  '+A': { label: '出勤類', color: 'primary', type: 'bonus' },
  '+B': { label: '表揚類', color: 'success', type: 'bonus' },
  '+C': { label: '合理化建議', color: 'info', type: 'bonus' },
  '+R': { label: '特殊貢獻', color: 'warning', type: 'bonus' }
}

// 責任程度定義
export const RESPONSIBILITY_LEVELS = {
  '完全責任': { coefficient: 1.0, minFaults: 7, maxFaults: 9, color: 'danger' },
  '主要責任': { coefficient: 0.7, minFaults: 4, maxFaults: 6, color: 'warning' },
  '次要責任': { coefficient: 0.3, minFaults: 1, maxFaults: 3, color: 'info' }
}

// R02-R05 需要責任判定的代碼
export const R_TYPE_CODES = ['R02', 'R03', 'R04', 'R05']

// 9 項疏失查核項目
export const FAULT_CHECKLIST_ITEMS = [
  { key: 'awareness_delay', label: '察覺過晚或誤判' },
  { key: 'report_delay', label: '通報延遲或不完整' },
  { key: 'unfamiliar_procedure', label: '不熟悉故障排除程序' },
  { key: 'wrong_operation', label: '故障排除決策/操作錯誤' },
  { key: 'slow_action', label: '動作遲緩' },
  { key: 'unconfirmed_result', label: '未確認結果或誤認完成' },
  { key: 'no_progress_report', label: '未主動回報處理進度' },
  { key: 'repeated_error', label: '重複性錯誤' },
  { key: 'mental_state_issue', label: '心理狀態影響表現' }
]

export const useAssessmentsStore = defineStore('assessments', () => {
  // ============================================================
  // State
  // ============================================================

  // 考核標準
  const standards = ref([])
  const standardsByCategory = ref({})
  const currentStandard = ref(null)

  // 考核記錄
  const records = ref([])
  const currentRecord = ref(null)

  // 員工年度摘要
  const employeeSummary = ref(null)

  // 月度獎勵
  const monthlyRewards = ref([])
  const monthlyRewardPreview = ref(null)

  // 責任判定查核表模板
  const checklistTemplate = ref(null)

  // 載入狀態
  const loading = ref(false)
  const saving = ref(false)
  const calculating = ref(false)

  // 錯誤訊息
  const error = ref(null)

  // 篩選條件
  const filters = ref({
    employee_id: null,
    year: new Date().getFullYear(),
    month: null,
    category: null
  })

  // ============================================================
  // Getters
  // ============================================================

  const hasStandards = computed(() => standards.value.length > 0)
  const hasRecords = computed(() => records.value.length > 0)

  const deductionStandards = computed(() =>
    standards.value.filter(s => s.base_points < 0)
  )

  const bonusStandards = computed(() =>
    standards.value.filter(s => s.base_points > 0)
  )

  const rTypeStandards = computed(() =>
    standards.value.filter(s => R_TYPE_CODES.includes(s.code))
  )

  // ============================================================
  // Actions - 考核標準
  // ============================================================

  /**
   * 載入所有考核標準
   */
  async function fetchStandards(options = {}) {
    loading.value = true
    error.value = null

    try {
      const params = { is_active: true, ...options }
      const response = await cloudApi.get(STANDARDS_API, { params })
      standards.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入考核標準失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 載入按類別分組的考核標準
   */
  async function fetchStandardsByCategory() {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${STANDARDS_API}/categories`)
      standardsByCategory.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入考核標準分類失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 搜尋考核標準
   */
  async function searchStandards(keyword) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${STANDARDS_API}/search`, {
        params: { keyword }
      })
      standards.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '搜尋考核標準失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 取得 R02-R05 項目
   */
  async function fetchRTypeStandards() {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${STANDARDS_API}/r-type`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入 R 類項目失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 建立考核標準（管理員）
   */
  async function createStandard(data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(STANDARDS_API, data)
      standards.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '建立考核標準失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 更新考核標準（管理員）
   */
  async function updateStandard(id, data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.put(`${STANDARDS_API}/${id}`, data)
      const index = standards.value.findIndex(s => s.id === id)
      if (index !== -1) {
        standards.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '更新考核標準失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 切換考核標準啟用狀態（管理員）
   */
  async function toggleStandardActive(id) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${STANDARDS_API}/${id}/toggle-active`)
      const index = standards.value.findIndex(s => s.id === id)
      if (index !== -1) {
        standards.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '切換狀態失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 初始化預設 61 項考核標準（管理員）
   */
  async function initializeDefaultStandards() {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${STANDARDS_API}/initialize-defaults`)
      if (response.data.created_count > 0) {
        await fetchStandards()
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '初始化失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  // ============================================================
  // Actions - 考核記錄
  // ============================================================

  /**
   * 載入員工考核記錄
   */
  async function fetchRecords(employeeId, options = {}) {
    loading.value = true
    error.value = null

    try {
      const params = {
        employee_id: employeeId,
        year: filters.value.year,
        ...options
      }

      // 移除空值
      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === undefined) {
          delete params[key]
        }
      })

      const response = await cloudApi.get(RECORDS_API, { params })
      records.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入考核記錄失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 取得單一考核記錄
   */
  async function fetchRecord(id) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${RECORDS_API}/${id}`)
      currentRecord.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入考核記錄失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 建立考核記錄
   */
  async function createRecord(data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(RECORDS_API, data)
      records.value.unshift(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '建立考核記錄失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 更新考核記錄
   */
  async function updateRecord(id, data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.put(`${RECORDS_API}/${id}`, data)
      const index = records.value.findIndex(r => r.id === id)
      if (index !== -1) {
        records.value[index] = response.data
      }
      currentRecord.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '更新考核記錄失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 刪除考核記錄（軟刪除）
   */
  async function deleteRecord(id) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.delete(`${RECORDS_API}/${id}`)
      // 軟刪除後更新列表中的狀態
      const index = records.value.findIndex(r => r.id === id)
      if (index !== -1) {
        records.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '刪除考核記錄失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 還原已刪除的考核記錄
   */
  async function restoreRecord(id) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${RECORDS_API}/${id}/restore`)
      const index = records.value.findIndex(r => r.id === id)
      if (index !== -1) {
        records.value[index] = response.data
      }
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '還原考核記錄失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  // ============================================================
  // Actions - R02-R05 責任判定
  // ============================================================

  /**
   * 取得責任判定查核表模板
   */
  async function fetchChecklistTemplate() {
    try {
      const response = await cloudApi.get(`${RECORDS_API}/checklist-template`)
      checklistTemplate.value = response.data
      return response.data
    } catch (err) {
      console.error('取得查核表模板失敗:', err)
      // 返回預設模板
      return {
        keys: FAULT_CHECKLIST_ITEMS.map(i => i.key),
        labels: Object.fromEntries(FAULT_CHECKLIST_ITEMS.map(i => [i.key, i.label])),
        template: Object.fromEntries(FAULT_CHECKLIST_ITEMS.map(i => [i.key, false])),
        responsibility_rules: RESPONSIBILITY_LEVELS
      }
    }
  }

  /**
   * 更新 R02-R05 責任判定
   */
  async function updateFaultResponsibility(recordId, data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(
        `${RECORDS_API}/${recordId}/fault-responsibility`,
        data
      )
      const index = records.value.findIndex(r => r.id === recordId)
      if (index !== -1) {
        records.value[index] = response.data
      }
      currentRecord.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '更新責任判定失敗'
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 預覽考核分數計算結果
   */
  async function previewCalculation(basePoints, cumulativeCount, checklistResults = null) {
    try {
      const params = {
        base_points: basePoints,
        cumulative_count: cumulativeCount
      }
      if (checklistResults) {
        params.checklist_results = JSON.stringify(checklistResults)
      }
      const response = await cloudApi.post(`${RECORDS_API}/preview-calculation`, null, { params })
      return response.data
    } catch (err) {
      console.error('預覽計算失敗:', err)
      return null
    }
  }

  /**
   * 判斷考核代碼是否需要責任判定
   */
  function isResponsibilityRequired(code) {
    return R_TYPE_CODES.includes(code)
  }

  /**
   * 根據疏失項數計算責任程度
   */
  function calculateResponsibilityLevel(faultCount) {
    if (faultCount >= 7) {
      return { level: '完全責任', coefficient: 1.0 }
    } else if (faultCount >= 4) {
      return { level: '主要責任', coefficient: 0.7 }
    } else if (faultCount >= 1) {
      return { level: '次要責任', coefficient: 0.3 }
    }
    return { level: '無責任', coefficient: 0 }
  }

  /**
   * 計算累計倍率
   */
  function calculateCumulativeMultiplier(count) {
    if (count <= 0) return 1.0
    return 1.0 + 0.5 * (count - 1)
  }

  // ============================================================
  // Actions - 員工年度摘要
  // ============================================================

  /**
   * 取得員工年度考核摘要
   */
  async function fetchEmployeeSummary(employeeId, year) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${RECORDS_API}/summary`, {
        params: { employee_id: employeeId, year }
      })
      employeeSummary.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入年度摘要失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // Actions - 月度獎勵
  // ============================================================

  /**
   * 預覽月度獎勵計算結果
   */
  async function previewMonthlyRewards(year, month) {
    calculating.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${RECORDS_API}/monthly-rewards/preview`, {
        year,
        month
      })
      monthlyRewardPreview.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '預覽月度獎勵失敗'
      throw err
    } finally {
      calculating.value = false
    }
  }

  /**
   * 執行月度獎勵計算（管理員）
   */
  async function calculateMonthlyRewards(year, month) {
    calculating.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${RECORDS_API}/monthly-rewards/calculate`, {
        year,
        month
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '計算月度獎勵失敗'
      throw err
    } finally {
      calculating.value = false
    }
  }

  /**
   * 取得月度獎勵列表
   */
  async function fetchMonthlyRewards(year, month) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${RECORDS_API}/monthly-rewards/list`, {
        params: { year, month }
      })
      monthlyRewards.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '載入月度獎勵失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  // ============================================================
  // Actions - 年度重置
  // ============================================================

  /**
   * 預覽年度重置影響
   */
  async function previewAnnualReset(year = null) {
    loading.value = true
    error.value = null

    try {
      const params = year ? { year } : {}
      const response = await cloudApi.post(`${RECORDS_API}/annual-reset/preview`, null, { params })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '預覽年度重置失敗'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 執行年度重置（管理員）
   */
  async function executeAnnualReset(year = null, confirm = false) {
    if (!confirm) {
      throw new Error('請確認執行年度重置')
    }

    calculating.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${RECORDS_API}/annual-reset`, {
        year,
        confirm: true
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || '年度重置失敗'
      throw err
    } finally {
      calculating.value = false
    }
  }

  /**
   * 檢查是否可執行年度重置
   */
  async function checkResetEligibility() {
    try {
      const response = await cloudApi.get(`${RECORDS_API}/annual-reset/eligibility`)
      return response.data
    } catch (err) {
      console.error('檢查重置資格失敗:', err)
      return { can_execute: false }
    }
  }

  // ============================================================
  // Utility Functions
  // ============================================================

  /**
   * 設定篩選條件
   */
  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
  }

  /**
   * 重置篩選條件
   */
  function resetFilters() {
    filters.value = {
      employee_id: null,
      year: new Date().getFullYear(),
      month: null,
      category: null
    }
  }

  /**
   * 清除錯誤
   */
  function clearError() {
    error.value = null
  }

  /**
   * 取得類別顏色
   */
  function getCategoryColor(category) {
    return ASSESSMENT_CATEGORIES[category]?.color || 'secondary'
  }

  /**
   * 取得類別標籤
   */
  function getCategoryLabel(category) {
    return ASSESSMENT_CATEGORIES[category]?.label || category
  }

  return {
    // State
    standards,
    standardsByCategory,
    currentStandard,
    records,
    currentRecord,
    employeeSummary,
    monthlyRewards,
    monthlyRewardPreview,
    checklistTemplate,
    loading,
    saving,
    calculating,
    error,
    filters,

    // Getters
    hasStandards,
    hasRecords,
    deductionStandards,
    bonusStandards,
    rTypeStandards,

    // Actions - 考核標準
    fetchStandards,
    fetchStandardsByCategory,
    searchStandards,
    fetchRTypeStandards,
    createStandard,
    updateStandard,
    toggleStandardActive,
    initializeDefaultStandards,

    // Actions - 考核記錄
    fetchRecords,
    fetchRecord,
    createRecord,
    updateRecord,
    deleteRecord,
    restoreRecord,

    // Actions - R02-R05 責任判定
    fetchChecklistTemplate,
    updateFaultResponsibility,
    previewCalculation,
    isResponsibilityRequired,
    calculateResponsibilityLevel,
    calculateCumulativeMultiplier,

    // Actions - 員工年度摘要
    fetchEmployeeSummary,

    // Actions - 月度獎勵
    previewMonthlyRewards,
    calculateMonthlyRewards,
    fetchMonthlyRewards,

    // Actions - 年度重置
    previewAnnualReset,
    executeAnnualReset,
    checkResetEligibility,

    // Utility
    setFilters,
    resetFilters,
    clearError,
    getCategoryColor,
    getCategoryLabel
  }
})
