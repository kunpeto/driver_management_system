/**
 * 員工管理 Pinia Store
 * 對應 tasks.md T057: 建立員工 Store
 *
 * 功能：
 * - 員工列表管理（CRUD）
 * - 部門篩選、離職狀態篩選
 * - 員工調動記錄
 * - 批次匯入/匯出
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { cloudApi } from '@/services/api'

// API 路徑
const API_BASE = '/api/employees'

export const useEmployeesStore = defineStore('employees', () => {
  // ============================================================
  // State
  // ============================================================

  // 員工列表
  const employees = ref([])
  const total = ref(0)

  // 當前選中的員工
  const currentEmployee = ref(null)

  // 調動記錄
  const transfers = ref([])

  // 統計資料
  const statistics = ref({
    total: 0,
    active: 0,
    resigned: 0,
    by_department: {}
  })

  // 載入狀態
  const loading = ref(false)
  const saving = ref(false)

  // 錯誤訊息
  const error = ref(null)

  // 篩選條件
  const filters = ref({
    department: null,
    includeResigned: false,
    search: ''
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

  // 依部門分組的員工
  const employeesByDepartment = computed(() => {
    const grouped = {
      '淡海': [],
      '安坑': []
    }

    employees.value.forEach(emp => {
      if (grouped[emp.current_department]) {
        grouped[emp.current_department].push(emp)
      }
    })

    return grouped
  })

  // 在職員工
  const activeEmployees = computed(() => {
    return employees.value.filter(emp => !emp.is_resigned)
  })

  // 離職員工
  const resignedEmployees = computed(() => {
    return employees.value.filter(emp => emp.is_resigned)
  })

  // 是否有任何載入中
  const isLoading = computed(() => loading.value || saving.value)

  // 是否有下一頁
  const hasMore = computed(() => {
    return pagination.value.skip + employees.value.length < total.value
  })

  // ============================================================
  // Actions - 員工列表
  // ============================================================

  /**
   * 載入員工列表
   */
  async function fetchEmployees(options = {}) {
    loading.value = true
    error.value = null

    try {
      const params = {
        department: options.department ?? filters.value.department,
        include_resigned: options.includeResigned ?? filters.value.includeResigned,
        search: options.search ?? filters.value.search,
        skip: options.skip ?? pagination.value.skip,
        limit: options.limit ?? pagination.value.pageSize
      }

      // 移除空值參數
      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === undefined || params[key] === '') {
          delete params[key]
        }
      })

      const response = await cloudApi.get(API_BASE, { params })

      employees.value = response.data.items
      total.value = response.data.total

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 載入更多員工（分頁）
   */
  async function loadMore() {
    if (!hasMore.value || loading.value) return

    const newSkip = pagination.value.skip + pagination.value.pageSize
    pagination.value.skip = newSkip

    loading.value = true
    error.value = null

    try {
      const params = {
        department: filters.value.department,
        include_resigned: filters.value.includeResigned,
        search: filters.value.search,
        skip: newSkip,
        limit: pagination.value.pageSize
      }

      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === undefined || params[key] === '') {
          delete params[key]
        }
      })

      const response = await cloudApi.get(API_BASE, { params })

      // 附加到現有列表
      employees.value.push(...response.data.items)

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 取得員工詳情
   */
  async function fetchEmployee(id) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${API_BASE}/${id}`)
      currentEmployee.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 根據員工編號取得員工
   */
  async function fetchEmployeeByCode(employeeCode) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${API_BASE}/by-employee-id/${employeeCode}`)
      currentEmployee.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 載入員工統計
   */
  async function fetchStatistics() {
    try {
      const response = await cloudApi.get(`${API_BASE}/statistics`)
      statistics.value = response.data
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  // ============================================================
  // Actions - CRUD
  // ============================================================

  /**
   * 建立員工
   */
  async function createEmployee(data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(API_BASE, data)

      // 加入本地列表
      employees.value.unshift(response.data)
      total.value++

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 更新員工
   */
  async function updateEmployee(id, data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.put(`${API_BASE}/${id}`, data)

      // 更新本地狀態
      const index = employees.value.findIndex(emp => emp.id === id)
      if (index !== -1) {
        employees.value[index] = response.data
      }

      if (currentEmployee.value?.id === id) {
        currentEmployee.value = response.data
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 標記員工離職
   */
  async function resignEmployee(id) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${API_BASE}/${id}/resign`)

      // 更新本地狀態
      const index = employees.value.findIndex(emp => emp.id === id)
      if (index !== -1) {
        employees.value[index] = response.data
      }

      if (currentEmployee.value?.id === id) {
        currentEmployee.value = response.data
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 標記員工復職
   */
  async function activateEmployee(id) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${API_BASE}/${id}/activate`)

      // 更新本地狀態
      const index = employees.value.findIndex(emp => emp.id === id)
      if (index !== -1) {
        employees.value[index] = response.data
      }

      if (currentEmployee.value?.id === id) {
        currentEmployee.value = response.data
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 刪除員工
   */
  async function deleteEmployee(id) {
    saving.value = true
    error.value = null

    try {
      await cloudApi.delete(`${API_BASE}/${id}`)

      // 從本地列表移除
      employees.value = employees.value.filter(emp => emp.id !== id)
      total.value--

      if (currentEmployee.value?.id === id) {
        currentEmployee.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 檢查員工編號是否存在
   */
  async function checkEmployeeExists(employeeCode) {
    try {
      const response = await cloudApi.get(`${API_BASE}/check/${employeeCode}`)
      return response.data.exists
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  // ============================================================
  // Actions - 員工調動
  // ============================================================

  /**
   * 執行員工調動
   */
  async function transferEmployee(employeeId, data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${API_BASE}/${employeeId}/transfer`, data)

      // 更新員工的部門
      const index = employees.value.findIndex(emp => emp.id === employeeId)
      if (index !== -1) {
        employees.value[index].current_department = data.to_department
      }

      if (currentEmployee.value?.id === employeeId) {
        currentEmployee.value.current_department = data.to_department
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 取得員工調動歷史
   */
  async function fetchTransferHistory(employeeId) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${API_BASE}/${employeeId}/transfers`)
      transfers.value = response.data.items
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 取得最近調動記錄
   */
  async function fetchRecentTransfers(days = 30, department = null) {
    loading.value = true
    error.value = null

    try {
      const params = { days }
      if (department) params.department = department

      const response = await cloudApi.get(`${API_BASE}/transfers/recent`, { params })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 取得調動統計
   */
  async function fetchTransferStatistics() {
    try {
      const response = await cloudApi.get(`${API_BASE}/transfers/statistics`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  // ============================================================
  // Actions - 批次匯入/匯出
  // ============================================================

  /**
   * 匯入員工
   */
  async function importEmployees(file, skipDuplicates = true) {
    saving.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('file', file)

      const params = { skip_duplicates: skipDuplicates }

      const response = await cloudApi.post(`${API_BASE}/import`, formData, {
        params,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      // 重新載入員工列表
      if (response.data.imported_count > 0) {
        await fetchEmployees()
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 驗證匯入檔案
   */
  async function validateImportFile(file) {
    loading.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await cloudApi.post(`${API_BASE}/validate`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 匯出員工（取得下載 URL）
   */
  function getExportUrl(options = {}) {
    const params = new URLSearchParams()

    if (options.department) params.append('department', options.department)
    if (options.includeResigned) params.append('include_resigned', 'true')
    if (options.search) params.append('search', options.search)
    if (options.format) params.append('format', options.format)

    const queryString = params.toString()
    return `/api${API_BASE}/export${queryString ? '?' + queryString : ''}`
  }

  /**
   * 取得匯出筆數
   */
  async function getExportCount(options = {}) {
    try {
      const params = {}
      if (options.department) params.department = options.department
      if (options.includeResigned) params.include_resigned = true
      if (options.search) params.search = options.search

      const response = await cloudApi.get(`${API_BASE}/export/count`, { params })
      return response.data.count
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  /**
   * 取得匯入範本下載 URL
   */
  function getTemplateUrl() {
    return `/api${API_BASE}/template`
  }

  /**
   * 取得範本欄位資訊
   */
  async function getTemplateColumns() {
    try {
      const response = await cloudApi.get(`${API_BASE}/template/columns`)
      return response.data.columns
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    }
  }

  // ============================================================
  // Actions - 篩選與分頁
  // ============================================================

  /**
   * 設定篩選條件
   */
  function setFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    // 重置分頁
    pagination.value.skip = 0
    pagination.value.page = 1
  }

  /**
   * 設定部門篩選
   */
  function setDepartmentFilter(department) {
    filters.value.department = department
    pagination.value.skip = 0
    pagination.value.page = 1
  }

  /**
   * 設定搜尋關鍵字
   */
  function setSearchFilter(search) {
    filters.value.search = search
    pagination.value.skip = 0
    pagination.value.page = 1
  }

  /**
   * 切換是否包含離職員工
   */
  function toggleIncludeResigned() {
    filters.value.includeResigned = !filters.value.includeResigned
    pagination.value.skip = 0
    pagination.value.page = 1
  }

  /**
   * 重置篩選條件
   */
  function resetFilters() {
    filters.value = {
      department: null,
      includeResigned: false,
      search: ''
    }
    pagination.value.skip = 0
    pagination.value.page = 1
  }

  // ============================================================
  // 輔助方法
  // ============================================================

  /**
   * 清除錯誤
   */
  function clearError() {
    error.value = null
  }

  /**
   * 清除當前員工
   */
  function clearCurrentEmployee() {
    currentEmployee.value = null
  }

  /**
   * 重置 Store
   */
  function $reset() {
    employees.value = []
    total.value = 0
    currentEmployee.value = null
    transfers.value = []
    statistics.value = { total: 0, active: 0, resigned: 0, by_department: {} }
    loading.value = false
    saving.value = false
    error.value = null
    filters.value = { department: null, includeResigned: false, search: '' }
    pagination.value = { page: 1, pageSize: 20, skip: 0 }
  }

  return {
    // State
    employees,
    total,
    currentEmployee,
    transfers,
    statistics,
    loading,
    saving,
    error,
    filters,
    pagination,

    // Getters
    employeesByDepartment,
    activeEmployees,
    resignedEmployees,
    isLoading,
    hasMore,

    // Actions - List
    fetchEmployees,
    loadMore,
    fetchEmployee,
    fetchEmployeeByCode,
    fetchStatistics,

    // Actions - CRUD
    createEmployee,
    updateEmployee,
    resignEmployee,
    activateEmployee,
    deleteEmployee,
    checkEmployeeExists,

    // Actions - Transfer
    transferEmployee,
    fetchTransferHistory,
    fetchRecentTransfers,
    fetchTransferStatistics,

    // Actions - Batch
    importEmployees,
    validateImportFile,
    getExportUrl,
    getExportCount,
    getTemplateUrl,
    getTemplateColumns,

    // Actions - Filters
    setFilters,
    setDepartmentFilter,
    setSearchFilter,
    toggleIncludeResigned,
    resetFilters,

    // Utils
    clearError,
    clearCurrentEmployee,
    $reset
  }
})
