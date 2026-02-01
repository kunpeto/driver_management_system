<template>
  <div class="pdf-upload-page">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>PDF 上傳處理</h1>
      <p class="subtitle">上傳 PDF 檔案，系統會自動識別條碼、切分檔案並上傳到 Google Drive</p>
    </div>

    <!-- 本機 API 狀態 -->
    <el-alert
      v-if="!localApiConnected"
      title="本機 API 未連線"
      type="warning"
      description="PDF 處理功能需要本機桌面應用程式支援。請確認應用程式已啟動。"
      show-icon
      :closable="false"
      class="connection-alert"
    />

    <!-- 上傳區域 -->
    <el-card v-if="localApiConnected" class="upload-card">
      <template #header>
        <div class="card-header">
          <span>選擇 PDF 檔案</span>
        </div>
      </template>

      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        :action="uploadUrl"
        :before-upload="beforeUpload"
        :on-success="handleSuccess"
        :on-error="handleError"
        :on-progress="handleProgress"
        :disabled="uploading"
        accept=".pdf"
        :show-file-list="false"
      >
        <template v-if="!uploading">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            將 PDF 檔案拖曳至此，或<em>點擊上傳</em>
          </div>
          <div class="el-upload__tip">
            僅支援 PDF 格式，檔案大小限制 50MB
          </div>
        </template>
        <template v-else>
          <el-progress
            :percentage="uploadProgress"
            :stroke-width="12"
            style="width: 80%"
          />
          <div class="upload-status">{{ uploadStatus }}</div>
        </template>
      </el-upload>

      <!-- 處理選項 -->
      <div class="process-options">
        <el-checkbox v-model="uploadToDrive">
          自動上傳到 Google Drive
        </el-checkbox>
      </div>
    </el-card>

    <!-- 處理結果 -->
    <el-card v-if="processResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>處理結果</span>
          <el-tag :type="processResult.success ? 'success' : 'danger'">
            {{ processResult.success ? '成功' : '失敗' }}
          </el-tag>
        </div>
      </template>

      <!-- 統計資訊 -->
      <div class="result-stats">
        <div class="stat-item">
          <span class="stat-label">原始檔案</span>
          <span class="stat-value">{{ processResult.file_name }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">總頁數</span>
          <span class="stat-value">{{ processResult.total_pages }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">識別條碼</span>
          <span class="stat-value">{{ processResult.barcodes_found }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">切分檔案</span>
          <span class="stat-value">{{ processResult.files_created }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">已上傳</span>
          <span class="stat-value">{{ processResult.files_uploaded }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">處理時間</span>
          <span class="stat-value">{{ processResult.processing_time_ms }}ms</span>
        </div>
      </div>

      <!-- 錯誤訊息 -->
      <el-alert
        v-if="processResult.error_message"
        :title="processResult.error_message"
        type="error"
        show-icon
        :closable="false"
        class="error-alert"
      />

      <!-- 切分檔案列表 -->
      <div v-if="processResult.split_files?.length" class="split-files">
        <h4>切分檔案列表</h4>
        <el-table :data="processResult.split_files" stripe>
          <el-table-column prop="file_name" label="檔案名稱" min-width="200" />
          <el-table-column prop="barcode_data" label="條碼" width="150" />
          <el-table-column prop="department" label="部門" width="80">
            <template #default="{ row }">
              <el-tag v-if="row.department" size="small">
                {{ row.department }}
              </el-tag>
              <span v-else class="text-muted">未知</span>
            </template>
          </el-table-column>
          <el-table-column label="頁碼範圍" width="100">
            <template #default="{ row }">
              {{ row.start_page }} - {{ row.end_page }}
            </template>
          </el-table-column>
          <el-table-column prop="page_count" label="頁數" width="60" />
          <el-table-column label="Drive 連結" width="100">
            <template #default="{ row }">
              <el-link
                v-if="row.drive_link"
                :href="row.drive_link"
                target="_blank"
                type="primary"
              >
                開啟
              </el-link>
              <span v-else class="text-muted">-</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>

    <!-- 掃描結果（僅掃描模式） -->
    <el-card v-if="scanResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>條碼掃描結果</span>
          <el-button size="small" @click="scanResult = null">清除</el-button>
        </div>
      </template>

      <div class="scan-info">
        <p>檔案: {{ scanResult.file_name }}</p>
        <p>總頁數: {{ scanResult.total_pages }}</p>
        <p>找到條碼: {{ scanResult.barcodes.length }}</p>
      </div>

      <el-table v-if="scanResult.barcodes.length" :data="scanResult.barcodes" stripe>
        <el-table-column prop="page_number" label="頁碼" width="80" />
        <el-table-column prop="barcode_type" label="類型" width="100" />
        <el-table-column prop="barcode_data" label="內容" />
        <el-table-column prop="department" label="部門" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.department" size="small">{{ row.department }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 操作按鈕 -->
    <div v-if="localApiConnected" class="action-buttons">
      <el-button @click="scanOnly">
        僅掃描條碼
      </el-button>
      <el-button type="primary" @click="triggerUpload">
        上傳並處理
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '@/utils/api'

// 本機 API 基礎 URL（從環境變數讀取）
const LOCAL_API_BASE = import.meta.env.VITE_LOCAL_API_URL || 'http://localhost:8001'

// 狀態
const localApiConnected = ref(false)
const uploading = ref(false)
const uploadProgress = ref(0)
const uploadStatus = ref('')
const uploadToDrive = ref(true)
const processResult = ref(null)
const scanResult = ref(null)
const uploadRef = ref(null)
const selectedFile = ref(null)

// 計算屬性
const uploadUrl = computed(() => {
  const endpoint = uploadToDrive.value ? '/api/pdf/process' : '/api/pdf/split'
  return `${LOCAL_API_BASE}${endpoint}`
})

// 檢查本機 API 連線
const checkLocalApi = async () => {
  try {
    const response = await fetch(`${LOCAL_API_BASE}/health`, {
      method: 'GET',
      mode: 'cors'
    })
    localApiConnected.value = response.ok
  } catch (error) {
    localApiConnected.value = false
    console.warn('本機 API 未連線:', error)
  }
}

// 上傳前驗證
const beforeUpload = (file) => {
  const isPdf = file.type === 'application/pdf'
  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isPdf) {
    ElMessage.error('只能上傳 PDF 檔案！')
    return false
  }

  if (!isLt50M) {
    ElMessage.error('檔案大小不能超過 50MB！')
    return false
  }

  selectedFile.value = file
  uploading.value = true
  uploadProgress.value = 0
  uploadStatus.value = '上傳中...'
  processResult.value = null
  scanResult.value = null

  return true
}

// 上傳進度
const handleProgress = (event) => {
  uploadProgress.value = Math.round(event.percent)
  if (uploadProgress.value >= 100) {
    uploadStatus.value = '處理中...'
  }
}

// 上傳成功
const handleSuccess = (response) => {
  uploading.value = false
  uploadProgress.value = 100
  uploadStatus.value = '完成'

  if (response.success) {
    ElMessage.success('PDF 處理完成！')
    processResult.value = response
  } else {
    ElMessage.warning(response.error_message || '處理失敗')
    processResult.value = response
  }
}

// 上傳失敗
const handleError = (error) => {
  uploading.value = false
  uploadProgress.value = 0
  uploadStatus.value = ''
  ElMessage.error('上傳失敗: ' + (error.message || '未知錯誤'))
}

// 僅掃描條碼
const scanOnly = async () => {
  if (!selectedFile.value) {
    // 觸發檔案選擇
    uploadRef.value?.$el.querySelector('input')?.click()
    return
  }

  uploading.value = true
  uploadStatus.value = '掃描中...'

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const response = await fetch(`${LOCAL_API_BASE}/api/pdf/scan`, {
      method: 'POST',
      body: formData,
      mode: 'cors'
    })

    const data = await response.json()
    scanResult.value = data
    processResult.value = null

    if (data.success) {
      ElMessage.success(`找到 ${data.barcodes.length} 個條碼`)
    } else {
      ElMessage.warning(data.error_message || '掃描失敗')
    }
  } catch (error) {
    ElMessage.error('掃描失敗: ' + error.message)
  } finally {
    uploading.value = false
    uploadStatus.value = ''
  }
}

// 觸發上傳
const triggerUpload = () => {
  uploadRef.value?.$el.querySelector('input')?.click()
}

// 頁面載入
onMounted(() => {
  checkLocalApi()
  // 定期檢查本機 API 狀態
  setInterval(checkLocalApi, 30000)
})
</script>

<style scoped>
.pdf-upload-page {
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.subtitle {
  margin: 0;
  color: #909399;
}

.connection-alert {
  margin-bottom: 20px;
}

.upload-card,
.result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px 20px;
}

.upload-status {
  margin-top: 10px;
  color: #909399;
}

.process-options {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 16px;
  font-weight: 500;
}

.error-alert {
  margin-bottom: 20px;
}

.split-files h4 {
  margin: 0 0 12px 0;
}

.scan-info {
  margin-bottom: 16px;
}

.scan-info p {
  margin: 4px 0;
}

.text-muted {
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 20px;
}
</style>
