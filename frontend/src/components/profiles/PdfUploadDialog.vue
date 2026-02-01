<template>
  <el-dialog
    v-model="dialogVisible"
    title="上傳 PDF 到 Google Drive"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <!-- 履歷資訊 -->
    <div v-if="uploadParams" class="profile-info">
      <el-descriptions :column="2" border size="small">
        <el-descriptions-item label="員工">
          {{ uploadParams.employee_name }} ({{ uploadParams.employee_id }})
        </el-descriptions-item>
        <el-descriptions-item label="類型">
          <el-tag :type="getTypeColor(uploadParams.profile_type)" size="small">
            {{ getTypeLabel(uploadParams.profile_type) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="事件日期">
          {{ uploadParams.event_date || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="部門">
          {{ uploadParams.department }}
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 檔案選擇 -->
    <div class="upload-section">
      <el-upload
        ref="uploadRef"
        class="pdf-uploader"
        drag
        :auto-upload="false"
        :limit="1"
        accept=".pdf"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
      >
        <el-icon class="el-icon--upload" :size="48"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖曳 PDF 檔案到此處，或 <em>點擊選擇</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            僅支援 PDF 格式，檔案大小限制 50MB
          </div>
        </template>
      </el-upload>
    </div>

    <!-- 上傳資訊 -->
    <div v-if="selectedFile" class="file-info">
      <el-icon><Document /></el-icon>
      <span class="file-name">{{ selectedFile.name }}</span>
      <span class="file-size">({{ formatFileSize(selectedFile.size) }})</span>
    </div>

    <!-- 建議資訊 -->
    <div v-if="uploadParams" class="suggested-info">
      <p><strong>建議檔案名稱：</strong>{{ uploadParams.suggested_file_name }}</p>
      <p><strong>目標資料夾：</strong>{{ uploadParams.suggested_folder_name }}</p>
    </div>

    <!-- 上傳進度 -->
    <div v-if="uploading" class="progress-section">
      <el-progress :percentage="uploadProgress" :status="progressStatus" />
      <p class="progress-text">{{ progressText }}</p>
    </div>

    <!-- 錯誤訊息 -->
    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      show-icon
      closable
      @close="errorMessage = ''"
    />

    <!-- 成功訊息 -->
    <el-alert
      v-if="uploadResult"
      title="上傳成功"
      type="success"
      show-icon
      :closable="false"
    >
      <template #default>
        <p>檔案已上傳到 Google Drive</p>
        <el-link
          type="primary"
          :href="uploadResult.web_view_link"
          target="_blank"
        >
          點擊查看檔案
        </el-link>
      </template>
    </el-alert>

    <template #footer>
      <span class="dialog-footer">
        <el-button :disabled="uploading" @click="handleClose">取消</el-button>
        <el-button
          type="primary"
          :disabled="!canUpload"
          :loading="uploading"
          @click="handleUpload"
        >
          {{ uploading ? '上傳中...' : '上傳' }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * PDF 上傳對話框
 * Phase 14 T194
 */
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Document } from '@element-plus/icons-vue'
import { useProfilesStore } from '@/stores/profiles'
import { localApi } from '@/utils/api'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  profileId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'uploaded'])

const profilesStore = useProfilesStore()

// 狀態
const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const uploadRef = ref(null)
const selectedFile = ref(null)
const uploadParams = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const progressText = ref('')
const errorMessage = ref('')
const uploadResult = ref(null)

// 履歷類型設定
const PROFILE_TYPES = {
  event_investigation: { label: '事件調查', color: 'danger' },
  personnel_interview: { label: '人員訪談', color: 'warning' },
  corrective_measures: { label: '矯正措施', color: 'success' },
  assessment_notice: { label: '考核通知', color: 'primary' },
  basic: { label: '基本', color: 'info' }
}

// 計算屬性
const canUpload = computed(() => {
  return selectedFile.value &&
    uploadParams.value?.can_upload &&
    !uploading.value &&
    !uploadResult.value
})

const progressStatus = computed(() => {
  if (uploadResult.value) return 'success'
  if (errorMessage.value) return 'exception'
  return ''
})

// 監聽 profileId 變化
watch(() => props.profileId, async (newId) => {
  if (newId) {
    await loadUploadParams()
  }
}, { immediate: true })

// 監聽對話框開啟
watch(dialogVisible, (visible) => {
  if (visible && props.profileId) {
    loadUploadParams()
  } else if (!visible) {
    resetState()
  }
})

// 載入上傳參數
async function loadUploadParams() {
  if (!props.profileId) return

  try {
    uploadParams.value = await profilesStore.fetchUploadParams(props.profileId)

    if (!uploadParams.value.can_upload) {
      errorMessage.value = uploadParams.value.error_message || '此履歷無法上傳'
    }
  } catch (err) {
    errorMessage.value = '載入上傳參數失敗'
    console.error(err)
  }
}

// 檔案選擇處理
function handleFileChange(file) {
  if (file.raw.type !== 'application/pdf') {
    ElMessage.warning('請選擇 PDF 檔案')
    uploadRef.value?.clearFiles()
    return
  }

  if (file.raw.size > 50 * 1024 * 1024) {
    ElMessage.warning('檔案大小不能超過 50MB')
    uploadRef.value?.clearFiles()
    return
  }

  selectedFile.value = file.raw
}

// 超出數量限制
function handleExceed() {
  ElMessage.warning('只能上傳一個檔案')
}

// 執行上傳
async function handleUpload() {
  if (!canUpload.value) return

  uploading.value = true
  uploadProgress.value = 0
  progressText.value = '準備上傳...'
  errorMessage.value = ''

  // Gemini Review P2：記錄上傳結果以區分錯誤類型
  let driveUploadSuccess = false
  let driveLink = null

  try {
    // 準備表單資料
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('profile_type', uploadParams.value.profile_type)
    formData.append('year_month', getYearMonth(uploadParams.value.event_date))
    formData.append('department', uploadParams.value.department)
    formData.append('file_name', uploadParams.value.suggested_file_name)
    // Gemini Review P1：傳遞後端提供的 folder_path，確保路徑一致
    formData.append('folder_path', uploadParams.value.suggested_folder_name)
    formData.append('set_domain_permission', 'true')

    // 上傳到本機 API
    uploadProgress.value = 20
    progressText.value = '上傳到 Google Drive...'

    const response = await localApi.post('/api/pdf/upload-profile', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        const progress = Math.round((progressEvent.loaded / progressEvent.total) * 60)
        uploadProgress.value = 20 + progress
      }
    })

    if (!response.data.success) {
      throw new Error(response.data.error_message || '上傳失敗')
    }

    // 記錄上傳成功（Gemini Review P2）
    driveUploadSuccess = true
    driveLink = response.data.web_view_link

    uploadProgress.value = 85
    progressText.value = '更新履歷狀態...'

    // 更新後端履歷狀態
    await profilesStore.markComplete(
      props.profileId,
      response.data.web_view_link
    )

    uploadProgress.value = 100
    progressText.value = '完成'
    uploadResult.value = response.data

    ElMessage.success('PDF 上傳成功')
    emit('uploaded', {
      profileId: props.profileId,
      gdriveLink: response.data.web_view_link
    })

  } catch (err) {
    console.error('上傳失敗:', err)

    // Gemini Review P2：區分「上傳失敗」與「狀態更新失敗」
    if (driveUploadSuccess && driveLink) {
      // 檔案已上傳到 Drive，但狀態更新失敗
      errorMessage.value = `檔案已上傳到 Google Drive，但系統狀態更新失敗。請聯繫管理員手動更新，或複製連結後重試。連結：${driveLink}`
      // 仍然顯示部分成功的結果
      uploadResult.value = { web_view_link: driveLink, partial_success: true }
      uploadProgress.value = 85
    } else {
      // 上傳本身失敗
      errorMessage.value = err.response?.data?.detail || err.message || '上傳失敗'
      uploadProgress.value = 0
    }
  } finally {
    uploading.value = false
  }
}

// 取得年月
function getYearMonth(dateStr) {
  if (!dateStr) {
    const now = new Date()
    return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}`
  }
  return dateStr.replace(/-/g, '').substring(0, 6)
}

// 格式化檔案大小
function formatFileSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 取得類型標籤
function getTypeLabel(type) {
  return PROFILE_TYPES[type]?.label || type
}

// 取得類型顏色
function getTypeColor(type) {
  return PROFILE_TYPES[type]?.color || 'info'
}

// 關閉對話框
function handleClose() {
  dialogVisible.value = false
}

// 重置狀態
function resetState() {
  selectedFile.value = null
  uploadParams.value = null
  uploading.value = false
  uploadProgress.value = 0
  progressText.value = ''
  errorMessage.value = ''
  uploadResult.value = null
  uploadRef.value?.clearFiles()
}
</script>

<style scoped>
.profile-info {
  margin-bottom: 20px;
}

.upload-section {
  margin-bottom: 16px;
}

.pdf-uploader {
  width: 100%;
}

.pdf-uploader :deep(.el-upload-dragger) {
  width: 100%;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-bottom: 16px;
}

.file-name {
  font-weight: 500;
  color: #303133;
}

.file-size {
  color: #909399;
  font-size: 13px;
}

.suggested-info {
  padding: 12px;
  background: #ecf5ff;
  border-radius: 4px;
  margin-bottom: 16px;
  font-size: 13px;
}

.suggested-info p {
  margin: 4px 0;
  color: #409eff;
}

.progress-section {
  margin-bottom: 16px;
}

.progress-text {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}

.el-alert {
  margin-bottom: 16px;
}
</style>
