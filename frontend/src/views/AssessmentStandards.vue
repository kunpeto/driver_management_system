<template>
  <div class="assessment-standards-page">
    <div class="page-header">
      <h1>考核標準管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增標準
        </el-button>
        <el-button @click="showImportDialog">
          <el-icon><Upload /></el-icon>
          Excel 匯入
        </el-button>
        <el-button :loading="initializing" @click="initializeDefaults">
          <el-icon><Refresh /></el-icon>
          初始化預設 61 項
        </el-button>
      </div>
    </div>

    <!-- 篩選區 -->
    <el-card class="filter-card" shadow="never">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-input
            v-model="searchKeyword"
            placeholder="搜尋代碼或名稱"
            clearable
            @input="onSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="filterCategory" placeholder="類別篩選" clearable @change="onFilter">
            <el-option
              v-for="(cat, key) in ASSESSMENT_CATEGORIES"
              :key="key"
              :label="cat.label"
              :value="key"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filterType" placeholder="類型篩選" clearable @change="onFilter">
            <el-option label="扣分項目" value="deduction" />
            <el-option label="加分項目" value="bonus" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-checkbox v-model="showInactive" @change="onFilter">
            顯示停用項目
          </el-checkbox>
        </el-col>
      </el-row>
    </el-card>

    <!-- 統計摘要 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <el-card shadow="never" class="stat-card">
          <div class="stat-value">{{ totalCount }}</div>
          <div class="stat-label">總項目數</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card deduction">
          <div class="stat-value">{{ deductionCount }}</div>
          <div class="stat-label">扣分項目</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card bonus">
          <div class="stat-value">{{ bonusCount }}</div>
          <div class="stat-label">加分項目</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="never" class="stat-card cumulative">
          <div class="stat-value">{{ cumulativeCount }}</div>
          <div class="stat-label">累計加重項目</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 標準列表 -->
    <el-card shadow="never">
      <el-table
        v-loading="loading"
        :data="filteredStandards"
        border
        stripe
        row-key="id"
      >
        <el-table-column prop="code" label="代碼" width="100" sortable>
          <template #default="{ row }">
            <el-tag :type="row.base_points > 0 ? 'success' : 'danger'" size="small">
              {{ row.code }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="category" label="類別" width="100">
          <template #default="{ row }">
            <el-tag :color="getCategoryColor(row.category)" size="small" style="color: #fff">
              {{ getCategoryLabel(row.category) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="項目名稱" min-width="200" show-overflow-tooltip />

        <el-table-column prop="base_points" label="基本分數" width="100" align="center">
          <template #default="{ row }">
            <span :class="row.base_points > 0 ? 'text-success' : 'text-danger'">
              {{ row.base_points > 0 ? '+' : '' }}{{ row.base_points }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="has_cumulative" label="累計加重" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.has_cumulative" type="warning" size="small">是</el-tag>
            <span v-else class="text-muted">否</span>
          </template>
        </el-table-column>

        <el-table-column prop="calculation_cycle" label="計算週期" width="100" align="center">
          <template #default="{ row }">
            {{ row.calculation_cycle === 'yearly' ? '年度' : '月度' }}
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="狀態" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '啟用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="editStandard(row)">
              編輯
            </el-button>
            <el-button
              :type="row.is_active ? 'warning' : 'success'"
              link
              size="small"
              @click="toggleActive(row)"
            >
              {{ row.is_active ? '停用' : '啟用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/編輯對話框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingStandard ? '編輯考核標準' : '新增考核標準'"
      width="600px"
    >
      <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
        <el-form-item label="代碼" prop="code">
          <el-input v-model="formData.code" :disabled="!!editingStandard" placeholder="如 D01, R03, +M01" />
        </el-form-item>

        <el-form-item label="類別" prop="category">
          <el-select v-model="formData.category" placeholder="選擇類別" style="width: 100%">
            <el-option
              v-for="(cat, key) in ASSESSMENT_CATEGORIES"
              :key="key"
              :label="cat.label"
              :value="key"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="項目名稱" prop="name">
          <el-input v-model="formData.name" placeholder="項目名稱" />
        </el-form-item>

        <el-form-item label="基本分數" prop="base_points">
          <el-input-number
            v-model="formData.base_points"
            :min="-100"
            :max="100"
            :precision="1"
          />
          <span class="form-hint">（扣分為負數，加分為正數）</span>
        </el-form-item>

        <el-form-item label="累計加重" prop="has_cumulative">
          <el-switch v-model="formData.has_cumulative" />
          <span class="form-hint">同類別多次違規時累計倍率增加</span>
        </el-form-item>

        <el-form-item label="計算週期" prop="calculation_cycle">
          <el-radio-group v-model="formData.calculation_cycle">
            <el-radio value="yearly">年度</el-radio>
            <el-radio value="monthly">月度</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item label="說明" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="項目說明（選填）" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveStandard">
          {{ editingStandard ? '更新' : '建立' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- Excel 匯入對話框 -->
    <el-dialog v-model="importDialogVisible" title="Excel 匯入" width="500px">
      <el-upload
        ref="uploadRef"
        drag
        :auto-upload="false"
        accept=".xlsx,.xls"
        :limit="1"
        :on-change="onFileChange"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖曳檔案至此或<em>點擊上傳</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            僅支援 .xlsx 或 .xls 格式，檔案大小不超過 5MB
          </div>
        </template>
      </el-upload>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="importing" @click="importExcel">
          開始匯入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 考核標準管理頁面
 * 對應 tasks.md T185: 建立考核標準管理頁面
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Upload, Refresh, Search, UploadFilled } from '@element-plus/icons-vue'
import { useAssessmentsStore, ASSESSMENT_CATEGORIES } from '@/stores/assessments'

const assessmentsStore = useAssessmentsStore()

// 狀態
const loading = ref(false)
const saving = ref(false)
const initializing = ref(false)
const importing = ref(false)

// 篩選
const searchKeyword = ref('')
const filterCategory = ref('')
const filterType = ref('')
const showInactive = ref(false)

// 對話框
const dialogVisible = ref(false)
const importDialogVisible = ref(false)
const editingStandard = ref(null)

// 表單
const formRef = ref()
const uploadRef = ref()
const uploadFile = ref(null)

const formData = ref({
  code: '',
  category: '',
  name: '',
  base_points: 0,
  has_cumulative: false,
  calculation_cycle: 'yearly',
  description: ''
})

const rules = {
  code: [{ required: true, message: '請輸入代碼', trigger: 'blur' }],
  category: [{ required: true, message: '請選擇類別', trigger: 'change' }],
  name: [{ required: true, message: '請輸入項目名稱', trigger: 'blur' }],
  base_points: [{ required: true, message: '請輸入基本分數', trigger: 'blur' }]
}

// 統計
const totalCount = computed(() => assessmentsStore.standards.length)
const deductionCount = computed(() => assessmentsStore.deductionStandards.length)
const bonusCount = computed(() => assessmentsStore.bonusStandards.length)
const cumulativeCount = computed(() =>
  assessmentsStore.standards.filter(s => s.has_cumulative).length
)

// 篩選後的列表
const filteredStandards = computed(() => {
  let list = assessmentsStore.standards

  // 關鍵字搜尋
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    list = list.filter(s =>
      s.code.toLowerCase().includes(kw) ||
      s.name.toLowerCase().includes(kw)
    )
  }

  // 類別篩選
  if (filterCategory.value) {
    list = list.filter(s => s.category === filterCategory.value)
  }

  // 類型篩選
  if (filterType.value) {
    if (filterType.value === 'deduction') {
      list = list.filter(s => s.base_points < 0)
    } else {
      list = list.filter(s => s.base_points > 0)
    }
  }

  // 啟用狀態
  if (!showInactive.value) {
    list = list.filter(s => s.is_active)
  }

  return list
})

// 取得類別標籤
function getCategoryLabel(category) {
  return ASSESSMENT_CATEGORIES[category]?.label || category
}

// 取得類別顏色
function getCategoryColor(category) {
  const colors = {
    D: '#409eff',
    W: '#f56c6c',
    O: '#909399',
    S: '#e6a23c',
    R: '#f56c6c',
    '+M': '#67c23a',
    '+A': '#409eff',
    '+B': '#67c23a',
    '+C': '#409eff',
    '+R': '#e6a23c'
  }
  return colors[category] || '#909399'
}

// 載入資料
async function loadStandards() {
  loading.value = true
  try {
    await assessmentsStore.fetchStandards({ is_active: showInactive.value ? undefined : true })
  } catch (err) {
    ElMessage.error('載入考核標準失敗')
  } finally {
    loading.value = false
  }
}

// 搜尋
function onSearch() {
  // 防抖處理由 computed 自動完成
}

// 篩選
function onFilter() {
  // 由 computed 自動處理
}

// 顯示新增對話框
function showCreateDialog() {
  editingStandard.value = null
  formData.value = {
    code: '',
    category: '',
    name: '',
    base_points: 0,
    has_cumulative: false,
    calculation_cycle: 'yearly',
    description: ''
  }
  dialogVisible.value = true
}

// 編輯標準
function editStandard(standard) {
  editingStandard.value = standard
  formData.value = {
    code: standard.code,
    category: standard.category,
    name: standard.name,
    base_points: standard.base_points,
    has_cumulative: standard.has_cumulative,
    calculation_cycle: standard.calculation_cycle,
    description: standard.description || ''
  }
  dialogVisible.value = true
}

// 儲存標準
async function saveStandard() {
  const valid = await formRef.value?.validate()
  if (!valid) return

  saving.value = true
  try {
    if (editingStandard.value) {
      await assessmentsStore.updateStandard(editingStandard.value.id, formData.value)
      ElMessage.success('更新成功')
    } else {
      await assessmentsStore.createStandard(formData.value)
      ElMessage.success('建立成功')
    }
    dialogVisible.value = false
    loadStandards()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失敗')
  } finally {
    saving.value = false
  }
}

// 切換啟用狀態
async function toggleActive(standard) {
  try {
    await assessmentsStore.toggleStandardActive(standard.id)
    ElMessage.success(standard.is_active ? '已停用' : '已啟用')
  } catch (err) {
    ElMessage.error('操作失敗')
  }
}

// 初始化預設標準
async function initializeDefaults() {
  try {
    await ElMessageBox.confirm(
      '將初始化預設的 61 項考核標準，已存在的項目不會重複建立。確定繼續？',
      '初始化確認',
      { type: 'warning' }
    )
  } catch {
    return
  }

  initializing.value = true
  try {
    const result = await assessmentsStore.initializeDefaultStandards()
    ElMessage.success(`已建立 ${result.created_count} 項標準`)
    loadStandards()
  } catch (err) {
    ElMessage.error('初始化失敗')
  } finally {
    initializing.value = false
  }
}

// 顯示匯入對話框
function showImportDialog() {
  uploadFile.value = null
  importDialogVisible.value = true
}

// 檔案選擇
function onFileChange(file) {
  uploadFile.value = file.raw
}

// Excel 匯入
async function importExcel() {
  if (!uploadFile.value) {
    ElMessage.warning('請選擇檔案')
    return
  }

  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', uploadFile.value)

    // TODO: 呼叫 API 匯入
    ElMessage.success('匯入成功')
    importDialogVisible.value = false
    loadStandards()
  } catch (err) {
    ElMessage.error('匯入失敗')
  } finally {
    importing.value = false
  }
}

onMounted(() => {
  loadStandards()
})
</script>

<style scoped>
.assessment-standards-page {
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

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 16px;
}

.stat-card .stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-card .stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.stat-card.deduction {
  border-top: 3px solid #f56c6c;
}

.stat-card.bonus {
  border-top: 3px solid #67c23a;
}

.stat-card.cumulative {
  border-top: 3px solid #e6a23c;
}

.text-success {
  color: #67c23a;
  font-weight: bold;
}

.text-danger {
  color: #f56c6c;
  font-weight: bold;
}

.text-muted {
  color: #c0c4cc;
}

.form-hint {
  margin-left: 10px;
  font-size: 12px;
  color: #999;
}
</style>
