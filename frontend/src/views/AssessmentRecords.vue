<template>
  <div class="assessment-records-page">
    <div class="page-header">
      <h1>考核記錄管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增記錄
        </el-button>
      </div>
    </div>

    <!-- 員工選擇與摘要 -->
    <el-row :gutter="20">
      <!-- 左側：篩選與列表 -->
      <el-col :xs="24" :lg="16">
        <!-- 篩選區 -->
        <el-card class="filter-card" shadow="never">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-select
                v-model="selectedEmployeeId"
                filterable
                remote
                :remote-method="searchEmployees"
                :loading="searchLoading"
                placeholder="搜尋員工"
                clearable
                style="width: 100%"
                @change="onEmployeeChange"
              >
                <el-option
                  v-for="emp in employeeOptions"
                  :key="emp.id"
                  :label="`${emp.employee_id} - ${emp.employee_name}`"
                  :value="emp.id"
                />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-model="filterYear" placeholder="年度" @change="onFilter">
                <el-option
                  v-for="y in yearOptions"
                  :key="y"
                  :label="`${y} 年`"
                  :value="y"
                />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-model="filterMonth" placeholder="月份" clearable @change="onFilter">
                <el-option
                  v-for="m in 12"
                  :key="m"
                  :label="`${m} 月`"
                  :value="m"
                />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-select v-model="filterCategory" placeholder="類別" clearable @change="onFilter">
                <el-option
                  v-for="(cat, key) in ASSESSMENT_CATEGORIES"
                  :key="key"
                  :label="cat.label"
                  :value="key"
                />
              </el-select>
            </el-col>
            <el-col :span="4">
              <el-checkbox v-model="showDeleted" @change="onFilter">
                顯示已刪除
              </el-checkbox>
            </el-col>
          </el-row>
        </el-card>

        <!-- 記錄列表 -->
        <el-card shadow="never">
          <el-table
            v-loading="loading"
            :data="records"
            border
            stripe
            row-key="id"
            :row-class-name="getRowClassName"
          >
            <el-table-column prop="record_date" label="日期" width="110" sortable>
              <template #default="{ row }">
                {{ formatDate(row.record_date) }}
              </template>
            </el-table-column>

            <el-table-column prop="standard_code" label="代碼" width="80">
              <template #default="{ row }">
                <el-tag
                  :type="row.base_points > 0 ? 'success' : 'danger'"
                  size="small"
                >
                  {{ row.standard_code }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="standard_name" label="項目名稱" min-width="180" show-overflow-tooltip />

            <el-table-column label="責任判定" width="100" align="center">
              <template #default="{ row }">
                <template v-if="row.fault_responsibility">
                  <el-tooltip :content="`疏失 ${row.fault_responsibility.fault_count} 項`">
                    <el-tag
                      :type="getResponsibilityTagType(row.fault_responsibility.responsibility_level)"
                      size="small"
                    >
                      {{ row.fault_responsibility.responsibility_level }}
                    </el-tag>
                  </el-tooltip>
                </template>
                <span v-else class="text-muted">—</span>
              </template>
            </el-table-column>

            <el-table-column prop="cumulative_count" label="累計" width="70" align="center">
              <template #default="{ row }">
                <span v-if="row.cumulative_count > 1" class="cumulative-badge">
                  第{{ row.cumulative_count }}次
                </span>
                <span v-else class="text-muted">—</span>
              </template>
            </el-table-column>

            <el-table-column label="分數計算" width="200">
              <template #default="{ row }">
                <div class="score-breakdown">
                  <span class="base">{{ row.base_points }}</span>
                  <span v-if="row.responsibility_coefficient" class="operator">×{{ row.responsibility_coefficient }}</span>
                  <span v-if="row.cumulative_multiplier > 1" class="operator">×{{ row.cumulative_multiplier.toFixed(1) }}</span>
                  <span class="equals">=</span>
                  <span class="final" :class="row.final_points > 0 ? 'positive' : 'negative'">
                    {{ row.final_points > 0 ? '+' : '' }}{{ row.final_points?.toFixed(1) }}
                  </span>
                </div>
              </template>
            </el-table-column>

            <el-table-column prop="is_deleted" label="狀態" width="70" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.is_deleted" type="info" size="small">已刪除</el-tag>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link size="small" @click="viewRecord(row)">
                  查看
                </el-button>
                <template v-if="!row.is_deleted">
                  <el-button type="danger" link size="small" @click="deleteRecord(row)">
                    刪除
                  </el-button>
                </template>
                <template v-else>
                  <el-button type="success" link size="small" @click="restoreRecord(row)">
                    還原
                  </el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右側：年度摘要 -->
      <el-col :xs="24" :lg="8" class="summary-col">
        <el-card v-if="selectedEmployeeId" shadow="never" class="summary-card">
          <template #header>
            <div class="card-header">
              <span>{{ filterYear }} 年度考核摘要</span>
              <el-button type="primary" link size="small" @click="refreshSummary">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          <AssessmentSummary
            ref="summaryRef"
            :employee-id="selectedEmployeeId"
            :year="filterYear"
            :on-view-all="() => {}"
          />
        </el-card>
        <el-card v-else shadow="never" class="summary-card">
          <el-empty description="請選擇員工以查看年度摘要" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增/查看對話框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="viewingRecord ? '考核記錄詳情' : '新增考核記錄'"
      width="800px"
      destroy-on-close
    >
      <AssessmentRecordForm
        v-if="!viewingRecord"
        ref="formRef"
        :employee-id="selectedEmployeeId"
        @submit="onFormSubmit"
      />

      <!-- 查看模式 -->
      <template v-else>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="員工">
            {{ viewingRecord.employee_name || `ID: ${viewingRecord.employee_id}` }}
          </el-descriptions-item>
          <el-descriptions-item label="事件日期">
            {{ formatDate(viewingRecord.record_date) }}
          </el-descriptions-item>
          <el-descriptions-item label="考核項目">
            <el-tag :type="viewingRecord.base_points > 0 ? 'success' : 'danger'" size="small">
              {{ viewingRecord.standard_code }}
            </el-tag>
            {{ viewingRecord.standard_name }}
          </el-descriptions-item>
          <el-descriptions-item label="基本分數">
            {{ viewingRecord.base_points }} 分
          </el-descriptions-item>
          <el-descriptions-item label="事件描述" :span="2">
            {{ viewingRecord.description || '無' }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 責任判定詳情 -->
        <template v-if="viewingRecord.fault_responsibility">
          <el-divider>責任判定詳情</el-divider>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="延誤時間">
              {{ Math.floor(viewingRecord.fault_responsibility.delay_seconds / 60) }} 分
              {{ viewingRecord.fault_responsibility.delay_seconds % 60 }} 秒
            </el-descriptions-item>
            <el-descriptions-item label="疏失項數">
              {{ viewingRecord.fault_responsibility.fault_count }} / 9 項
            </el-descriptions-item>
            <el-descriptions-item label="責任程度">
              <el-tag :type="getResponsibilityTagType(viewingRecord.fault_responsibility.responsibility_level)">
                {{ viewingRecord.fault_responsibility.responsibility_level }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="責任係數">
              ×{{ viewingRecord.fault_responsibility.responsibility_coefficient }}
            </el-descriptions-item>
            <el-descriptions-item label="已勾選疏失項目" :span="2">
              <div class="checked-faults">
                <el-tag
                  v-for="fault in getCheckedFaults(viewingRecord.fault_responsibility.checklist_results)"
                  :key="fault"
                  type="danger"
                  size="small"
                  style="margin: 2px"
                >
                  {{ fault }}
                </el-tag>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </template>

        <!-- 分數計算 -->
        <el-divider>分數計算</el-divider>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="累計次數">
            第 {{ viewingRecord.cumulative_count || 1 }} 次
          </el-descriptions-item>
          <el-descriptions-item label="累計倍率">
            ×{{ viewingRecord.cumulative_multiplier?.toFixed(1) || '1.0' }}
          </el-descriptions-item>
          <el-descriptions-item label="實際扣分">
            {{ viewingRecord.actual_points?.toFixed(1) }} 分
          </el-descriptions-item>
          <el-descriptions-item label="最終分數">
            <span :class="viewingRecord.final_points > 0 ? 'text-success' : 'text-danger'" style="font-weight: bold">
              {{ viewingRecord.final_points > 0 ? '+' : '' }}{{ viewingRecord.final_points?.toFixed(1) }} 分
            </span>
          </el-descriptions-item>
        </el-descriptions>
      </template>

      <template #footer>
        <el-button @click="dialogVisible = false">關閉</el-button>
        <el-button v-if="!viewingRecord" type="primary" :loading="saving" @click="submitForm">
          建立
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 考核記錄列表頁面
 * 對應 tasks.md T186: 建立考核記錄列表頁面
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { useAssessmentsStore, ASSESSMENT_CATEGORIES, FAULT_CHECKLIST_ITEMS } from '@/stores/assessments'
import { cloudApi } from '@/services/api'
import AssessmentRecordForm from '@/components/assessments/AssessmentRecordForm.vue'
import AssessmentSummary from '@/components/assessments/AssessmentSummary.vue'

const assessmentsStore = useAssessmentsStore()

// 狀態
const loading = ref(false)
const saving = ref(false)
const searchLoading = ref(false)

// 員工選項
const employeeOptions = ref([])
const selectedEmployeeId = ref(null)

// 篩選
const currentYear = new Date().getFullYear()
const filterYear = ref(currentYear)
const filterMonth = ref(null)
const filterCategory = ref('')
const showDeleted = ref(false)

const yearOptions = computed(() => {
  const years = []
  for (let y = currentYear; y >= currentYear - 5; y--) {
    years.push(y)
  }
  return years
})

// 記錄列表
const records = ref([])

// 對話框
const dialogVisible = ref(false)
const viewingRecord = ref(null)
const formRef = ref()
const summaryRef = ref()

// 疏失項目標籤對照
const faultLabels = computed(() => {
  const map = {}
  FAULT_CHECKLIST_ITEMS.forEach(item => {
    map[item.key] = item.label
  })
  return map
})

// 搜尋員工
async function searchEmployees(query) {
  if (!query || query.length < 1) {
    employeeOptions.value = []
    return
  }

  searchLoading.value = true
  try {
    const response = await cloudApi.get('/api/employees', {
      params: { keyword: query, limit: 20 }
    })
    employeeOptions.value = response.data
  } catch (err) {
    console.error('搜尋員工失敗:', err)
    employeeOptions.value = []
  } finally {
    searchLoading.value = false
  }
}

// 員工變更
function onEmployeeChange() {
  loadRecords()
}

// 篩選變更
function onFilter() {
  loadRecords()
}

// 載入記錄
async function loadRecords() {
  if (!selectedEmployeeId.value) {
    records.value = []
    return
  }

  loading.value = true
  try {
    const data = await assessmentsStore.fetchRecords(selectedEmployeeId.value, {
      year: filterYear.value,
      month: filterMonth.value || undefined,
      category: filterCategory.value || undefined,
      include_deleted: showDeleted.value
    })
    records.value = data
  } catch (err) {
    ElMessage.error('載入記錄失敗')
    records.value = []
  } finally {
    loading.value = false
  }
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getFullYear()}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}`
}

// 取得行樣式
function getRowClassName({ row }) {
  if (row.is_deleted) return 'deleted-row'
  return ''
}

// 取得責任程度標籤類型
function getResponsibilityTagType(level) {
  if (level === '完全責任') return 'danger'
  if (level === '主要責任') return 'warning'
  if (level === '次要責任') return 'info'
  return ''
}

// 取得已勾選疏失項目
function getCheckedFaults(checklist) {
  if (!checklist) return []
  return Object.entries(checklist)
    .filter(([, checked]) => checked)
    .map(([key]) => faultLabels.value[key] || key)
}

// 顯示新增對話框
function showCreateDialog() {
  viewingRecord.value = null
  dialogVisible.value = true
}

// 查看記錄
function viewRecord(record) {
  viewingRecord.value = record
  dialogVisible.value = true
}

// 刪除記錄 - 強化二次確認
async function deleteRecord(record) {
  // 第一階段：顯示警告
  try {
    await ElMessageBox.confirm(
      `即將刪除 ${record.employee_name || '員工'} 的考核記錄 (${record.standard_code})。\n\n⚠️ 刪除後將觸發累計次數重算，此操作可能影響其他記錄的最終分數！`,
      '刪除確認',
      {
        type: 'warning',
        confirmButtonText: '繼續刪除',
        cancelButtonText: '取消'
      }
    )
  } catch {
    return
  }

  // 第二階段：要求輸入確認文字
  try {
    const { value } = await ElMessageBox.prompt(
      '請輸入「DELETE」以確認刪除（此操作不可復原）：',
      '二次確認',
      {
        confirmButtonText: '確認刪除',
        cancelButtonText: '取消',
        inputPattern: /^DELETE$/,
        inputErrorMessage: '請輸入正確的確認文字「DELETE」',
        type: 'warning'
      }
    )

    if (value !== 'DELETE') {
      ElMessage.info('刪除已取消')
      return
    }
  } catch {
    return
  }

  try {
    await assessmentsStore.deleteRecord(record.id)
    ElMessage.success('刪除成功，累計次數已重新計算')
    loadRecords()
    refreshSummary()
  } catch (err) {
    ElMessage.error('刪除失敗')
  }
}

// 還原記錄
async function restoreRecord(record) {
  try {
    await assessmentsStore.restoreRecord(record.id)
    ElMessage.success('還原成功')
    loadRecords()
    refreshSummary()
  } catch (err) {
    ElMessage.error('還原失敗')
  }
}

// 表單提交
async function onFormSubmit(data) {
  saving.value = true
  try {
    await assessmentsStore.createRecord(data)
    ElMessage.success('建立成功')
    dialogVisible.value = false
    loadRecords()
    refreshSummary()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '建立失敗')
  } finally {
    saving.value = false
  }
}

// 提交表單
async function submitForm() {
  if (formRef.value) {
    const valid = await formRef.value.validate()
    if (valid) {
      onFormSubmit(formRef.value.getData())
    }
  }
}

// 刷新摘要
function refreshSummary() {
  if (summaryRef.value) {
    summaryRef.value.refresh()
  }
}

onMounted(() => {
  // 初始載入
})
</script>

<style scoped>
.assessment-records-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
}

.filter-card {
  margin-bottom: 20px;
}

.summary-card {
  position: sticky;
  top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-muted {
  color: #c0c4cc;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}

.cumulative-badge {
  display: inline-block;
  padding: 2px 6px;
  background: #fef0f0;
  color: #f56c6c;
  border-radius: 4px;
  font-size: 12px;
}

.score-breakdown {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
}

.score-breakdown .base {
  color: #666;
}

.score-breakdown .operator {
  color: #999;
}

.score-breakdown .equals {
  color: #999;
  margin: 0 4px;
}

.score-breakdown .final {
  font-weight: bold;
}

.score-breakdown .final.positive {
  color: #67c23a;
}

.score-breakdown .final.negative {
  color: #f56c6c;
}

.checked-faults {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

:deep(.deleted-row) {
  background-color: #f5f5f5 !important;
  color: #999;
}

/* 響應式調整 */
@media (max-width: 1199px) {
  .summary-col {
    margin-top: 20px;
  }

  .summary-card {
    position: static;
  }
}
</style>
