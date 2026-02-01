<template>
  <div class="google-services-page">
    <h1 class="page-title">Google 服務管理</h1>

    <!-- 連線狀態 -->
    <section class="section">
      <h2 class="section-title">連線狀態</h2>
      <ConnectionStatus :auto-refresh="true" :refresh-interval="60000" />
    </section>

    <!-- 同步控制 -->
    <section class="section">
      <h2 class="section-title">班表同步</h2>

      <div class="sync-controls">
        <div class="sync-form">
          <div class="form-row">
            <div class="form-group">
              <label>部門</label>
              <select v-model="syncForm.department">
                <option value="">全部部門</option>
                <option value="淡海">淡海</option>
                <option value="安坑">安坑</option>
              </select>
            </div>

            <div class="form-group">
              <label>年份</label>
              <select v-model="syncForm.year">
                <option v-for="y in availableYears" :key="y" :value="y">
                  {{ y }}
                </option>
              </select>
            </div>

            <div class="form-group">
              <label>月份</label>
              <select v-model="syncForm.month">
                <option v-for="m in 12" :key="m" :value="m">
                  {{ m }} 月
                </option>
              </select>
            </div>

            <div class="form-actions">
              <button
                class="btn btn-primary"
                :disabled="syncing"
                @click="triggerSync"
              >
                {{ syncing ? '同步中...' : '立即同步' }}
              </button>
            </div>
          </div>
        </div>

        <!-- 同步進度 -->
        <SyncProgress
          v-if="currentTaskId"
          :task-id="currentTaskId"
          @complete="onSyncComplete"
        />

        <!-- 同步結果 -->
        <SyncResult
          v-if="lastSyncResult"
          :result="lastSyncResult"
          @dismiss="lastSyncResult = null"
        />
      </div>
    </section>

    <!-- 排程器狀態 -->
    <section class="section">
      <h2 class="section-title">定時任務</h2>

      <div class="scheduler-status">
        <div class="status-header">
          <span :class="['status-indicator', schedulerRunning ? 'running' : 'stopped']"></span>
          <span>排程器狀態：{{ schedulerRunning ? '執行中' : '已停止' }}</span>

          <div v-if="isAdmin" class="scheduler-controls">
            <button
              v-if="!schedulerRunning"
              class="btn btn-success"
              @click="startScheduler"
            >
              啟動
            </button>
            <button
              v-else
              class="btn btn-warning"
              @click="stopScheduler"
            >
              停止
            </button>
          </div>
        </div>

        <div v-if="schedulerJobs.length > 0" class="jobs-list">
          <h3>已註冊任務</h3>
          <table class="jobs-table">
            <thead>
              <tr>
                <th>任務 ID</th>
                <th>名稱</th>
                <th>下次執行時間</th>
                <th>觸發規則</th>
                <th v-if="isAdmin">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in schedulerJobs" :key="job.id">
                <td>{{ job.id }}</td>
                <td>{{ job.name }}</td>
                <td>{{ formatDateTime(job.next_run_time) }}</td>
                <td>{{ job.trigger }}</td>
                <td v-if="isAdmin">
                  <button
                    class="btn btn-sm btn-primary"
                    title="立即執行"
                    @click="triggerJob(job.id)"
                  >
                    ▶
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- 同步歷史 -->
    <section class="section">
      <h2 class="section-title">同步歷史</h2>

      <div class="history-controls">
        <button class="btn btn-secondary" @click="loadSyncHistory">
          重新載入
        </button>
      </div>

      <div v-if="loadingHistory" class="loading">載入中...</div>

      <table v-else-if="syncHistory.length > 0" class="history-table">
        <thead>
          <tr>
            <th>批次 ID</th>
            <th>類型</th>
            <th>部門</th>
            <th>年月</th>
            <th>狀態</th>
            <th>成功/錯誤</th>
            <th>觸發方式</th>
            <th>時間</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in syncHistory" :key="task.batch_id">
            <td class="batch-id">{{ task.batch_id.slice(0, 8) }}...</td>
            <td>{{ task.task_type }}</td>
            <td>
              <span v-if="task.department" :class="['dept-badge', task.department]">
                {{ task.department }}
              </span>
              <span v-else>全部</span>
            </td>
            <td>{{ task.year }}/{{ task.month }}</td>
            <td>
              <span :class="['status-badge', task.status]">
                {{ getStatusText(task.status) }}
              </span>
            </td>
            <td>
              <span class="success">{{ task.success_count || 0 }}</span>
              /
              <span class="error">{{ task.error_count || 0 }}</span>
            </td>
            <td>{{ task.triggered_by === 'auto' ? '自動' : '手動' }}</td>
            <td>{{ formatDateTime(task.created_at) }}</td>
          </tr>
        </tbody>
      </table>

      <div v-else class="no-data">
        沒有同步記錄
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import api from '@/utils/api'
import ConnectionStatus from '@/components/common/ConnectionStatus.vue'
import SyncProgress from '@/components/sync/SyncProgress.vue'
import SyncResult from '@/components/sync/SyncResult.vue'

const authStore = useAuthStore()

// 狀態
const syncing = ref(false)
const currentTaskId = ref(null)
const lastSyncResult = ref(null)
const schedulerRunning = ref(false)
const schedulerJobs = ref([])
const syncHistory = ref([])
const loadingHistory = ref(false)

// 同步表單
const syncForm = ref({
  department: '',
  year: new Date().getFullYear(),
  month: new Date().getMonth() + 1
})

// 計算屬性
const availableYears = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

const isAdmin = computed(() => {
  return authStore.user?.role === 'admin'
})

// 方法
const formatDateTime = (dateStr) => {
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

const getStatusText = (status) => {
  const statusMap = {
    pending: '等待中',
    running: '執行中',
    completed: '已完成',
    failed: '失敗'
  }
  return statusMap[status] || status
}

const triggerSync = async () => {
  syncing.value = true
  lastSyncResult.value = null

  try {
    const response = await api.post('/api/sync/schedule', {
      department: syncForm.value.department || null,
      year: syncForm.value.year,
      month: syncForm.value.month
    })

    if (response.data.batch_id) {
      currentTaskId.value = response.data.batch_id
    } else {
      // 全部門同步直接返回結果
      lastSyncResult.value = response.data
      syncing.value = false
    }
  } catch (error) {
    console.error('觸發同步失敗:', error)
    lastSyncResult.value = {
      success: false,
      message: error.response?.data?.detail || '同步失敗'
    }
    syncing.value = false
  }
}

const onSyncComplete = (result) => {
  syncing.value = false
  currentTaskId.value = null
  lastSyncResult.value = result
  loadSyncHistory()
}

const loadSchedulerStatus = async () => {
  try {
    const response = await api.get('/api/sync/scheduler')
    schedulerRunning.value = response.data.running
    schedulerJobs.value = response.data.jobs
  } catch (error) {
    console.error('載入排程器狀態失敗:', error)
  }
}

const startScheduler = async () => {
  try {
    await api.post('/api/sync/scheduler/start')
    await loadSchedulerStatus()
  } catch (error) {
    console.error('啟動排程器失敗:', error)
  }
}

const stopScheduler = async () => {
  try {
    await api.post('/api/sync/scheduler/stop')
    await loadSchedulerStatus()
  } catch (error) {
    console.error('停止排程器失敗:', error)
  }
}

const triggerJob = async (jobId) => {
  try {
    await api.post(`/api/sync/scheduler/trigger/${jobId}`)
    alert(`任務 ${jobId} 已觸發`)
  } catch (error) {
    console.error('觸發任務失敗:', error)
    alert('觸發任務失敗')
  }
}

const loadSyncHistory = async () => {
  loadingHistory.value = true

  try {
    const response = await api.get('/api/sync/history', {
      params: { limit: 20 }
    })
    syncHistory.value = response.data.items
  } catch (error) {
    console.error('載入同步歷史失敗:', error)
  } finally {
    loadingHistory.value = false
  }
}

// 生命週期
onMounted(() => {
  loadSchedulerStatus()
  loadSyncHistory()
})
</script>

<style scoped>
.google-services-page {
  padding: 20px;
}

.page-title {
  font-size: 24px;
  margin-bottom: 20px;
  color: var(--color-heading);
}

.section {
  background: var(--color-background);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.section-title {
  font-size: 18px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

/* 同步控制 */
.sync-form {
  margin-bottom: 16px;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-group label {
  font-size: 12px;
  color: var(--color-text-light);
}

.form-group select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  font-size: 14px;
  min-width: 120px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-secondary {
  background: var(--color-background-soft);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.btn-success {
  background: #4caf50;
  color: white;
}

.btn-warning {
  background: #ff9800;
  color: white;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 排程器狀態 */
.scheduler-status {
  padding: 16px;
  background: var(--color-background-soft);
  border-radius: 8px;
}

.status-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-indicator.running {
  background: #4caf50;
}

.status-indicator.stopped {
  background: #f44336;
}

.scheduler-controls {
  margin-left: auto;
}

.jobs-list h3 {
  font-size: 14px;
  margin-bottom: 12px;
}

.jobs-table {
  width: 100%;
  border-collapse: collapse;
}

.jobs-table th,
.jobs-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.jobs-table th {
  font-weight: 500;
  background: var(--color-background);
}

/* 同步歷史 */
.history-controls {
  margin-bottom: 16px;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.history-table th {
  font-weight: 500;
  background: var(--color-background-soft);
}

.batch-id {
  font-family: monospace;
  font-size: 12px;
}

.dept-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.dept-badge.淡海 {
  background: #e3f2fd;
  color: #1976d2;
}

.dept-badge.安坑 {
  background: #f3e5f5;
  color: #7b1fa2;
}

.status-badge {
  padding: 2px 8px;
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

.success {
  color: #4caf50;
}

.error {
  color: #f44336;
}

.loading,
.no-data {
  text-align: center;
  padding: 20px;
  color: var(--color-text-light);
}
</style>
