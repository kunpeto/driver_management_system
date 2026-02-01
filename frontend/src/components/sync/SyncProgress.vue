<template>
  <div class="sync-progress">
    <div class="progress-header">
      <span class="progress-title">同步進度</span>
      <span :class="['status-badge', status]">{{ statusText }}</span>
    </div>

    <div class="progress-bar-container">
      <div
        class="progress-bar"
        :style="{ width: `${progress}%` }"
        :class="status"
      ></div>
    </div>

    <div class="progress-details">
      <div class="detail-item">
        <span class="label">進度:</span>
        <span class="value">{{ progress.toFixed(1) }}%</span>
      </div>
      <div v-if="taskData" class="detail-item">
        <span class="label">處理:</span>
        <span class="value">
          {{ (taskData.success_count || 0) + (taskData.error_count || 0) }}
          / {{ taskData.total_rows || 0 }}
        </span>
      </div>
      <div v-if="taskData?.success_count" class="detail-item">
        <span class="label">成功:</span>
        <span class="value success">{{ taskData.success_count }}</span>
      </div>
      <div v-if="taskData?.error_count" class="detail-item">
        <span class="label">錯誤:</span>
        <span class="value error">{{ taskData.error_count }}</span>
      </div>
    </div>

    <div v-if="status === 'running'" class="progress-actions">
      <button class="btn btn-secondary" :disabled="cancelling" @click="cancel">
        {{ cancelling ? '取消中...' : '取消' }}
      </button>
    </div>

    <div v-if="taskData?.error_details?.length > 0" class="error-list">
      <h4>錯誤詳情</h4>
      <ul>
        <li v-for="(error, idx) in taskData.error_details.slice(0, 5)" :key="idx">
          {{ error }}
        </li>
        <li v-if="taskData.error_details.length > 5">
          ...還有 {{ taskData.error_details.length - 5 }} 個錯誤
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import api from '@/utils/api'

const props = defineProps({
  taskId: {
    type: String,
    required: true
  },
  pollInterval: {
    type: Number,
    default: 2000
  }
})

const emit = defineEmits(['complete', 'error'])

// 狀態
const taskData = ref(null)
const status = ref('pending')
const progress = ref(0)
const cancelling = ref(false)
let pollTimer = null

// 計算屬性
const statusText = computed(() => {
  const statusMap = {
    pending: '等待中',
    running: '同步中',
    completed: '已完成',
    failed: '失敗'
  }
  return statusMap[status.value] || status.value
})

// 方法
const fetchStatus = async () => {
  try {
    const response = await api.get(`/api/sync/status/${props.taskId}`)
    taskData.value = response.data
    status.value = response.data.status
    progress.value = response.data.progress || 0

    // 檢查是否完成
    if (['completed', 'failed'].includes(status.value)) {
      stopPolling()
      emit('complete', {
        success: status.value === 'completed',
        ...response.data
      })
    }
  } catch (error) {
    console.error('獲取同步狀態失敗:', error)
    emit('error', error)
  }
}

const startPolling = () => {
  stopPolling()
  pollTimer = setInterval(fetchStatus, props.pollInterval)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const cancel = async () => {
  cancelling.value = true
  // 注意：目前 API 未實作取消功能
  // 這裡只是 UI 展示
  setTimeout(() => {
    cancelling.value = false
    stopPolling()
    emit('complete', { success: false, cancelled: true })
  }, 1000)
}

// 生命週期
onMounted(() => {
  fetchStatus()
  startPolling()
})

onUnmounted(() => {
  stopPolling()
})

// 監聽 taskId 變化
watch(() => props.taskId, () => {
  fetchStatus()
  startPolling()
})
</script>

<style scoped>
.sync-progress {
  background: var(--color-background-soft);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-title {
  font-weight: 500;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.pending {
  background: #fff8e1;
  color: #ff8f00;
}

.status-badge.running {
  background: #e3f2fd;
  color: #1976d2;
}

.status-badge.completed {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.failed {
  background: #ffebee;
  color: #c62828;
}

.progress-bar-container {
  height: 8px;
  background: var(--color-background);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.progress-bar {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-bar.pending,
.progress-bar.running {
  background: #2196f3;
}

.progress-bar.completed {
  background: #4caf50;
}

.progress-bar.failed {
  background: #f44336;
}

.progress-details {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  font-size: 13px;
}

.detail-item {
  display: flex;
  gap: 4px;
}

.label {
  color: var(--color-text-light);
}

.value {
  font-weight: 500;
}

.value.success {
  color: #4caf50;
}

.value.error {
  color: #f44336;
}

.progress-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.btn {
  padding: 6px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-background);
  cursor: pointer;
  font-size: 13px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-list {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--color-border);
}

.error-list h4 {
  font-size: 13px;
  margin-bottom: 8px;
  color: #f44336;
}

.error-list ul {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: var(--color-text-light);
}

.error-list li {
  margin-bottom: 4px;
}
</style>
