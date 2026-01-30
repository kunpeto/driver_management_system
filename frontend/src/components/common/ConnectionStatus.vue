<template>
  <div class="connection-status" :class="overallStatusClass">
    <!-- 折疊顯示模式 -->
    <div
      class="status-summary"
      @click="expanded = !expanded"
      :title="statusTooltip"
    >
      <span class="status-indicator" :class="overallStatusClass"></span>
      <span class="status-text">{{ summaryText }}</span>
      <span class="expand-icon">{{ expanded ? '▼' : '▶' }}</span>
    </div>

    <!-- 展開詳情 -->
    <div v-if="expanded" class="status-details">
      <!-- 雲端 API 狀態 -->
      <div class="status-item">
        <span class="item-icon" :class="cloudStatusClass">●</span>
        <span class="item-label">雲端 API</span>
        <span class="item-status">{{ cloudStatus.message || cloudStatus.status }}</span>
        <span v-if="cloudStatus.response_time_ms" class="item-latency">
          {{ Math.round(cloudStatus.response_time_ms) }}ms
        </span>
      </div>

      <!-- 本機 API 狀態 -->
      <div class="status-item">
        <span class="item-icon" :class="localStatusClass">●</span>
        <span class="item-label">本機 API</span>
        <span class="item-status">{{ localStatus.message || localStatus.status }}</span>
      </div>

      <!-- Google API 狀態（可選展開） -->
      <div class="google-section" v-if="showGoogleStatus">
        <div class="section-header" @click="googleExpanded = !googleExpanded">
          <span class="item-icon" :class="googleOverallClass">●</span>
          <span class="item-label">Google API</span>
          <span class="expand-icon small">{{ googleExpanded ? '▼' : '▶' }}</span>
        </div>

        <div v-if="googleExpanded" class="google-details">
          <!-- 淡海 -->
          <div class="dept-status">
            <span class="dept-label">淡海</span>
            <div class="dept-services">
              <span class="service" :class="googleStatus.danhai_sheets?.status">
                Sheets: {{ googleStatus.danhai_sheets?.status || '未知' }}
              </span>
              <span class="service" :class="googleStatus.danhai_drive?.status">
                Drive: {{ googleStatus.danhai_drive?.status || '未知' }}
              </span>
            </div>
          </div>

          <!-- 安坑 -->
          <div class="dept-status">
            <span class="dept-label">安坑</span>
            <div class="dept-services">
              <span class="service" :class="googleStatus.ankeng_sheets?.status">
                Sheets: {{ googleStatus.ankeng_sheets?.status || '未知' }}
              </span>
              <span class="service" :class="googleStatus.ankeng_drive?.status">
                Drive: {{ googleStatus.ankeng_drive?.status || '未知' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- 操作按鈕 -->
      <div class="status-actions">
        <button class="refresh-btn" @click.stop="refresh" :disabled="loading">
          {{ loading ? '檢查中...' : '重新檢查' }}
        </button>
        <span class="last-check" v-if="lastCheck">
          上次檢查: {{ formatTime(lastCheck) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import api from '@/utils/api'

// Props
const props = defineProps({
  autoRefresh: {
    type: Boolean,
    default: true
  },
  refreshInterval: {
    type: Number,
    default: 60000 // 1 分鐘
  },
  showGoogleStatus: {
    type: Boolean,
    default: true
  },
  compact: {
    type: Boolean,
    default: false
  }
})

// State
const expanded = ref(!props.compact)
const googleExpanded = ref(false)
const loading = ref(false)
const lastCheck = ref(null)

const cloudStatus = ref({
  status: 'unknown',
  message: '尚未檢查'
})

const localStatus = ref({
  status: 'unknown',
  message: '尚未檢查'
})

const googleStatus = ref({
  overall_status: 'unknown',
  danhai_sheets: null,
  danhai_drive: null,
  ankeng_sheets: null,
  ankeng_drive: null
})

let refreshTimer = null

// Computed
const overallStatusClass = computed(() => {
  if (cloudStatus.value.status === 'connected') {
    return 'healthy'
  } else if (cloudStatus.value.status === 'error') {
    return 'unhealthy'
  } else {
    return 'unknown'
  }
})

const cloudStatusClass = computed(() => {
  return getStatusClass(cloudStatus.value.status)
})

const localStatusClass = computed(() => {
  return getStatusClass(localStatus.value.status)
})

const googleOverallClass = computed(() => {
  return getStatusClass(googleStatus.value.overall_status)
})

const summaryText = computed(() => {
  if (loading.value) return '檢查中...'

  const cloud = cloudStatus.value.status === 'connected' ? '正常' : '異常'
  return `連線狀態: ${cloud}`
})

const statusTooltip = computed(() => {
  return `雲端: ${cloudStatus.value.status}\n本機: ${localStatus.value.status}\nGoogle: ${googleStatus.value.overall_status}`
})

// Methods
function getStatusClass(status) {
  switch (status) {
    case 'connected':
      return 'connected'
    case 'disconnected':
    case 'error':
      return 'error'
    case 'not_configured':
      return 'warning'
    default:
      return 'unknown'
  }
}

function formatTime(date) {
  if (!date) return ''
  return new Date(date).toLocaleTimeString('zh-TW', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

async function checkCloudStatus() {
  try {
    const response = await api.get('/api/status/cloud')
    cloudStatus.value = {
      status: response.data.database?.status || 'unknown',
      message: response.data.database?.message || '已連線'
    }
  } catch (err) {
    cloudStatus.value = {
      status: 'error',
      message: err.response?.data?.detail || err.message || '無法連線'
    }
  }
}

async function checkLocalStatus() {
  try {
    // 從環境變數讀取本機 API URL（Gemini Review Fix: 移除硬編碼）
    const localApi = import.meta.env.VITE_LOCAL_API_URL || 'http://127.0.0.1:8001'
    const response = await fetch(`${localApi}/health`, {
      method: 'GET',
      mode: 'cors'
    })

    if (response.ok) {
      localStatus.value = {
        status: 'connected',
        message: '本機 API 運行中'
      }
    } else {
      localStatus.value = {
        status: 'error',
        message: `HTTP ${response.status}`
      }
    }
  } catch (err) {
    localStatus.value = {
      status: 'disconnected',
      message: '本機 API 未啟動'
    }
  }
}

async function checkGoogleStatus() {
  if (!props.showGoogleStatus) return

  try {
    const response = await api.get('/api/status/google')
    googleStatus.value = {
      overall_status: response.data.overall_status,
      danhai_sheets: response.data.danhai_sheets,
      danhai_drive: response.data.danhai_drive,
      ankeng_sheets: response.data.ankeng_sheets,
      ankeng_drive: response.data.ankeng_drive
    }
  } catch (err) {
    // Google 狀態需要登入，如果失敗可能是未登入
    googleStatus.value = {
      overall_status: 'unknown',
      danhai_sheets: null,
      danhai_drive: null,
      ankeng_sheets: null,
      ankeng_drive: null
    }
  }
}

async function refresh() {
  loading.value = true

  try {
    // 並行檢查
    await Promise.all([
      checkCloudStatus(),
      checkLocalStatus(),
      checkGoogleStatus()
    ])

    lastCheck.value = new Date()
  } finally {
    loading.value = false
  }
}

function startAutoRefresh() {
  if (props.autoRefresh && props.refreshInterval > 0) {
    refreshTimer = setInterval(refresh, props.refreshInterval)
  }
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

// Lifecycle
onMounted(() => {
  refresh()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})

// Expose
defineExpose({
  refresh
})
</script>

<style scoped>
.connection-status {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  font-size: 13px;
}

.connection-status.healthy {
  border-color: #4caf50;
}

.connection-status.unhealthy {
  border-color: #f44336;
}

.status-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
  transition: background-color 0.2s;
}

.status-summary:hover {
  background: var(--color-background-soft);
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #9e9e9e;
}

.status-indicator.healthy {
  background: #4caf50;
}

.status-indicator.unhealthy {
  background: #f44336;
}

.status-text {
  flex: 1;
  font-weight: 500;
}

.expand-icon {
  font-size: 10px;
  color: var(--color-text-light);
}

.expand-icon.small {
  font-size: 8px;
}

.status-details {
  padding: 12px 14px;
  border-top: 1px solid var(--color-border);
  background: var(--color-background-soft);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
}

.item-icon {
  font-size: 8px;
}

.item-icon.connected {
  color: #4caf50;
}

.item-icon.error {
  color: #f44336;
}

.item-icon.warning {
  color: #ff9800;
}

.item-icon.unknown {
  color: #9e9e9e;
}

.item-label {
  width: 80px;
  color: var(--color-text-light);
}

.item-status {
  flex: 1;
}

.item-latency {
  font-size: 11px;
  color: var(--color-text-light);
  background: var(--color-background);
  padding: 2px 6px;
  border-radius: 4px;
}

.google-section {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--color-border);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 0;
}

.section-header:hover {
  opacity: 0.8;
}

.google-details {
  margin-top: 8px;
  padding-left: 16px;
}

.dept-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}

.dept-label {
  width: 40px;
  font-size: 12px;
  color: var(--color-text-light);
}

.dept-services {
  display: flex;
  gap: 12px;
}

.service {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 4px;
  background: var(--color-background);
}

.service.connected {
  color: #4caf50;
}

.service.error {
  color: #f44336;
}

.service.not_configured {
  color: #ff9800;
}

.status-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.refresh-btn {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-background);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.last-check {
  font-size: 11px;
  color: var(--color-text-light);
}
</style>
