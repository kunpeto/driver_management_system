<template>
  <div class="batch-operations">
    <!-- 標籤頁 -->
    <div class="tabs">
      <button
        :class="['tab', { active: activeTab === 'import' }]"
        @click="activeTab = 'import'"
      >
        匯入員工
      </button>
      <button
        :class="['tab', { active: activeTab === 'export' }]"
        @click="activeTab = 'export'"
      >
        匯出員工
      </button>
    </div>

    <!-- 匯入區塊 -->
    <div v-if="activeTab === 'import'" class="tab-content">
      <div class="import-section">
        <!-- 下載範本 -->
        <div class="template-download">
          <p>下載匯入範本，按照格式填寫員工資料後上傳</p>
          <AppButton size="small" @click="downloadTemplate">
            下載範本
          </AppButton>
        </div>

        <!-- 檔案上傳 -->
        <div class="file-upload">
          <input
            ref="fileInput"
            type="file"
            accept=".xlsx,.xls"
            style="display: none"
            @change="handleFileSelect"
          />

          <div
            class="upload-area"
            :class="{ dragover: isDragover }"
            @click="$refs.fileInput.click()"
            @dragover.prevent="isDragover = true"
            @dragleave.prevent="isDragover = false"
            @drop.prevent="handleDrop"
          >
            <div v-if="!selectedFile" class="upload-placeholder">
              <span class="upload-icon">📄</span>
              <p>點擊或拖放 Excel 檔案</p>
              <p class="upload-hint">支援 .xlsx, .xls 格式</p>
            </div>
            <div v-else class="selected-file">
              <span class="file-icon">📊</span>
              <span class="file-name">{{ selectedFile.name }}</span>
              <AppButton size="small" @click.stop="clearFile">
                移除
              </AppButton>
            </div>
          </div>
        </div>

        <!-- 匯入選項 -->
        <div v-if="selectedFile" class="import-options">
          <label class="checkbox-label">
            <input v-model="skipDuplicates" type="checkbox" />
            跳過重複的員工編號
          </label>
        </div>

        <!-- 驗證結果 -->
        <div v-if="validationResult" class="validation-result">
          <div :class="['result-header', validationResult.success ? 'success' : 'error']">
            <span class="result-icon">{{ validationResult.success ? '✓' : '✗' }}</span>
            <span>{{ validationResult.success ? '驗證通過' : '驗證失敗' }}</span>
          </div>
          <div class="result-stats">
            <span>總筆數：{{ validationResult.total_rows }}</span>
            <span v-if="validationResult.error_count > 0" class="error-count">
              錯誤：{{ validationResult.error_count }}
            </span>
          </div>
          <div v-if="validationResult.errors?.length > 0" class="error-list">
            <div
              v-for="err in validationResult.errors.slice(0, 5)"
              :key="err.row"
              class="error-item"
            >
              第 {{ err.row }} 行：{{ err.error }}
            </div>
            <div v-if="validationResult.errors.length > 5" class="more-errors">
              還有 {{ validationResult.errors.length - 5 }} 個錯誤...
            </div>
          </div>
        </div>

        <!-- 匯入結果 -->
        <div v-if="importResult" class="import-result">
          <div :class="['result-header', importResult.success ? 'success' : 'warning']">
            <span class="result-icon">{{ importResult.success ? '✓' : '⚠' }}</span>
            <span>匯入完成</span>
          </div>
          <div class="result-stats">
            <span>成功匯入：{{ importResult.imported_count }}</span>
            <span v-if="importResult.skipped_count > 0">跳過：{{ importResult.skipped_count }}</span>
            <span v-if="importResult.error_count > 0" class="error-count">
              失敗：{{ importResult.error_count }}
            </span>
          </div>
        </div>

        <!-- 操作按鈕 -->
        <div class="action-buttons">
          <AppButton
            v-if="selectedFile && !validationResult"
            :loading="validating"
            @click="validateFile"
          >
            驗證檔案
          </AppButton>
          <AppButton
            v-if="validationResult?.success"
            :loading="importing"
            variant="primary"
            @click="importFile"
          >
            開始匯入
          </AppButton>
        </div>
      </div>
    </div>

    <!-- 匯出區塊 -->
    <div v-if="activeTab === 'export'" class="tab-content">
      <div class="export-section">
        <!-- 篩選選項 -->
        <div class="export-options">
          <div class="option-group">
            <label class="option-label">部門</label>
            <select v-model="exportOptions.department" class="option-select">
              <option :value="null">全部部門</option>
              <option value="淡海">淡海</option>
              <option value="安坑">安坑</option>
            </select>
          </div>

          <div class="option-group">
            <label class="option-label">格式</label>
            <select v-model="exportOptions.format" class="option-select">
              <option value="xlsx">Excel (.xlsx)</option>
              <option value="csv">CSV (.csv)</option>
            </select>
          </div>

          <div class="option-group checkbox">
            <label class="checkbox-label">
              <input v-model="exportOptions.includeResigned" type="checkbox" />
              包含離職員工
            </label>
          </div>
        </div>

        <!-- 匯出預覽 -->
        <div class="export-preview">
          <div class="preview-count">
            <span v-if="exportCount !== null">
              預計匯出 <strong>{{ exportCount }}</strong> 筆資料
            </span>
            <AppButton size="small" @click="refreshExportCount">
              重新計算
            </AppButton>
          </div>
        </div>

        <!-- 匯出按鈕 -->
        <div class="action-buttons">
          <AppButton
            variant="primary"
            :disabled="exportCount === 0"
            @click="exportEmployees"
          >
            下載檔案
          </AppButton>
        </div>
      </div>
    </div>

    <!-- 關閉按鈕 -->
    <div class="dialog-footer">
      <AppButton @click="$emit('close')">
        關閉
      </AppButton>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useEmployeesStore } from '@/stores/employees'
import AppButton from '@/components/common/AppButton.vue'

const emit = defineEmits(['import-complete', 'close'])

const store = useEmployeesStore()

// 狀態
const activeTab = ref('import')
const selectedFile = ref(null)
const isDragover = ref(false)
const skipDuplicates = ref(true)
const validating = ref(false)
const importing = ref(false)
const validationResult = ref(null)
const importResult = ref(null)
const exportCount = ref(null)

// 匯出選項
const exportOptions = ref({
  department: null,
  includeResigned: false,
  format: 'xlsx'
})

// 監聽匯出選項變化
watch(exportOptions, () => {
  refreshExportCount()
}, { deep: true })

// 生命週期
onMounted(() => {
  refreshExportCount()
})

// 檔案選擇
function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    selectFile(file)
  }
}

function handleDrop(event) {
  isDragover.value = false
  const file = event.dataTransfer.files[0]
  if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
    selectFile(file)
  }
}

function selectFile(file) {
  selectedFile.value = file
  validationResult.value = null
  importResult.value = null
}

function clearFile() {
  selectedFile.value = null
  validationResult.value = null
  importResult.value = null
}

// 下載範本
function downloadTemplate() {
  const url = store.getTemplateUrl()
  window.open(url, '_blank')
}

// 驗證檔案
async function validateFile() {
  if (!selectedFile.value) return

  validating.value = true
  try {
    const result = await store.validateImportFile(selectedFile.value)
    validationResult.value = result
  } catch (err) {
    validationResult.value = {
      success: false,
      total_rows: 0,
      error_count: 1,
      errors: [{ row: 0, error: err.message || '驗證失敗' }]
    }
  } finally {
    validating.value = false
  }
}

// 匯入檔案
async function importFile() {
  if (!selectedFile.value || !validationResult.value?.success) return

  importing.value = true
  try {
    const result = await store.importEmployees(selectedFile.value, skipDuplicates.value)
    importResult.value = result

    if (result.imported_count > 0) {
      emit('import-complete')
    }
  } catch (err) {
    importResult.value = {
      success: false,
      imported_count: 0,
      skipped_count: 0,
      error_count: 1,
      errors: [{ row: 0, error: err.message || '匯入失敗' }]
    }
  } finally {
    importing.value = false
  }
}

// 重新計算匯出筆數
async function refreshExportCount() {
  try {
    exportCount.value = await store.getExportCount(exportOptions.value)
  } catch (err) {
    console.error('取得匯出筆數失敗:', err)
    exportCount.value = null
  }
}

// 匯出員工
function exportEmployees() {
  const url = store.getExportUrl(exportOptions.value)
  window.open(url, '_blank')
}
</script>

<style scoped>
.batch-operations {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tabs {
  display: flex;
  border-bottom: 1px solid var(--color-border);
}

.tab {
  padding: 12px 24px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text-light);
  transition: all 0.2s;
}

.tab:hover {
  color: var(--color-text);
}

.tab.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.tab-content {
  padding: 16px 0;
}

.import-section,
.export-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.template-download {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: var(--color-background-soft);
  border-radius: 8px;
}

.template-download p {
  margin: 0;
  font-size: 14px;
  color: var(--color-text-light);
}

.upload-area {
  border: 2px dashed var(--color-border);
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover,
.upload-area.dragover {
  border-color: var(--color-primary);
  background: rgba(var(--color-primary-rgb), 0.05);
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 48px;
}

.upload-placeholder p {
  margin: 0;
  color: var(--color-text);
}

.upload-hint {
  font-size: 12px;
  color: var(--color-text-light) !important;
}

.selected-file {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.file-icon {
  font-size: 24px;
}

.file-name {
  font-weight: 500;
}

.import-options {
  padding: 12px 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.validation-result,
.import-result {
  padding: 16px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  margin-bottom: 12px;
}

.result-header.success {
  color: #2e7d32;
}

.result-header.error {
  color: #c62828;
}

.result-header.warning {
  color: #f57c00;
}

.result-icon {
  font-size: 18px;
}

.result-stats {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--color-text-light);
}

.error-count {
  color: #c62828;
}

.error-list {
  margin-top: 12px;
  padding: 12px;
  background: #ffebee;
  border-radius: 4px;
}

.error-item {
  font-size: 12px;
  color: #c62828;
  margin-bottom: 4px;
}

.more-errors {
  font-size: 12px;
  color: #c62828;
  font-style: italic;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.export-options {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.option-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.option-group.checkbox {
  justify-content: flex-end;
}

.option-label {
  font-size: 12px;
  color: var(--color-text-light);
}

.option-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-background);
  min-width: 120px;
}

.export-preview {
  padding: 16px;
  background: var(--color-background-soft);
  border-radius: 8px;
}

.preview-count {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}
</style>
