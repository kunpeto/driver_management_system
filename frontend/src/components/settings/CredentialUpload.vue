<template>
  <div class="credential-upload">
    <!-- 標題 -->
    <div class="upload-header">
      <h4>{{ title }}</h4>
      <span v-if="description" class="description">{{ description }}</span>
    </div>

    <!-- 檔案上傳區域 -->
    <div
      class="upload-area"
      :class="{
        'drag-over': isDragOver,
        'has-file': hasCredential,
        'is-valid': validationStatus === 'valid',
        'is-invalid': validationStatus === 'invalid',
        'is-validating': validationStatus === 'validating'
      }"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <input
        ref="fileInput"
        type="file"
        accept=".json"
        class="hidden-input"
        @change="handleFileSelect"
      />

      <!-- 上傳圖示與提示 -->
      <div v-if="!hasCredential && validationStatus !== 'validating'" class="upload-prompt">
        <div class="upload-icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>
        <p class="upload-text">拖放 JSON 憑證檔案到此處</p>
        <p class="upload-hint">或點擊選擇檔案</p>
      </div>

      <!-- 驗證中 -->
      <div v-if="validationStatus === 'validating'" class="validating">
        <div class="spinner"></div>
        <p>驗證中...</p>
      </div>

      <!-- 已上傳的憑證資訊 -->
      <div v-if="hasCredential && validationStatus !== 'validating'" class="credential-info">
        <div class="status-icon" :class="validationStatus">
          <svg v-if="validationStatus === 'valid'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12" />
          </svg>
          <svg v-else-if="validationStatus === 'invalid'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>

        <div class="info-content">
          <p v-if="credentialDetails?.project_id" class="project-id">
            專案: {{ credentialDetails.project_id }}
          </p>
          <p v-if="credentialDetails?.client_email" class="client-email">
            {{ credentialDetails.client_email }}
          </p>
          <p class="validation-message" :class="validationStatus">
            {{ validationMessage }}
          </p>
        </div>

        <button class="clear-btn" title="清除憑證" @click.stop="clearCredential">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 錯誤訊息 -->
    <div v-if="errorMessage" class="error-message">
      {{ errorMessage }}
    </div>

    <!-- 驗證按鈕 -->
    <div v-if="hasCredential && showValidateButton" class="action-buttons">
      <button
        class="validate-btn"
        :disabled="validationStatus === 'validating'"
        @click="runValidation"
      >
        {{ validationStatus === 'validating' ? '驗證中...' : '重新驗證' }}
      </button>
    </div>

    <!-- 驗證詳情 -->
    <div v-if="validationDetails && showDetails" class="validation-details">
      <h5>驗證詳情</h5>
      <div v-if="validationDetails.spreadsheet" class="detail-item">
        <span class="label">試算表:</span>
        <span class="value">{{ validationDetails.spreadsheet.spreadsheet_title }}</span>
      </div>
      <div v-if="validationDetails.spreadsheet?.sheet_names" class="detail-item">
        <span class="label">分頁:</span>
        <span class="value">{{ validationDetails.spreadsheet.sheet_names.join(', ') }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useSystemSettingsStore } from '@/stores/systemSettings'

// Props
const props = defineProps({
  title: {
    type: String,
    default: 'Service Account 憑證'
  },
  description: {
    type: String,
    default: ''
  },
  department: {
    type: String,
    required: true,
    validator: (value) => ['淡海', '安坑'].includes(value)
  },
  spreadsheetId: {
    type: String,
    default: ''
  },
  modelValue: {
    type: String,
    default: ''
  },
  showValidateButton: {
    type: Boolean,
    default: true
  },
  showDetails: {
    type: Boolean,
    default: true
  },
  autoValidate: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'validated', 'error'])

// Store
const settingsStore = useSystemSettingsStore()

// Refs
const fileInput = ref(null)
const isDragOver = ref(false)
const base64Credential = ref(props.modelValue)
const credentialDetails = ref(null)
const validationStatus = ref('pending') // pending, validating, valid, invalid
const validationMessage = ref('')
const validationDetails = ref(null)
const errorMessage = ref('')

// Computed
const hasCredential = computed(() => !!base64Credential.value)

// Watch modelValue changes
watch(() => props.modelValue, (newVal) => {
  if (newVal !== base64Credential.value) {
    base64Credential.value = newVal
    if (newVal && props.autoValidate) {
      validateCredential()
    }
  }
})

// Methods
function triggerFileInput() {
  fileInput.value?.click()
}

function handleDrop(e) {
  isDragOver.value = false
  const files = e.dataTransfer?.files
  if (files?.length) {
    processFile(files[0])
  }
}

function handleFileSelect(e) {
  const files = e.target?.files
  if (files?.length) {
    processFile(files[0])
  }
}

async function processFile(file) {
  // 驗證檔案類型
  if (!file.name.endsWith('.json')) {
    errorMessage.value = '請上傳 JSON 格式的憑證檔案'
    return
  }

  // 驗證檔案大小 (最大 100KB)
  if (file.size > 100 * 1024) {
    errorMessage.value = '檔案大小不能超過 100KB'
    return
  }

  errorMessage.value = ''

  try {
    // 讀取檔案內容
    const content = await readFileAsText(file)

    // 驗證 JSON 格式
    try {
      const json = JSON.parse(content)

      // 檢查必要欄位
      if (json.type !== 'service_account') {
        errorMessage.value = '憑證類型錯誤，請上傳 Service Account 憑證'
        return
      }

      // 儲存基本資訊
      credentialDetails.value = {
        project_id: json.project_id,
        client_email: json.client_email
      }

    } catch {
      errorMessage.value = 'JSON 格式無效'
      return
    }

    // 轉換為 Base64
    base64Credential.value = btoa(content)

    // 更新 v-model
    emit('update:modelValue', base64Credential.value)

    // 自動驗證
    if (props.autoValidate && props.spreadsheetId) {
      await validateCredential()
    } else {
      validationStatus.value = 'pending'
      validationMessage.value = '憑證已上傳，尚未驗證'
    }

  } catch (err) {
    errorMessage.value = `讀取檔案失敗: ${err.message}`
  }
}

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(new Error('讀取檔案失敗'))
    reader.readAsText(file)
  })
}

async function validateCredential() {
  if (!base64Credential.value) return

  validationStatus.value = 'validating'
  validationMessage.value = '驗證中...'
  errorMessage.value = ''

  try {
    if (props.spreadsheetId) {
      // 快速驗證（格式 + Sheets 連線）
      const result = await settingsStore.quickValidate(
        base64Credential.value,
        props.spreadsheetId
      )

      if (result.valid) {
        validationStatus.value = 'valid'
        validationMessage.value = '憑證有效，可存取試算表'
        validationDetails.value = result

        // 更新詳細資訊
        if (result.service_account) {
          credentialDetails.value = {
            ...credentialDetails.value,
            ...result.service_account
          }
        }

        emit('validated', { valid: true, details: result })
      } else {
        validationStatus.value = 'invalid'
        validationMessage.value = result.error || '驗證失敗'
        emit('validated', { valid: false, error: result.error })
      }
    } else {
      // 只驗證格式
      const result = await settingsStore.validateCredentials(base64Credential.value)

      if (result.valid) {
        validationStatus.value = 'valid'
        validationMessage.value = '憑證格式正確'
        credentialDetails.value = result.details
        emit('validated', { valid: true, details: result.details })
      } else {
        validationStatus.value = 'invalid'
        validationMessage.value = result.error || '憑證格式錯誤'
        emit('validated', { valid: false, error: result.error })
      }
    }
  } catch (err) {
    validationStatus.value = 'invalid'
    validationMessage.value = err.message
    emit('error', err)
  }
}

function runValidation() {
  validateCredential()
}

function clearCredential() {
  base64Credential.value = ''
  credentialDetails.value = null
  validationStatus.value = 'pending'
  validationMessage.value = ''
  validationDetails.value = null
  errorMessage.value = ''

  // 清除 file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }

  emit('update:modelValue', '')
}

// 暴露方法給父元件
defineExpose({
  validate: validateCredential,
  clear: clearCredential
})
</script>

<style scoped>
.credential-upload {
  width: 100%;
}

.upload-header {
  margin-bottom: 12px;
}

.upload-header h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.upload-header .description {
  font-size: 12px;
  color: #909399;
}

.upload-area {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: #fafafa;
}

.upload-area:hover {
  border-color: #409eff;
  background: #f5f7fa;
}

.upload-area.drag-over {
  border-color: #409eff;
  background: #ecf5ff;
}

.upload-area.has-file {
  border-style: solid;
  cursor: default;
}

.upload-area.is-valid {
  border-color: #67c23a;
  background: #f0f9eb;
}

.upload-area.is-invalid {
  border-color: #f56c6c;
  background: #fef0f0;
}

.upload-area.is-validating {
  border-color: #409eff;
}

.hidden-input {
  display: none;
}

.upload-prompt {
  color: #909399;
}

.upload-icon {
  margin-bottom: 12px;
}

.upload-icon svg {
  color: #c0c4cc;
}

.upload-text {
  margin: 0 0 4px 0;
  font-size: 14px;
}

.upload-hint {
  margin: 0;
  font-size: 12px;
}

.validating {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #409eff;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #e4e7ed;
  border-top-color: #409eff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.credential-info {
  display: flex;
  align-items: center;
  gap: 12px;
  text-align: left;
}

.status-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-icon.valid {
  background: #67c23a;
  color: white;
}

.status-icon.invalid {
  background: #f56c6c;
  color: white;
}

.status-icon.pending {
  background: #909399;
  color: white;
}

.info-content {
  flex: 1;
  min-width: 0;
}

.project-id {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.client-email {
  margin: 4px 0;
  font-size: 12px;
  color: #606266;
  word-break: break-all;
}

.validation-message {
  margin: 4px 0 0 0;
  font-size: 12px;
}

.validation-message.valid {
  color: #67c23a;
}

.validation-message.invalid {
  color: #f56c6c;
}

.validation-message.pending {
  color: #909399;
}

.clear-btn {
  flex-shrink: 0;
  padding: 8px;
  background: transparent;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  color: #909399;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: #f5f7fa;
  color: #f56c6c;
}

.error-message {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fef0f0;
  border-radius: 4px;
  font-size: 12px;
  color: #f56c6c;
}

.action-buttons {
  margin-top: 12px;
}

.validate-btn {
  padding: 8px 16px;
  background: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}

.validate-btn:hover:not(:disabled) {
  background: #66b1ff;
}

.validate-btn:disabled {
  background: #a0cfff;
  cursor: not-allowed;
}

.validation-details {
  margin-top: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.validation-details h5 {
  margin: 0 0 8px 0;
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  text-transform: uppercase;
}

.detail-item {
  display: flex;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 13px;
}

.detail-item .label {
  color: #909399;
  flex-shrink: 0;
}

.detail-item .value {
  color: #606266;
  word-break: break-word;
}
</style>
