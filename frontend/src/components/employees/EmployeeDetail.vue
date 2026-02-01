<template>
  <div class="employee-detail">
    <!-- 員工基本資訊 -->
    <div class="info-section">
      <div class="info-header">
        <div class="employee-identity">
          <h2 class="employee-name">{{ employee.employee_name }}</h2>
          <span class="employee-code">{{ employee.employee_id }}</span>
        </div>
        <div class="employee-status">
          <span :class="['dept-badge', getDeptClass(employee.current_department)]">
            {{ employee.current_department }}
          </span>
          <span :class="['status-badge', employee.is_resigned ? 'resigned' : 'active']">
            {{ employee.is_resigned ? '離職' : '在職' }}
          </span>
        </div>
      </div>

      <div class="info-grid">
        <div class="info-item">
          <label>入職年月</label>
          <span>{{ employee.hire_year_month || '-' }}</span>
        </div>
        <div class="info-item">
          <label>電話</label>
          <span>{{ employee.phone || '-' }}</span>
        </div>
        <div class="info-item">
          <label>電子郵件</label>
          <span>{{ employee.email || '-' }}</span>
        </div>
        <div class="info-item">
          <label>緊急聯絡人</label>
          <span>{{ employee.emergency_contact || '-' }}</span>
        </div>
        <div class="info-item">
          <label>緊急聯絡電話</label>
          <span>{{ employee.emergency_phone || '-' }}</span>
        </div>
      </div>
    </div>

    <!-- 調動歷史 -->
    <div class="history-section">
      <h3 class="section-title">調動歷史</h3>

      <LoadingSpinner v-if="loadingTransfers" size="small" />

      <div v-else-if="transfers.length === 0" class="no-history">
        尚無調動記錄
      </div>

      <div v-else class="transfer-list">
        <div
          v-for="transfer in transfers"
          :key="transfer.id"
          class="transfer-item"
        >
          <div class="transfer-arrow">
            <span class="from-dept">{{ transfer.from_department }}</span>
            <span class="arrow">→</span>
            <span class="to-dept">{{ transfer.to_department }}</span>
          </div>
          <div class="transfer-info">
            <span class="transfer-date">{{ formatDate(transfer.transfer_date) }}</span>
            <span v-if="transfer.reason" class="transfer-reason">
              {{ transfer.reason }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按鈕 -->
    <div class="detail-actions">
      <AppButton @click="$emit('close')">
        關閉
      </AppButton>
      <AppButton @click="$emit('edit', employee)">
        編輯
      </AppButton>
      <AppButton
        v-if="!employee.is_resigned"
        variant="primary"
        @click="$emit('transfer', employee)"
      >
        調動
      </AppButton>
      <AppButton
        v-if="employee.is_resigned"
        :loading="activating"
        variant="success"
        @click="handleActivate"
      >
        復職
      </AppButton>
      <AppButton
        v-else
        :loading="resigning"
        variant="danger"
        @click="handleResign"
      >
        離職
      </AppButton>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useEmployeesStore } from '@/stores/employees'
import AppButton from '@/components/common/AppButton.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'

const props = defineProps({
  employee: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['edit', 'transfer', 'close'])

const store = useEmployeesStore()

// 狀態
const transfers = ref([])
const loadingTransfers = ref(false)
const resigning = ref(false)
const activating = ref(false)

// 生命週期
onMounted(async () => {
  await loadTransferHistory()
})

// 方法
function getDeptClass(department) {
  return department === '淡海' ? 'danhai' : 'ankeng'
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-TW')
}

async function loadTransferHistory() {
  loadingTransfers.value = true
  try {
    const result = await store.fetchTransferHistory(props.employee.id)
    transfers.value = result.items
  } catch (err) {
    console.error('載入調動歷史失敗:', err)
  } finally {
    loadingTransfers.value = false
  }
}

async function handleResign() {
  if (!confirm(`確定要將 ${props.employee.employee_name} 標記為離職嗎？`)) {
    return
  }

  resigning.value = true
  try {
    await store.resignEmployee(props.employee.id)
    emit('close')
  } catch (err) {
    console.error('標記離職失敗:', err)
    alert('操作失敗：' + (err.message || '未知錯誤'))
  } finally {
    resigning.value = false
  }
}

async function handleActivate() {
  if (!confirm(`確定要讓 ${props.employee.employee_name} 復職嗎？`)) {
    return
  }

  activating.value = true
  try {
    await store.activateEmployee(props.employee.id)
    emit('close')
  } catch (err) {
    console.error('復職失敗:', err)
    alert('操作失敗：' + (err.message || '未知錯誤'))
  } finally {
    activating.value = false
  }
}
</script>

<style scoped>
.employee-detail {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-section {
  background: var(--color-background-soft);
  padding: 20px;
  border-radius: 8px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.employee-identity {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.employee-name {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.employee-code {
  font-family: monospace;
  font-size: 14px;
  color: var(--color-text-light);
}

.employee-status {
  display: flex;
  gap: 8px;
}

.dept-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.dept-badge.danhai {
  background: #e3f2fd;
  color: #1976d2;
}

.dept-badge.ankeng {
  background: #fff3e0;
  color: #f57c00;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: #e8f5e9;
  color: #388e3c;
}

.status-badge.resigned {
  background: #f5f5f5;
  color: #757575;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  color: var(--color-text-light);
}

.info-item span {
  font-size: 14px;
  color: var(--color-text);
}

.history-section {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 16px 0;
}

.no-history {
  color: var(--color-text-light);
  text-align: center;
  padding: 20px;
}

.transfer-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.transfer-item {
  padding: 12px;
  background: var(--color-background-soft);
  border-radius: 6px;
}

.transfer-arrow {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.from-dept,
.to-dept {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.from-dept {
  background: #ffebee;
  color: #c62828;
}

.to-dept {
  background: #e8f5e9;
  color: #2e7d32;
}

.arrow {
  color: var(--color-text-light);
}

.transfer-info {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--color-text-light);
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}
</style>
