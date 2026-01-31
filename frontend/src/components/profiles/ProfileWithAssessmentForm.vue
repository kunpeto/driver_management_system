<template>
  <div class="profile-with-assessment-form">
    <el-form ref="formRef" :model="formData" :rules="rules" label-width="120px">
      <!-- 基本資訊 -->
      <div class="form-section">
        <div class="section-title">
          <el-icon><Document /></el-icon>
          基本資訊
        </div>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="員工" prop="employee_id">
              <el-select
                v-model="formData.employee_id"
                filterable
                remote
                :remote-method="searchEmployees"
                :loading="searchLoading"
                placeholder="搜尋員工"
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
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部門" prop="department">
              <el-select v-model="formData.department" placeholder="選擇部門" style="width: 100%">
                <el-option label="淡海" value="淡海" />
                <el-option label="安坑" value="安坑" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="事件日期" prop="event_date">
              <el-date-picker
                v-model="formData.event_date"
                type="date"
                value-format="YYYY-MM-DD"
                placeholder="選擇日期"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="事件時間">
              <el-time-picker
                v-model="formData.event_time"
                format="HH:mm"
                value-format="HH:mm"
                placeholder="選擇時間"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="事件地點">
              <el-input v-model="formData.event_location" placeholder="事件發生地點" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="列車車號">
              <el-input v-model="formData.train_number" placeholder="列車車號" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="事件標題">
          <el-input v-model="formData.event_title" placeholder="簡述事件" />
        </el-form-item>

        <el-form-item label="事件描述">
          <el-input
            v-model="formData.event_description"
            type="textarea"
            :rows="3"
            placeholder="詳細描述事件經過"
          />
        </el-form-item>
      </div>

      <!-- 考核項目選擇 -->
      <div class="form-section">
        <div class="section-title">
          <el-icon><Medal /></el-icon>
          考核項目
        </div>

        <el-form-item label="考核代碼" prop="assessment_code">
          <el-select
            v-model="formData.assessment_code"
            filterable
            placeholder="選擇或搜尋考核項目"
            style="width: 100%"
            @change="onAssessmentCodeChange"
          >
            <el-option-group
              v-for="(standards, category) in groupedStandards"
              :key="category"
              :label="getCategoryLabel(category)"
            >
              <el-option
                v-for="std in standards"
                :key="std.code"
                :label="`${std.code} - ${std.name}（${std.base_points > 0 ? '+' : ''}${std.base_points} 分）`"
                :value="std.code"
              >
                <div class="standard-option">
                  <span class="code">{{ std.code }}</span>
                  <span class="name">{{ std.name }}</span>
                  <span class="points" :class="std.base_points > 0 ? 'bonus' : 'deduction'">
                    {{ std.base_points > 0 ? '+' : '' }}{{ std.base_points }}
                  </span>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
        </el-form-item>

        <!-- 選中項目資訊 -->
        <div v-if="selectedStandard" class="selected-standard">
          <el-alert :type="selectedStandard.base_points > 0 ? 'success' : 'warning'" :closable="false">
            <template #title>
              <div class="standard-info">
                <el-tag :type="selectedStandard.base_points > 0 ? 'success' : 'danger'" size="large">
                  {{ selectedStandard.code }}
                </el-tag>
                <span class="standard-name">{{ selectedStandard.name }}</span>
                <span class="standard-points" :class="selectedStandard.base_points > 0 ? 'bonus' : 'deduction'">
                  {{ selectedStandard.base_points > 0 ? '+' : '' }}{{ selectedStandard.base_points }} 分
                </span>
              </div>
            </template>
            <div v-if="selectedStandard.has_cumulative" class="cumulative-hint">
              <el-icon><Warning /></el-icon>
              此項目適用累計加重機制
            </div>
          </el-alert>
        </div>

        <!-- R02-R05 需要責任判定提示 -->
        <div v-if="isRTypeCode" class="r-type-alert">
          <el-alert
            title="此為責任類項目（R02-R05），需填寫責任判定查核表"
            type="error"
            :closable="false"
            show-icon
          />
        </div>
      </div>

      <!-- R02-R05 責任判定查核表 -->
      <div v-if="isRTypeCode" class="form-section responsibility-section">
        <div class="section-title">
          <el-icon><Warning /></el-icon>
          責任判定查核表
          <span class="section-hint">（R02-R05 必填）</span>
        </div>

        <FaultResponsibilityChecklist
          ref="checklistRef"
          v-model="formData.fault_responsibility_data"
          :base-points="selectedStandard?.base_points || 0"
          :cumulative-count="1"
          @responsibility-change="onResponsibilityChange"
        />
      </div>

      <!-- 分數預覽 -->
      <div v-if="selectedStandard" class="form-section">
        <div class="section-title">
          <el-icon><DataAnalysis /></el-icon>
          分數計算預覽
        </div>

        <div class="score-preview">
          <div class="preview-row">
            <span class="label">基本分數</span>
            <span class="value">{{ selectedStandard.base_points }} 分</span>
          </div>
          <template v-if="isRTypeCode && responsibilityData">
            <div class="preview-row">
              <span class="label">責任係數（{{ responsibilityData.level }}）</span>
              <span class="value">× {{ responsibilityData.coefficient }}</span>
            </div>
            <div class="preview-row">
              <span class="label">實際分數</span>
              <span class="value">= {{ calculatedPoints.actual.toFixed(1) }} 分</span>
            </div>
          </template>
          <div class="preview-row final">
            <span class="label">預計最終分數</span>
            <span class="value" :class="calculatedPoints.final > 0 ? 'bonus' : 'deduction'">
              {{ calculatedPoints.final > 0 ? '+' : '' }}{{ calculatedPoints.final.toFixed(1) }} 分
            </span>
          </div>
        </div>
      </div>
    </el-form>
  </div>
</template>

<script setup>
/**
 * 履歷與考核整合表單
 * 對應 tasks.md T192: 整合履歷表單與責任判定
 * 當選擇 R02-R05 考核項目時，自動顯示責任判定查核表區塊
 */
import { ref, computed, watch, onMounted } from 'vue'
import { Document, Medal, Warning, DataAnalysis } from '@element-plus/icons-vue'
import { useAssessmentsStore, ASSESSMENT_CATEGORIES, R_TYPE_CODES } from '@/stores/assessments'
import { cloudApi } from '@/services/api'
import FaultResponsibilityChecklist from '@/components/assessments/FaultResponsibilityChecklist.vue'

const props = defineProps({
  initialData: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit'])

const assessmentsStore = useAssessmentsStore()

// 狀態
const formRef = ref()
const checklistRef = ref()
const searchLoading = ref(false)
const employeeOptions = ref([])
const responsibilityData = ref(null)

// 表單資料
const formData = ref({
  employee_id: null,
  department: '',
  event_date: '',
  event_time: '',
  event_location: '',
  train_number: '',
  event_title: '',
  event_description: '',
  data_source: '',
  assessment_code: '',
  fault_responsibility_data: null
})

const rules = {
  employee_id: [{ required: true, message: '請選擇員工', trigger: 'change' }],
  department: [{ required: true, message: '請選擇部門', trigger: 'change' }],
  event_date: [{ required: true, message: '請選擇事件日期', trigger: 'change' }],
  assessment_code: [{ required: true, message: '請選擇考核項目', trigger: 'change' }]
}

// 考核標準按類別分組
const groupedStandards = computed(() => {
  const groups = {}
  for (const std of assessmentsStore.standards) {
    if (!groups[std.category]) {
      groups[std.category] = []
    }
    groups[std.category].push(std)
  }
  return groups
})

// 選中的考核標準
const selectedStandard = computed(() => {
  if (!formData.value.assessment_code) return null
  return assessmentsStore.standards.find(s => s.code === formData.value.assessment_code)
})

// 是否為 R02-R05
const isRTypeCode = computed(() => {
  return R_TYPE_CODES.includes(formData.value.assessment_code)
})

// 計算分數
const calculatedPoints = computed(() => {
  if (!selectedStandard.value) return { actual: 0, final: 0 }

  const base = selectedStandard.value.base_points
  let actual = base
  let final = base

  if (isRTypeCode.value && responsibilityData.value?.coefficient) {
    actual = base * responsibilityData.value.coefficient
    final = actual
  }

  return { actual, final }
})

// 取得類別標籤
function getCategoryLabel(category) {
  return ASSESSMENT_CATEGORIES[category]?.label || category
}

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
  const emp = employeeOptions.value.find(e => e.id === formData.value.employee_id)
  if (emp?.current_department) {
    formData.value.department = emp.current_department
  }
}

// 考核代碼變更
function onAssessmentCodeChange() {
  // 如果不是 R 類，清除責任判定資料
  if (!isRTypeCode.value) {
    formData.value.fault_responsibility_data = null
    responsibilityData.value = null
  }
}

// 責任判定變更
function onResponsibilityChange(data) {
  responsibilityData.value = data
}

// 驗證
async function validate() {
  const valid = await formRef.value?.validate()
  if (!valid) return false

  // R02-R05 需要驗證責任判定
  if (isRTypeCode.value) {
    if (!formData.value.fault_responsibility_data) {
      return false
    }
  }

  return true
}

// 取得資料
function getData() {
  const data = { ...formData.value }

  if (isRTypeCode.value && checklistRef.value) {
    data.fault_responsibility_data = checklistRef.value.getData()
  }

  return data
}

// 提交
async function submit() {
  const valid = await validate()
  if (!valid) return false

  emit('submit', getData())
  return true
}

// 初始化
onMounted(async () => {
  // 載入考核標準
  if (!assessmentsStore.hasStandards) {
    await assessmentsStore.fetchStandards()
  }

  // 初始化資料
  if (props.initialData) {
    formData.value = { ...formData.value, ...props.initialData }
  }
})

defineExpose({ validate, getData, submit })
</script>

<style scoped>
.profile-with-assessment-form {
  padding: 16px;
}

.form-section {
  margin-bottom: 24px;
  padding: 20px;
  background: #fafafa;
  border-radius: 8px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.section-hint {
  font-weight: normal;
  font-size: 13px;
  color: #f56c6c;
}

.responsibility-section {
  background: #fff5f5;
  border: 1px solid #fde2e2;
}

.standard-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.standard-option .code {
  font-weight: bold;
  min-width: 50px;
}

.standard-option .name {
  flex: 1;
}

.standard-option .points {
  font-weight: bold;
}

.standard-option .points.bonus {
  color: #67c23a;
}

.standard-option .points.deduction {
  color: #f56c6c;
}

.selected-standard {
  margin-top: 16px;
}

.standard-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.standard-name {
  flex: 1;
  font-weight: bold;
}

.standard-points {
  font-size: 18px;
  font-weight: bold;
}

.standard-points.bonus {
  color: #67c23a;
}

.standard-points.deduction {
  color: #f56c6c;
}

.cumulative-hint {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 13px;
  color: #e6a23c;
}

.r-type-alert {
  margin-top: 16px;
}

.score-preview {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.preview-row {
  display: flex;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.preview-row:last-child {
  border-bottom: none;
}

.preview-row.final {
  background: #f5f7fa;
  font-weight: bold;
}

.preview-row .label {
  color: #666;
}

.preview-row .value {
  font-weight: 500;
}

.preview-row .value.bonus {
  color: #67c23a;
}

.preview-row .value.deduction {
  color: #f56c6c;
}
</style>
