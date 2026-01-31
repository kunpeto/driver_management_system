/**
 * 系統設定 Pinia Store
 * 對應 tasks.md T041: 建立系統設定 Store
 *
 * 功能：
 * - 系統設定 CRUD 操作
 * - 部門配置管理
 * - Google 憑證驗證狀態
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { cloudApi } from '@/services/api'

// API 路徑
const API_BASE = '/api/settings'
const GOOGLE_API_BASE = '/api/google'

export const useSystemSettingsStore = defineStore('systemSettings', () => {
  // ============================================================
  // State
  // ============================================================

  // 所有設定
  const settings = ref([])

  // 部門配置快取
  const departmentConfigs = ref({
    '淡海': {},
    '安坑': {}
  })

  // 載入狀態
  const loading = ref(false)
  const saving = ref(false)

  // 錯誤訊息
  const error = ref(null)

  // 憑證驗證狀態
  const credentialValidation = ref({
    '淡海': { valid: null, error: null, details: null },
    '安坑': { valid: null, error: null, details: null }
  })

  // ============================================================
  // Getters
  // ============================================================

  // 依部門分組的設定
  const settingsByDepartment = computed(() => {
    const grouped = {
      global: [],
      '淡海': [],
      '安坑': []
    }

    settings.value.forEach(setting => {
      const dept = setting.department || 'global'
      if (grouped[dept]) {
        grouped[dept].push(setting)
      }
    })

    return grouped
  })

  // 取得設定值的便捷方法
  const getSettingValue = computed(() => {
    return (key, department = null) => {
      // 先找部門設定
      if (department) {
        const deptSetting = settings.value.find(
          s => s.key === key && s.department === department
        )
        if (deptSetting?.value) return deptSetting.value
      }

      // 再找 global 設定
      const globalSetting = settings.value.find(
        s => s.key === key && (s.department === 'global' || !s.department)
      )
      return globalSetting?.value || null
    }
  })

  // 是否有任何載入中
  const isLoading = computed(() => loading.value || saving.value)

  // ============================================================
  // Actions
  // ============================================================

  /**
   * 載入所有設定
   */
  async function fetchSettings(department = null) {
    loading.value = true
    error.value = null

    try {
      const params = department ? { department, include_global: true } : {}
      const response = await cloudApi.get(API_BASE, { params })

      if (department) {
        // 只更新指定部門的設定
        settings.value = settings.value.filter(
          s => s.department !== department && s.department !== 'global'
        )
        settings.value.push(...response.data.items)
      } else {
        settings.value = response.data.items
      }

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 載入部門完整配置
   */
  async function fetchDepartmentConfig(department) {
    loading.value = true
    error.value = null

    try {
      const response = await cloudApi.get(`${API_BASE}/department/${department}/config`)
      departmentConfigs.value[department] = response.data.settings
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * 建立設定
   */
  async function createSetting(data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(API_BASE, data)
      settings.value.push(response.data)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 更新設定
   */
  async function updateSetting(id, data) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.put(`${API_BASE}/${id}`, data)

      // 更新本地狀態
      const index = settings.value.findIndex(s => s.id === id)
      if (index !== -1) {
        settings.value[index] = response.data
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
   * 更新或建立設定
   */
  async function upsertSetting(key, value, department = null, description = null) {
    saving.value = true
    error.value = null

    try {
      const params = department ? { department } : {}
      const response = await cloudApi.put(
        `${API_BASE}/upsert/${key}`,
        { value, description },
        { params }
      )

      // 更新或新增本地狀態
      const index = settings.value.findIndex(
        s => s.key === key && s.department === department
      )
      if (index !== -1) {
        settings.value[index] = response.data
      } else {
        settings.value.push(response.data)
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
   * 刪除設定
   */
  async function deleteSetting(id) {
    saving.value = true
    error.value = null

    try {
      await cloudApi.delete(`${API_BASE}/${id}`)
      settings.value = settings.value.filter(s => s.id !== id)
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  /**
   * 批次更新設定
   */
  async function bulkUpsertSettings(settingsData) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${API_BASE}/bulk`, {
        settings: settingsData
      })

      // 重新載入所有設定
      await fetchSettings()

      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw err
    } finally {
      saving.value = false
    }
  }

  // ============================================================
  // Google 憑證驗證
  // ============================================================

  /**
   * 驗證 Service Account 格式
   */
  async function validateCredentials(base64Json) {
    try {
      const response = await cloudApi.post(`${GOOGLE_API_BASE}/validate-credentials`, {
        base64_json: base64Json
      })
      return response.data
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message)
    }
  }

  /**
   * 測試 Sheets 連線
   */
  async function testSheetsConnection(base64Json, spreadsheetId) {
    try {
      const response = await cloudApi.post(`${GOOGLE_API_BASE}/test-sheets`, {
        base64_json: base64Json,
        spreadsheet_id: spreadsheetId
      })
      return response.data
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message)
    }
  }

  /**
   * 測試 Drive 連線
   */
  async function testDriveConnection(base64Json, folderId) {
    try {
      const response = await cloudApi.post(`${GOOGLE_API_BASE}/test-drive`, {
        base64_json: base64Json,
        folder_id: folderId
      })
      return response.data
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message)
    }
  }

  /**
   * 執行 Dry Run 測試
   */
  async function dryRun(department, base64Json, sheetsId = null, driveFolderId = null) {
    try {
      const response = await cloudApi.post(`${GOOGLE_API_BASE}/dry-run`, {
        department,
        base64_json: base64Json,
        sheets_id: sheetsId,
        drive_folder_id: driveFolderId
      })

      // 更新驗證狀態
      credentialValidation.value[department] = {
        valid: response.data.success,
        error: response.data.sheets_error || response.data.drive_error,
        details: {
          sheets: response.data.sheets_details,
          drive: response.data.drive_details
        }
      }

      return response.data
    } catch (err) {
      credentialValidation.value[department] = {
        valid: false,
        error: err.response?.data?.detail || err.message,
        details: null
      }
      throw new Error(err.response?.data?.detail || err.message)
    }
  }

  /**
   * 快速驗證
   */
  async function quickValidate(base64Json, spreadsheetId) {
    try {
      const response = await cloudApi.post(`${GOOGLE_API_BASE}/quick-validate`, {
        base64_json: base64Json,
        spreadsheet_id: spreadsheetId
      })
      return response.data
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message)
    }
  }

  // ============================================================
  // 憑證儲存（修復 Gemini Review High Priority #1）
  // ============================================================

  /**
   * 儲存部門憑證
   */
  async function saveCredential(department, base64Json, authorizedEmail = null) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.post(`${GOOGLE_API_BASE}/credentials/${department}`, {
        base64_json: base64Json,
        authorized_email: authorizedEmail
      })
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw new Error(err.response?.data?.detail || err.message)
    } finally {
      saving.value = false
    }
  }

  /**
   * 取得部門憑證狀態
   */
  async function getCredentialStatus(department) {
    try {
      const response = await cloudApi.get(`${GOOGLE_API_BASE}/credentials/${department}`)
      return response.data
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message)
    }
  }

  /**
   * 取得所有部門憑證狀態
   */
  async function getAllCredentialStatus() {
    try {
      const response = await cloudApi.get(`${GOOGLE_API_BASE}/credentials`)
      return response.data
    } catch (err) {
      throw new Error(err.response?.data?.detail || err.message)
    }
  }

  /**
   * 刪除部門憑證
   */
  async function deleteCredential(department) {
    saving.value = true
    error.value = null

    try {
      const response = await cloudApi.delete(`${GOOGLE_API_BASE}/credentials/${department}`)
      return response.data
    } catch (err) {
      error.value = err.response?.data?.detail || err.message
      throw new Error(err.response?.data?.detail || err.message)
    } finally {
      saving.value = false
    }
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
   * 重置 Store
   */
  function $reset() {
    settings.value = []
    departmentConfigs.value = { '淡海': {}, '安坑': {} }
    loading.value = false
    saving.value = false
    error.value = null
    credentialValidation.value = {
      '淡海': { valid: null, error: null, details: null },
      '安坑': { valid: null, error: null, details: null }
    }
  }

  return {
    // State
    settings,
    departmentConfigs,
    loading,
    saving,
    error,
    credentialValidation,

    // Getters
    settingsByDepartment,
    getSettingValue,
    isLoading,

    // Actions - Settings
    fetchSettings,
    fetchDepartmentConfig,
    createSetting,
    updateSetting,
    upsertSetting,
    deleteSetting,
    bulkUpsertSettings,

    // Actions - Google Credentials
    validateCredentials,
    testSheetsConnection,
    testDriveConnection,
    dryRun,
    quickValidate,

    // Actions - Credential Storage
    saveCredential,
    getCredentialStatus,
    getAllCredentialStatus,
    deleteCredential,

    // Utils
    clearError,
    $reset
  }
})
