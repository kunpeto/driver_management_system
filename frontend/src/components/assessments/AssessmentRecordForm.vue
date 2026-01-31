<template>
  <div class="assessment-record-form">
    <!-- 主表單區域（可捲動） -->
    <div class="form-scroll-area">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      :disabled="loading"
    >
      <!-- 員工選擇 -->
      <el-form-item label="員工" prop="employee_id">
        <el-select
          v-model="formData.employee_id"
          filterable
          remote
          :remote-method="searchEmployees"
          :loading="searchLoading"
          placeholder="搜尋員工（編號或姓名）"
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

      <!-- 事件日期 -->
      <el-form-item label="事件日期" prop="record_date">
        <el-date-picker
          v-model="formData.record_date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="選擇日期"
          style="width: 100%"
        />
      </el-form-item>

      <!-- 考核項目選擇 -->
      <el-form-item label="考核項目" prop="standard_code">
        <el-select
          v-model="formData.standard_code"
          filterable
          placeholder="搜尋考核項目"
          style="width: 100%"
          @change="onStandardChange"
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
      <div v-if="selectedStandard" class="selected-standard-info">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="代碼">
            <el-tag :type="selectedStandard.base_points > 0 ? 'success' : 'danger'" size="small">
              {{ selectedStandard.code }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="類別">
            {{ getCategoryLabel(selectedStandard.category) }}
          </el-descriptions-item>
          <el-descriptions-item label="基本分數">
            <span :class="selectedStandard.base_points > 0 ? 'text-success' : 'text-danger'">
              {{ selectedStandard.base_points > 0 ? '+' : '' }}{{ selectedStandard.base_points }} 分
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="項目名稱" :span="3">
            {{ selectedStandard.name }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedStandard.has_cumulative" label="累計加重" :span="3">
            <el-tag type="warning" size="small">此項目適用累計加重機制</el-tag>
            <span v-if="cumulativeInfo" style="margin-left: 10px">
              本年度第 {{ cumulativeInfo.count + 1 }} 次，累計倍率 ×{{ cumulativeMultiplier.toFixed(1) }}
            </span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- R02-R05 責任判定提示 -->
      <div v-if="isRTypeCode" class="r-type-notice">
        <el-alert
          title="此為責任類項目（R02-R05），需填寫責任判定查核表"
          type="warning"
          :closable="false"
          show-icon
        />
      </div>

      <!-- 事件描述 -->
      <el-form-item label="事件描述">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="3"
          placeholder="描述事件經過"
        />
      </el-form-item>

      <!-- R02-R05 責任判定查核表 -->
      <div v-if="isRTypeCode" class="responsibility-section">
        <el-divider content-position="left">
          <el-icon><Warning /></el-icon>
          責任判定查核表
        </el-divider>

        <FaultResponsibilityChecklist
          ref="checklistRef"
          v-model="formData.fault_responsibility_data"
          :base-points="selectedStandard?.base_points || 0"
          :cumulative-count="(cumulativeInfo?.count || 0) + 1"
          @responsibility-change="onResponsibilityChange"
        />
      </div>

      <!-- 關聯履歷 -->
      <el-form-item v-if="profileId" label="關聯履歷">
        <el-tag type="info">履歷 ID: {{ profileId }}</el-tag>
      </el-form-item>
    </el-form>
    </div>

    <!-- 分數計算預覽 - 吸附底部 -->
    <div v-if="selectedStandard" class="score-calculation-sticky">
      <div class="calculation-header">
        <el-icon><Coin /></el-icon>
        <span>分數計算預覽</span>
      </div>

      <div class="calculation-body">
        <div class="calc-item">
          <span class="calc-label">基本分</span>
          <span class="calc-value">{{ selectedStandard.base_points }}</span>
        </div>

        <template v-if="isRTypeCode && responsibilityData">
          <div class="calc-operator">×</div>
          <div class="calc-item">
            <span class="calc-label">責任係數</span>
            <span class="calc-value">{{ responsibilityData.coefficient || 0 }}</span>
          </div>
        </template>

        <template v-if="selectedStandard.has_cumulative && cumulativeInfo">
          <div class="calc-operator">×</div>
          <div class="calc-item">
            <span class="calc-label">累計倍率</span>
            <span class="calc-value">{{ cumulativeMultiplier.toFixed(1) }}</span>
          </div>
        </template>

        <div class="calc-operator">=</div>
        <div class="calc-item final">
          <span class="calc-label">最終分數</span>
          <span class="calc-value" :class="finalPoints > 0 ? 'positive' : 'negative'">
            {{ finalPoints > 0 ? '+' : '' }}{{ finalPoints.toFixed(1) }} 分
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 考核記錄表單元件
 * 對應 tasks.md T187: 建立考核記錄表單元件
 */
import { ref, computed, watch, onMounted } from 'vue'
import { Warning, Coin } from '@element-plus/icons-vue'
import { useAssessmentsStore, ASSESSMENT_CATEGORIES, R_TYPE_CODES } from '@/stores/assessments'
import FaultResponsibilityChecklist from './FaultResponsibilityChecklist.vue'
import { cloudApi } from '@/services/api'

const props = defineProps({
  record: {
    type: Object,
    default: null
  },
  profileId: {
    type: Number,
    default: null
  },
  employeeId: {
    type: Number,
    default: null
  },
  eventDate: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const assessmentsStore = useAssessmentsStore()
const formRef = ref()
const checklistRef = ref()
const loading = ref(false)
const searchLoading = ref(false)

// 員工選項
const employeeOptions = ref([])

// 累計資訊
const cumulativeInfo = ref(null)

// 責任判定資料
const responsibilityData = ref(null)

// 表單資料
const formData = ref({
  employee_id: null,
  record_date: '',
  standard_code: '',
  description: '',
  profile_id: null,
  fault_responsibility_data: null
})

const rules = {
  employee_id: [{ required: true, message: '請選擇員工', trigger: 'change' }],
  record_date: [{ required: true, message: '請選擇事件日期', trigger: 'change' }],
  standard_code: [{ required: true, message: '請選擇考核項目', trigger: 'change' }]
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
  if (!formData.value.standard_code) return null
  return assessmentsStore.standards.find(s => s.code === formData.value.standard_code)
})

// 是否為 R02-R05
const isRTypeCode = computed(() => {
  return R_TYPE_CODES.includes(formData.value.standard_code)
})

// 累計倍率
const cumulativeMultiplier = computed(() => {
  const count = (cumulativeInfo.value?.count || 0) + 1
  return 1.0 + 0.5 * (count - 1)
})

// 實際分數（考慮責任係數）
const actualPoints = computed(() => {
  if (!selectedStandard.value) return 0
  const base = selectedStandard.value.base_points
  if (isRTypeCode.value && responsibilityData.value?.coefficient) {
    return base * responsibilityData.value.coefficient
  }
  return base
})

// 最終分數
const finalPoints = computed(() => {
  let points = actualPoints.value
  if (selectedStandard.value?.has_cumulative && cumulativeInfo.value) {
    points *= cumulativeMultiplier.value
  }
  return points
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
  loadCumulativeInfo()
}

// 考核項目變更
function onStandardChange() {
  loadCumulativeInfo()
  // 重置責任判定資料
  if (!isRTypeCode.value) {
    formData.value.fault_responsibility_data = null
    responsibilityData.value = null
  }
}

// 載入累計資訊
async function loadCumulativeInfo() {
  if (!formData.value.employee_id || !formData.value.standard_code) {
    cumulativeInfo.value = null
    return
  }

  const std = selectedStandard.value
  if (!std?.has_cumulative) {
    cumulativeInfo.value = null
    return
  }

  try {
    const year = formData.value.record_date
      ? new Date(formData.value.record_date).getFullYear()
      : new Date().getFullYear()

    // 取得該類別累計次數
    const response = await cloudApi.get('/api/assessment-records/cumulative-count', {
      params: {
        employee_id: formData.value.employee_id,
        year: year,
        category: std.category
      }
    })
    cumulativeInfo.value = response.data
  } catch (err) {
    console.error('載入累計資訊失敗:', err)
    cumulativeInfo.value = { count: 0 }
  }
}

// 責任判定變更
function onResponsibilityChange(data) {
  responsibilityData.value = data
}

// 初始化
onMounted(async () => {
  // 載入考核標準
  if (!assessmentsStore.hasStandards) {
    await assessmentsStore.fetchStandards()
  }

  // 初始化表單資料
  if (props.record) {
    formData.value = {
      employee_id: props.record.employee_id,
      record_date: props.record.record_date,
      standard_code: props.record.standard_code,
      description: props.record.description || '',
      profile_id: props.record.profile_id,
      fault_responsibility_data: props.record.fault_responsibility || null
    }
  } else {
    if (props.employeeId) {
      formData.value.employee_id = props.employeeId
    }
    if (props.eventDate) {
      formData.value.record_date = props.eventDate
    }
    if (props.profileId) {
      formData.value.profile_id = props.profileId
    }
  }
})

// 驗證
async function validate() {
  const valid = await formRef.value?.validate()
  if (!valid) return false

  // R02-R05 需要驗證責任判定
  if (isRTypeCode.value && checklistRef.value) {
    const checklistValid = await checklistRef.value.validate()
    if (!checklistValid) return false
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
  if (!valid) return

  emit('submit', getData())
}

defineExpose({ validate, getData, submit })
</script>

<style scoped>
.assessment-record-form {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 70vh;
}

.form-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 10px;
}

.selected-standard-info {
  margin: 16px 0;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 4px;
}

.r-type-notice {
  margin: 16px 0;
}

.responsibility-section {
  margin-top: 20px;
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

/* 吸附底部的分數計算預覽 */
.score-calculation-sticky {
  position: sticky;
  bottom: 0;
  background: linear-gradient(180deg, #f0f9ff 0%, #e8f4fd 100%);
  border-top: 2px solid #409eff;
  padding: 12px 20px;
  margin-top: auto;
  box-shadow: 0 -4px 12px rgba(64, 158, 255, 0.15);
}

.calculation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #409eff;
  margin-bottom: 10px;
  font-size: 14px;
}

.calculation-body {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.calc-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  background: #fff;
  border-radius: 8px;
  min-width: 80px;
}

.calc-item.final {
  background: #409eff;
  color: #fff;
  min-width: 120px;
}

.calc-item.final .calc-label {
  color: rgba(255, 255, 255, 0.85);
}

.calc-item.final .calc-value {
  color: #fff;
}

.calc-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.calc-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.calc-value.positive {
  color: #67c23a;
}

.calc-value.negative {
  color: #f56c6c;
}

.calc-operator {
  font-size: 18px;
  font-weight: bold;
  color: #909399;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}
</style>
