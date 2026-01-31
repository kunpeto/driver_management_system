<template>
  <div class="employees-page">
    <!-- 頁面標題 -->
    <PageHeader title="員工管理" subtitle="管理員工基本資料、調動記錄">
      <template #actions>
        <AppButton type="primary" @click="showCreateDialog = true">
          新增員工
        </AppButton>
        <AppButton @click="showBatchDialog = true">
          批次操作
        </AppButton>
      </template>
    </PageHeader>

    <!-- 篩選區塊 -->
    <div class="filter-section">
      <div class="filter-row">
        <!-- 搜尋框 -->
        <div class="filter-item search-box">
          <AppInput
            v-model="searchKeyword"
            placeholder="搜尋員工編號或姓名..."
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <span class="search-icon">🔍</span>
            </template>
          </AppInput>
        </div>

        <!-- 部門篩選 -->
        <div class="filter-item">
          <select v-model="selectedDepartment" class="filter-select" @change="handleDepartmentChange">
            <option
              v-for="dept in DEPARTMENT_OPTIONS"
              :key="dept.value"
              :value="dept.value"
            >
              {{ dept.label }}
            </option>
          </select>
        </div>

        <!-- 離職狀態 -->
        <div class="filter-item">
          <label class="checkbox-label">
            <input
              type="checkbox"
              v-model="includeResigned"
              @change="handleIncludeResignedChange"
            />
            包含離職員工
          </label>
        </div>

        <!-- 重置篩選 -->
        <div class="filter-item">
          <AppButton size="small" @click="resetFilters">
            重置
          </AppButton>
        </div>
      </div>
    </div>

    <!-- 統計摘要 -->
    <div class="stats-section" v-if="statistics.total > 0">
      <div class="stat-card">
        <div class="stat-value">{{ statistics.total }}</div>
        <div class="stat-label">總人數</div>
      </div>
      <div class="stat-card active">
        <div class="stat-value">{{ statistics.active }}</div>
        <div class="stat-label">在職</div>
      </div>
      <div class="stat-card resigned">
        <div class="stat-value">{{ statistics.resigned }}</div>
        <div class="stat-label">離職</div>
      </div>
      <div class="stat-card danhai">
        <div class="stat-value">{{ statistics.by_department?.['淡海'] || 0 }}</div>
        <div class="stat-label">淡海</div>
      </div>
      <div class="stat-card ankeng">
        <div class="stat-value">{{ statistics.by_department?.['安坑'] || 0 }}</div>
        <div class="stat-label">安坑</div>
      </div>
    </div>

    <!-- 員工列表 -->
    <div class="table-section">
      <LoadingSpinner v-if="loading && employees.length === 0" />

      <EmptyState
        v-else-if="employees.length === 0"
        message="沒有找到符合條件的員工"
      />

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>員工編號</th>
            <th>姓名</th>
            <th>部門</th>
            <th>入職年月</th>
            <th>電話</th>
            <th>狀態</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="employee in employees"
            :key="employee.id"
            :class="{ resigned: employee.is_resigned }"
          >
            <td class="employee-id">{{ employee.employee_id }}</td>
            <td>{{ employee.employee_name }}</td>
            <td>
              <span :class="['dept-badge', getDeptClass(employee.current_department)]">
                {{ employee.current_department }}
              </span>
            </td>
            <td>{{ employee.hire_year_month || '-' }}</td>
            <td>{{ employee.phone || '-' }}</td>
            <td>
              <span :class="['status-badge', employee.is_resigned ? 'resigned' : 'active']">
                {{ employee.is_resigned ? '離職' : '在職' }}
              </span>
            </td>
            <td class="actions">
              <AppButton size="small" @click="viewEmployee(employee)">
                查看
              </AppButton>
              <AppButton
                size="small"
                @click="editEmployee(employee)"
                :disabled="!canEditEmployee(employee)"
                :title="canEditEmployee(employee) ? '' : '無權限編輯此部門員工'"
              >
                編輯
              </AppButton>
              <AppButton
                v-if="!employee.is_resigned"
                size="small"
                @click="openTransferDialog(employee)"
                :disabled="!canEditEmployee(employee)"
                :title="canEditEmployee(employee) ? '' : '無權限調動此部門員工'"
              >
                調動
              </AppButton>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 載入更多 -->
      <div class="load-more" v-if="hasMore">
        <AppButton :loading="loading" @click="loadMore">
          載入更多
        </AppButton>
      </div>
    </div>

    <!-- 新增/編輯對話框 -->
    <AppModal
      v-model="showCreateDialog"
      :title="editingEmployee ? '編輯員工' : '新增員工'"
      width="600px"
    >
      <EmployeeForm
        :employee="editingEmployee"
        @submit="handleFormSubmit"
        @cancel="closeFormDialog"
      />
    </AppModal>

    <!-- 員工詳情對話框 -->
    <AppModal
      v-model="showDetailDialog"
      title="員工詳情"
      width="700px"
    >
      <EmployeeDetail
        v-if="selectedEmployee"
        :employee="selectedEmployee"
        @edit="editEmployee"
        @transfer="openTransferDialog"
        @close="showDetailDialog = false"
      />
    </AppModal>

    <!-- 調動對話框 -->
    <AppModal
      v-model="showTransferDialog"
      title="員工調動"
      width="500px"
    >
      <TransferDialog
        v-if="transferEmployee"
        :employee="transferEmployee"
        @submit="handleTransfer"
        @cancel="showTransferDialog = false"
      />
    </AppModal>

    <!-- 批次操作對話框 -->
    <AppModal
      v-model="showBatchDialog"
      title="批次操作"
      width="600px"
    >
      <BatchOperations
        @import-complete="handleImportComplete"
        @close="showBatchDialog = false"
      />
    </AppModal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useEmployeesStore } from '@/stores/employees'
import { useAuthStore } from '@/stores/auth'
import { DEPARTMENT_OPTIONS } from '@/constants/departments'
import PageHeader from '@/components/common/PageHeader.vue'
import AppButton from '@/components/common/AppButton.vue'
import AppInput from '@/components/common/AppInput.vue'
import AppModal from '@/components/common/AppModal.vue'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'

// 延遲載入元件
import EmployeeForm from '@/components/employees/EmployeeForm.vue'
import EmployeeDetail from '@/components/employees/EmployeeDetail.vue'
import TransferDialog from '@/components/employees/TransferDialog.vue'
import BatchOperations from '@/components/employees/BatchOperations.vue'

const store = useEmployeesStore()
const authStore = useAuthStore()

// 響應式狀態
const searchKeyword = ref('')
const selectedDepartment = ref(null)
const includeResigned = ref(false)

// 權限相關計算屬性
const canEditEmployee = (employee) => {
  return authStore.canEditDepartment(employee.current_department)
}

// 對話框狀態
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const showTransferDialog = ref(false)
const showBatchDialog = ref(false)

// 選中的員工
const selectedEmployee = ref(null)
const editingEmployee = ref(null)
const transferEmployee = ref(null)

// 計算屬性
const employees = computed(() => store.employees)
const loading = computed(() => store.loading)
const statistics = computed(() => store.statistics)
const hasMore = computed(() => store.hasMore)

// 生命週期
onMounted(async () => {
  // 根據使用者權限設定預設部門篩選
  const defaultDept = authStore.getDefaultDepartment()
  if (defaultDept) {
    selectedDepartment.value = defaultDept
    store.setDepartmentFilter(defaultDept)
  }

  await Promise.all([
    store.fetchEmployees(),
    store.fetchStatistics()
  ])
})

// 方法
function getDeptClass(department) {
  return department === '淡海' ? 'danhai' : 'ankeng'
}

function handleSearch() {
  store.setSearchFilter(searchKeyword.value)
  store.fetchEmployees()
}

function handleDepartmentChange() {
  store.setDepartmentFilter(selectedDepartment.value)
  store.fetchEmployees()
}

function handleIncludeResignedChange() {
  store.setFilters({ includeResigned: includeResigned.value })
  store.fetchEmployees()
}

function resetFilters() {
  searchKeyword.value = ''
  selectedDepartment.value = null
  includeResigned.value = false
  store.resetFilters()
  store.fetchEmployees()
}

function loadMore() {
  store.loadMore()
}

function viewEmployee(employee) {
  selectedEmployee.value = employee
  showDetailDialog.value = true
}

function editEmployee(employee) {
  editingEmployee.value = employee
  showDetailDialog.value = false
  showCreateDialog.value = true
}

function openTransferDialog(employee) {
  transferEmployee.value = employee
  showDetailDialog.value = false
  showTransferDialog.value = true
}

function closeFormDialog() {
  editingEmployee.value = null
  showCreateDialog.value = false
}

async function handleFormSubmit(formData) {
  try {
    if (editingEmployee.value) {
      await store.updateEmployee(editingEmployee.value.id, formData)
    } else {
      await store.createEmployee(formData)
    }
    closeFormDialog()
    await store.fetchStatistics()
  } catch (err) {
    console.error('表單提交失敗:', err)
    const errorMessage = err.response?.data?.detail || err.message || '操作失敗'
    alert(`錯誤：${errorMessage}`)
  }
}

async function handleTransfer(transferData) {
  try {
    await store.transferEmployee(transferEmployee.value.id, transferData)
    showTransferDialog.value = false
    transferEmployee.value = null
    await store.fetchStatistics()
  } catch (err) {
    console.error('調動失敗:', err)
    const errorMessage = err.response?.data?.detail || err.message || '調動失敗'
    alert(`錯誤：${errorMessage}`)
  }
}

async function handleImportComplete() {
  showBatchDialog.value = false
  await Promise.all([
    store.fetchEmployees(),
    store.fetchStatistics()
  ])
}
</script>

<style scoped>
.employees-page {
  padding: 20px;
}

.filter-section {
  background: var(--color-background-soft);
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.filter-item {
  display: flex;
  align-items: center;
}

.search-box {
  flex: 1;
  min-width: 200px;
  max-width: 400px;
}

.filter-select {
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-background);
  min-width: 120px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.stats-section {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.stat-card {
  background: var(--color-background);
  padding: 16px 24px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  text-align: center;
  min-width: 100px;
}

.stat-card.active {
  border-color: #4caf50;
}

.stat-card.resigned {
  border-color: #9e9e9e;
}

.stat-card.danhai {
  border-color: #2196f3;
}

.stat-card.ankeng {
  border-color: #ff9800;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--color-text);
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-light);
  margin-top: 4px;
}

.table-section {
  background: var(--color-background);
  border-radius: 8px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  background: var(--color-background-soft);
  font-weight: 600;
}

.data-table tr:hover {
  background: var(--color-background-soft);
}

.data-table tr.resigned {
  opacity: 0.6;
}

.employee-id {
  font-family: monospace;
  font-weight: 500;
}

.dept-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
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
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.status-badge.active {
  background: #e8f5e9;
  color: #388e3c;
}

.status-badge.resigned {
  background: #f5f5f5;
  color: #757575;
}

.actions {
  display: flex;
  gap: 8px;
}

.load-more {
  padding: 20px;
  text-align: center;
}

.search-icon {
  opacity: 0.5;
}
</style>
