<template>
  <div class="system-settings">
    <!-- 頁面標題 -->
    <PageHeader
      title="系統設定"
      description="管理淡海與安坑兩個部門的 Google 服務連接設定"
    />

    <!-- 連線狀態監控 (T078) -->
    <ConnectionStatus
      ref="connectionStatusRef"
      class="connection-status-panel"
      :auto-refresh="true"
      :refresh-interval="60000"
      :show-google-status="true"
    />

    <!-- 載入中 -->
    <LoadingSpinner v-if="loading" />

    <!-- 設定表單 -->
    <div v-else class="settings-container">
      <!-- 淡海部門設定 -->
      <section class="department-section">
        <div class="section-header">
          <h2>淡海部門設定</h2>
          <span class="department-badge danhai">淡海</span>
        </div>

        <div class="settings-form">
          <!-- Google Sheets ID -->
          <div class="form-group">
            <label>Google Sheets ID (班表)</label>
            <input
              v-model="formData.danhai.sheetsId"
              type="text"
              placeholder="輸入 Google Sheets ID"
              class="form-input"
            />
            <span class="help-text">
              從試算表網址中取得，格式如：1ABC123DEF456...
            </span>
          </div>

          <!-- Google Drive 資料夾 ID -->
          <div class="form-group">
            <label>Google Drive 資料夾 ID</label>
            <input
              v-model="formData.danhai.driveFolderId"
              type="text"
              placeholder="輸入 Google Drive 資料夾 ID"
              class="form-input"
            />
            <span class="help-text">
              用於儲存履歷 PDF 檔案
            </span>
          </div>

          <!-- 憑證上傳 -->
          <div class="form-group">
            <CredentialUpload
              v-model="formData.danhai.credential"
              title="Service Account 憑證"
              description="上傳 Google Cloud 服務帳戶的 JSON 金鑰檔案"
              department="淡海"
              :spreadsheet-id="formData.danhai.sheetsId"
              :show-details="true"
              @validated="handleDanhaiValidated"
              @error="handleValidationError"
            />
          </div>

          <!-- Dry Run 測試按鈕 -->
          <div class="form-actions">
            <button
              class="btn btn-secondary"
              :disabled="!canDryRunDanhai || dryRunning.danhai"
              @click="runDryRun('淡海')"
            >
              {{ dryRunning.danhai ? '測試中...' : '測試連線' }}
            </button>

            <!-- 測試結果 -->
            <div v-if="dryRunResults.danhai" class="dry-run-result" :class="dryRunResults.danhai.success ? 'success' : 'error'">
              <span v-if="dryRunResults.danhai.success">連線測試成功</span>
              <span v-else>
                {{ dryRunResults.danhai.sheets_error || dryRunResults.danhai.drive_error || '連線測試失敗' }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- 安坑部門設定 -->
      <section class="department-section">
        <div class="section-header">
          <h2>安坑部門設定</h2>
          <span class="department-badge ankeng">安坑</span>
        </div>

        <div class="settings-form">
          <!-- Google Sheets ID -->
          <div class="form-group">
            <label>Google Sheets ID (班表)</label>
            <input
              v-model="formData.ankeng.sheetsId"
              type="text"
              placeholder="輸入 Google Sheets ID"
              class="form-input"
            />
            <span class="help-text">
              從試算表網址中取得，格式如：1ABC123DEF456...
            </span>
          </div>

          <!-- Google Drive 資料夾 ID -->
          <div class="form-group">
            <label>Google Drive 資料夾 ID</label>
            <input
              v-model="formData.ankeng.driveFolderId"
              type="text"
              placeholder="輸入 Google Drive 資料夾 ID"
              class="form-input"
            />
            <span class="help-text">
              用於儲存履歷 PDF 檔案
            </span>
          </div>

          <!-- 憑證上傳 -->
          <div class="form-group">
            <CredentialUpload
              v-model="formData.ankeng.credential"
              title="Service Account 憑證"
              description="上傳 Google Cloud 服務帳戶的 JSON 金鑰檔案"
              department="安坑"
              :spreadsheet-id="formData.ankeng.sheetsId"
              :show-details="true"
              @validated="handleAnkengValidated"
              @error="handleValidationError"
            />
          </div>

          <!-- Dry Run 測試按鈕 -->
          <div class="form-actions">
            <button
              class="btn btn-secondary"
              :disabled="!canDryRunAnkeng || dryRunning.ankeng"
              @click="runDryRun('安坑')"
            >
              {{ dryRunning.ankeng ? '測試中...' : '測試連線' }}
            </button>

            <!-- 測試結果 -->
            <div v-if="dryRunResults.ankeng" class="dry-run-result" :class="dryRunResults.ankeng.success ? 'success' : 'error'">
              <span v-if="dryRunResults.ankeng.success">連線測試成功</span>
              <span v-else>
                {{ dryRunResults.ankeng.sheets_error || dryRunResults.ankeng.drive_error || '連線測試失敗' }}
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- 全域設定 -->
      <section class="department-section global-section">
        <div class="section-header">
          <h2>全域設定</h2>
          <span class="department-badge global">全域</span>
        </div>

        <div class="settings-form">
          <!-- 考核累計加重係數 -->
          <div class="form-group">
            <label>考核累計加重係數</label>
            <input
              v-model.number="formData.global.accumulationCoefficient"
              type="number"
              step="0.1"
              min="0"
              max="2"
              placeholder="0.5"
              class="form-input short"
            />
            <span class="help-text">
              累計加重公式：實際扣分 = 基本分 × [1 + 係數 × (第N次 - 1)]
            </span>
          </div>

          <!-- 同步間隔 -->
          <div class="form-group">
            <label>自動同步間隔（分鐘）</label>
            <input
              v-model.number="formData.global.syncInterval"
              type="number"
              step="5"
              min="5"
              max="1440"
              placeholder="60"
              class="form-input short"
            />
            <span class="help-text">
              系統自動從 Google Sheets 同步資料的間隔時間
            </span>
          </div>
        </div>
      </section>

      <!-- 儲存按鈕 -->
      <div class="save-actions">
        <button
          class="btn btn-primary"
          :disabled="saving"
          @click="saveSettings"
        >
          {{ saving ? '儲存中...' : '儲存設定' }}
        </button>

        <button
          class="btn btn-outline"
          :disabled="saving"
          @click="resetForm"
        >
          重設
        </button>
      </div>

      <!-- 錯誤訊息 -->
      <div v-if="errorMessage" class="error-banner">
        {{ errorMessage }}
        <button class="close-btn" @click="errorMessage = ''">×</button>
      </div>

      <!-- 成功訊息 -->
      <div v-if="successMessage" class="success-banner">
        {{ successMessage }}
        <button class="close-btn" @click="successMessage = ''">×</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useSystemSettingsStore } from '@/stores/systemSettings'
import PageHeader from '@/components/common/PageHeader.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import CredentialUpload from '@/components/settings/CredentialUpload.vue'
import ConnectionStatus from '@/components/common/ConnectionStatus.vue'

// Store
const settingsStore = useSystemSettingsStore()

// Refs (T078)
const connectionStatusRef = ref(null)

// 載入狀態
const loading = ref(true)
const saving = ref(false)

// 表單資料
const formData = ref({
  danhai: {
    sheetsId: '',
    driveFolderId: '',
    credential: ''
  },
  ankeng: {
    sheetsId: '',
    driveFolderId: '',
    credential: ''
  },
  global: {
    accumulationCoefficient: 0.5,
    syncInterval: 60
  }
})

// Dry Run 狀態
const dryRunning = ref({
  danhai: false,
  ankeng: false
})

const dryRunResults = ref({
  danhai: null,
  ankeng: null
})

// 驗證狀態
const validationStatus = ref({
  danhai: null,
  ankeng: null
})

// 訊息
const errorMessage = ref('')
const successMessage = ref('')

// Computed
const canDryRunDanhai = computed(() => {
  return formData.value.danhai.credential && formData.value.danhai.sheetsId
})

const canDryRunAnkeng = computed(() => {
  return formData.value.ankeng.credential && formData.value.ankeng.sheetsId
})

// Methods
async function loadSettings() {
  loading.value = true

  try {
    await settingsStore.fetchSettings()

    // 從 store 載入設定值
    const getValue = settingsStore.getSettingValue

    // 淡海設定
    formData.value.danhai.sheetsId = getValue('google_sheets_id', '淡海') || ''
    formData.value.danhai.driveFolderId = getValue('google_drive_folder_id', '淡海') || ''

    // 安坑設定
    formData.value.ankeng.sheetsId = getValue('google_sheets_id', '安坑') || ''
    formData.value.ankeng.driveFolderId = getValue('google_drive_folder_id', '安坑') || ''

    // 全域設定
    const coefficient = getValue('assessment_accumulation_coefficient', 'global')
    formData.value.global.accumulationCoefficient = coefficient ? parseFloat(coefficient) : 0.5

    const interval = getValue('sync_interval_minutes', 'global')
    formData.value.global.syncInterval = interval ? parseInt(interval) : 60

  } catch (err) {
    errorMessage.value = `載入設定失敗: ${err.message}`
  } finally {
    loading.value = false
  }
}

async function saveSettings() {
  saving.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const settingsToSave = []
    const credentialSavePromises = []

    // 淡海設定
    if (formData.value.danhai.sheetsId) {
      settingsToSave.push({
        key: 'google_sheets_id',
        value: formData.value.danhai.sheetsId,
        department: '淡海',
        description: '淡海班表 Google Sheets ID'
      })
    }
    if (formData.value.danhai.driveFolderId) {
      settingsToSave.push({
        key: 'google_drive_folder_id',
        value: formData.value.danhai.driveFolderId,
        department: '淡海',
        description: '淡海 Google Drive 資料夾 ID'
      })
    }
    // 儲存淡海憑證（修復 Gemini Review High Priority #1）
    if (formData.value.danhai.credential) {
      credentialSavePromises.push(
        settingsStore.saveCredential('淡海', formData.value.danhai.credential)
      )
    }

    // 安坑設定
    if (formData.value.ankeng.sheetsId) {
      settingsToSave.push({
        key: 'google_sheets_id',
        value: formData.value.ankeng.sheetsId,
        department: '安坑',
        description: '安坑班表 Google Sheets ID'
      })
    }
    if (formData.value.ankeng.driveFolderId) {
      settingsToSave.push({
        key: 'google_drive_folder_id',
        value: formData.value.ankeng.driveFolderId,
        department: '安坑',
        description: '安坑 Google Drive 資料夾 ID'
      })
    }
    // 儲存安坑憑證（修復 Gemini Review High Priority #1）
    if (formData.value.ankeng.credential) {
      credentialSavePromises.push(
        settingsStore.saveCredential('安坑', formData.value.ankeng.credential)
      )
    }

    // 全域設定
    settingsToSave.push({
      key: 'assessment_accumulation_coefficient',
      value: String(formData.value.global.accumulationCoefficient),
      department: 'global',
      description: '考核累計加重係數'
    })
    settingsToSave.push({
      key: 'sync_interval_minutes',
      value: String(formData.value.global.syncInterval),
      department: 'global',
      description: '自動同步間隔（分鐘）'
    })

    // 並行執行：儲存系統設定 + 儲存憑證
    await Promise.all([
      settingsStore.bulkUpsertSettings(settingsToSave),
      ...credentialSavePromises
    ])

    successMessage.value = '設定已儲存'

    // 儲存成功後重新檢查連線狀態 (T078)
    if (connectionStatusRef.value) {
      connectionStatusRef.value.refresh()
    }

    // 3 秒後清除成功訊息
    setTimeout(() => {
      successMessage.value = ''
    }, 3000)

  } catch (err) {
    errorMessage.value = `儲存設定失敗: ${err.message}`
  } finally {
    saving.value = false
  }
}

async function runDryRun(department) {
  const key = department === '淡海' ? 'danhai' : 'ankeng'

  dryRunning.value[key] = true
  dryRunResults.value[key] = null

  try {
    const data = formData.value[key]
    const result = await settingsStore.dryRun(
      department,
      data.credential,
      data.sheetsId,
      data.driveFolderId
    )

    dryRunResults.value[key] = result

  } catch (err) {
    dryRunResults.value[key] = {
      success: false,
      sheets_error: err.message
    }
  } finally {
    dryRunning.value[key] = false
  }
}

function handleDanhaiValidated(result) {
  validationStatus.value.danhai = result
}

function handleAnkengValidated(result) {
  validationStatus.value.ankeng = result
}

function handleValidationError(err) {
  errorMessage.value = `憑證驗證失敗: ${err.message}`
}

function resetForm() {
  loadSettings()
  dryRunResults.value = { danhai: null, ankeng: null }
  errorMessage.value = ''
  successMessage.value = ''
}

// Lifecycle
onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.system-settings {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

/* T078: 連線狀態面板樣式 */
.connection-status-panel {
  margin-bottom: 24px;
}

.settings-container {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.department-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.section-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.department-badge {
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.department-badge.danhai {
  background: #e1f3d8;
  color: #67c23a;
}

.department-badge.ankeng {
  background: #fdf6ec;
  color: #e6a23c;
}

.department-badge.global {
  background: #ecf5ff;
  color: #409eff;
}

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
}

.form-input {
  padding: 10px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #409eff;
}

.form-input.short {
  width: 120px;
}

.help-text {
  font-size: 12px;
  color: #909399;
}

.form-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 8px;
}

.btn {
  padding: 10px 20px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #409eff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #66b1ff;
}

.btn-secondary {
  background: #f5f7fa;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.btn-secondary:hover:not(:disabled) {
  background: #ecf5ff;
  border-color: #409eff;
  color: #409eff;
}

.btn-outline {
  background: transparent;
  color: #606266;
  border: 1px solid #dcdfe6;
}

.btn-outline:hover:not(:disabled) {
  background: #f5f7fa;
}

.dry-run-result {
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 13px;
}

.dry-run-result.success {
  background: #f0f9eb;
  color: #67c23a;
}

.dry-run-result.error {
  background: #fef0f0;
  color: #f56c6c;
}

.save-actions {
  display: flex;
  gap: 12px;
  padding-top: 16px;
}

.error-banner,
.success-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-radius: 4px;
  font-size: 14px;
}

.error-banner {
  background: #fef0f0;
  color: #f56c6c;
}

.success-banner {
  background: #f0f9eb;
  color: #67c23a;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 18px;
  cursor: pointer;
  color: inherit;
  opacity: 0.6;
}

.close-btn:hover {
  opacity: 1;
}

.global-section {
  border: 2px dashed #dcdfe6;
  background: #fafafa;
}
</style>
