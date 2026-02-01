<template>
  <div class="drive-authorization">
    <!-- 授權狀態卡片 -->
    <el-card class="auth-card" :class="{ authorized: isAuthorized }">
      <template #header>
        <div class="card-header">
          <span>{{ department }} - Google Drive 授權</span>
          <el-tag :type="isAuthorized ? 'success' : 'info'" size="small">
            {{ isAuthorized ? '已授權' : '未授權' }}
          </el-tag>
        </div>
      </template>

      <!-- 授權資訊 -->
      <div v-if="isAuthorized" class="auth-info">
        <div class="info-item">
          <el-icon><User /></el-icon>
          <span>授權帳號：{{ authStatus?.authorized_email || '未知' }}</span>
        </div>
        <div class="info-item">
          <el-icon><Clock /></el-icon>
          <span>
            Token 狀態：
            <el-tag :type="authStatus?.access_token_valid ? 'success' : 'warning'" size="small">
              {{ authStatus?.access_token_valid ? '有效' : '需刷新' }}
            </el-tag>
          </span>
        </div>
        <div v-if="authStatus?.expires_at" class="info-item">
          <el-icon><Timer /></el-icon>
          <span>到期時間：{{ formatDate(authStatus.expires_at) }}</span>
        </div>
      </div>

      <!-- 未授權提示 -->
      <div v-else class="no-auth">
        <el-icon :size="32" color="#909399"><Warning /></el-icon>
        <p>尚未完成 Google Drive 授權</p>
        <p class="hint">授權後才能上傳 PDF 檔案到 Google Drive</p>
      </div>

      <!-- 操作按鈕 -->
      <div class="auth-actions">
        <el-button
          v-if="!isAuthorized"
          type="primary"
          :loading="authorizing"
          @click="startAuth"
        >
          <el-icon><Connection /></el-icon>
          開始授權
        </el-button>

        <template v-else>
          <el-button :loading="refreshing" @click="refreshToken">
            <el-icon><Refresh /></el-icon>
            刷新 Token
          </el-button>
          <el-button type="danger" plain @click="confirmRevoke">
            <el-icon><Delete /></el-icon>
            撤銷授權
          </el-button>
        </template>
      </div>
    </el-card>

    <!-- 授權說明對話框 -->
    <el-dialog
      v-model="showAuthDialog"
      title="Google Drive 授權說明"
      width="500px"
    >
      <div class="auth-instructions">
        <el-steps :active="authStep" finish-status="success" direction="vertical">
          <el-step title="開始授權" description="點擊下方按鈕開始授權流程" />
          <el-step title="登入 Google" description="在彈出視窗中登入您的 Google 帳號" />
          <el-step title="同意授權" description="同意允許本系統存取 Google Drive" />
          <el-step title="完成" description="授權成功後視窗會自動關閉" />
        </el-steps>

        <el-alert
          type="info"
          show-icon
          :closable="false"
          class="auth-note"
        >
          <template #title>
            注意事項
          </template>
          <template #default>
            <ul>
              <li>授權帳號需要有目標 Google Drive 資料夾的存取權限</li>
              <li>授權僅用於上傳檔案，不會存取其他資料</li>
              <li>您可以隨時在這裡撤銷授權</li>
            </ul>
          </template>
        </el-alert>
      </div>

      <template #footer>
        <el-button @click="showAuthDialog = false">取消</el-button>
        <el-button type="primary" :loading="authorizing" @click="openAuthWindow">
          開啟授權頁面
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Clock,
  Timer,
  Warning,
  Connection,
  Refresh,
  Delete
} from '@element-plus/icons-vue'
import api from '@/utils/api'

// Props
const props = defineProps({
  department: {
    type: String,
    required: true,
    validator: (val) => ['淡海', '安坑'].includes(val)
  }
})

// Emits
const emit = defineEmits(['authorized', 'revoked', 'refreshed'])

// 狀態
const authStatus = ref(null)
const authorizing = ref(false)
const refreshing = ref(false)
const showAuthDialog = ref(false)
const authStep = ref(0)
const authWindow = ref(null)

// 計算屬性
const isAuthorized = computed(() => authStatus.value?.is_authorized ?? false)

// 取得授權狀態
const fetchAuthStatus = async () => {
  try {
    const response = await api.get('/api/google/oauth-status')
    const statuses = response.data
    authStatus.value = statuses.find(s => s.department === props.department)
  } catch (error) {
    console.error('取得授權狀態失敗:', error)
  }
}

// 開始授權流程
const startAuth = () => {
  authStep.value = 0
  showAuthDialog.value = true
}

// 開啟授權視窗
const openAuthWindow = async () => {
  authorizing.value = true
  authStep.value = 1

  try {
    // 取得授權 URL
    const response = await api.get('/api/google/auth-url', {
      params: { department: props.department }
    })

    const { auth_url } = response.data

    // 開啟彈出視窗
    const width = 600
    const height = 700
    const left = (window.screen.width - width) / 2
    const top = (window.screen.height - height) / 2

    authWindow.value = window.open(
      auth_url,
      'google_auth',
      `width=${width},height=${height},left=${left},top=${top},scrollbars=yes`
    )

    // 監聽視窗關閉
    const checkInterval = setInterval(() => {
      if (authWindow.value?.closed) {
        clearInterval(checkInterval)
        handleAuthWindowClosed()
      }
    }, 500)

  } catch (error) {
    ElMessage.error('取得授權 URL 失敗: ' + (error.response?.data?.detail || error.message))
    authorizing.value = false
  }
}

// 處理授權視窗關閉
const handleAuthWindowClosed = async () => {
  authorizing.value = false
  showAuthDialog.value = false

  // 重新取得狀態
  await fetchAuthStatus()

  if (isAuthorized.value) {
    ElMessage.success(`${props.department} Google Drive 授權成功！`)
    emit('authorized', props.department)
  } else {
    ElMessage.warning('授權流程未完成')
  }
}

// 刷新 Token
const refreshToken = async () => {
  refreshing.value = true

  try {
    const response = await api.post('/api/google/get-access-token', null, {
      params: { department: props.department }
    })

    if (response.data.success) {
      ElMessage.success('Token 刷新成功')
      await fetchAuthStatus()
      emit('refreshed', props.department)
    } else {
      ElMessage.error(response.data.error_message || 'Token 刷新失敗')
    }
  } catch (error) {
    ElMessage.error('Token 刷新失敗: ' + (error.response?.data?.detail || error.message))
  } finally {
    refreshing.value = false
  }
}

// 確認撤銷授權
const confirmRevoke = () => {
  ElMessageBox.confirm(
    `確定要撤銷 ${props.department} 的 Google Drive 授權嗎？撤銷後將無法上傳檔案到該部門的 Google Drive。`,
    '撤銷授權',
    {
      confirmButtonText: '確定撤銷',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(() => {
    revokeAuth()
  }).catch(() => {
    // 取消
  })
}

// 撤銷授權
const revokeAuth = async () => {
  try {
    const response = await api.delete('/api/google/revoke', {
      params: { department: props.department }
    })

    if (response.data.success) {
      ElMessage.success('授權已撤銷')
      await fetchAuthStatus()
      emit('revoked', props.department)
    } else {
      ElMessage.error(response.data.message || '撤銷失敗')
    }
  } catch (error) {
    ElMessage.error('撤銷授權失敗: ' + (error.response?.data?.detail || error.message))
  }
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-TW', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 監聽 department 變化
watch(() => props.department, () => {
  fetchAuthStatus()
})

// 頁面載入
onMounted(() => {
  fetchAuthStatus()
})

// 暴露方法
defineExpose({
  fetchAuthStatus
})
</script>

<style scoped>
.drive-authorization {
  width: 100%;
}

.auth-card {
  transition: border-color 0.3s;
}

.auth-card.authorized {
  border-color: #67c23a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.auth-info {
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  color: #606266;
}

.info-item .el-icon {
  color: #909399;
}

.no-auth {
  text-align: center;
  padding: 20px 0;
}

.no-auth p {
  margin: 8px 0 0 0;
  color: #606266;
}

.no-auth .hint {
  font-size: 12px;
  color: #909399;
}

.auth-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.auth-instructions {
  padding: 0 20px;
}

.auth-note {
  margin-top: 20px;
}

.auth-note ul {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.auth-note li {
  margin-bottom: 4px;
}
</style>
