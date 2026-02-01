<template>
  <div class="route-standard-times">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>勤務標準時間管理</h1>
      <p class="subtitle">管理各部門勤務項目的標準分鐘數，用於計算駕駛時數</p>
    </div>

    <!-- 工具列 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-select
          v-model="filters.department"
          placeholder="選擇部門"
          clearable
          @change="handleFilterChange"
        >
          <el-option label="淡海" value="淡海" />
          <el-option label="安坑" value="安坑" />
        </el-select>

        <el-input
          v-model="filters.search"
          placeholder="搜尋勤務代碼或名稱"
          clearable
          style="width: 200px"
          @clear="handleFilterChange"
          @keyup.enter="handleFilterChange"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <div class="toolbar-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增勤務
        </el-button>

        <el-button @click="showImportDialog">
          <el-icon><Upload /></el-icon>
          匯入 Excel
        </el-button>
      </div>
    </div>

    <!-- 資料表格 -->
    <el-table
      v-loading="store.loading"
      :data="store.routeStandardTimes"
      stripe
      border
    >
      <el-table-column prop="department" label="部門" width="100" />
      <el-table-column prop="route_code" label="勤務代碼" width="150" />
      <el-table-column prop="route_name" label="勤務名稱" min-width="200" />
      <el-table-column label="標準時間" width="120" align="center">
        <template #default="{ row }">
          {{ formatMinutes(row.standard_minutes) }}
        </template>
      </el-table-column>
      <el-table-column prop="description" label="說明" min-width="150" />
      <el-table-column label="狀態" width="80" align="center">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
            {{ row.is_active ? '啟用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150" align="center" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" link size="small" @click="showEditDialog(row)">
            編輯
          </el-button>
          <el-button type="danger" link size="small" @click="handleDelete(row)">
            刪除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分頁 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="store.routeStandardTimesTotal"
        :page-sizes="[20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadData"
        @size-change="loadData"
      />
    </div>

    <!-- 新增/編輯對話框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '編輯勤務標準時間' : '新增勤務標準時間'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item v-if="!isEdit" label="部門" prop="department">
          <el-select v-model="formData.department" placeholder="選擇部門">
            <el-option label="淡海" value="淡海" />
            <el-option label="安坑" value="安坑" />
          </el-select>
        </el-form-item>

        <el-form-item v-if="!isEdit" label="勤務代碼" prop="route_code">
          <el-input v-model="formData.route_code" placeholder="如 0905G" />
        </el-form-item>

        <el-form-item label="勤務名稱" prop="route_name">
          <el-input v-model="formData.route_name" placeholder="如 早班 09:05 出發" />
        </el-form-item>

        <el-form-item label="標準分鐘數" prop="standard_minutes">
          <el-input-number
            v-model="formData.standard_minutes"
            :min="0"
            :max="1440"
            controls-position="right"
          />
          <span class="ml-2 text-gray-500">
            ({{ formatMinutes(formData.standard_minutes) }})
          </span>
        </el-form-item>

        <el-form-item label="說明" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="2"
            placeholder="選填"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="store.saving" @click="handleSubmit">
          {{ isEdit ? '更新' : '建立' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 匯入對話框 -->
    <el-dialog v-model="importDialogVisible" title="匯入勤務標準時間" width="500px">
      <el-form label-width="100px">
        <el-form-item label="目標部門" required>
          <el-select v-model="importDepartment" placeholder="選擇部門">
            <el-option label="淡海" value="淡海" />
            <el-option label="安坑" value="安坑" />
          </el-select>
        </el-form-item>

        <el-form-item label="Excel 檔案" required>
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls"
            :on-change="handleFileChange"
          >
            <el-button type="primary">選擇檔案</el-button>
            <template #tip>
              <div class="el-upload__tip">
                僅支援 .xlsx 或 .xls 格式
              </div>
            </template>
          </el-upload>
        </el-form-item>

        <el-form-item label="更新模式">
          <el-checkbox v-model="updateExisting">
            覆蓋已存在的勤務代碼
          </el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="importDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="store.saving"
          :disabled="!importFile || !importDepartment"
          @click="handleImport"
        >
          開始匯入
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Upload } from '@element-plus/icons-vue'
import { useDrivingStatsStore } from '@/stores/drivingStats'

const store = useDrivingStatsStore()

// 篩選條件
const filters = reactive({
  department: null,
  search: ''
})

// 分頁
const pagination = reactive({
  page: 1,
  pageSize: 50
})

// 對話框
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const formData = reactive({
  id: null,
  department: '',
  route_code: '',
  route_name: '',
  standard_minutes: 480,
  description: ''
})

const formRules = {
  department: [{ required: true, message: '請選擇部門', trigger: 'change' }],
  route_code: [{ required: true, message: '請輸入勤務代碼', trigger: 'blur' }],
  route_name: [{ required: true, message: '請輸入勤務名稱', trigger: 'blur' }],
  standard_minutes: [{ required: true, message: '請輸入標準分鐘數', trigger: 'blur' }]
}

// 匯入對話框
const importDialogVisible = ref(false)
const importDepartment = ref('')
const importFile = ref(null)
const updateExisting = ref(true)

// 載入資料
async function loadData() {
  await store.loadRouteStandardTimes({
    department: filters.department,
    search: filters.search,
    skip: (pagination.page - 1) * pagination.pageSize,
    limit: pagination.pageSize
  })
}

// 篩選變更
function handleFilterChange() {
  pagination.page = 1
  loadData()
}

// 格式化分鐘數
function formatMinutes(minutes) {
  if (!minutes) return '0:00'
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${hours}:${mins.toString().padStart(2, '0')}`
}

// 顯示新增對話框
function showCreateDialog() {
  isEdit.value = false
  Object.assign(formData, {
    id: null,
    department: filters.department || '',
    route_code: '',
    route_name: '',
    standard_minutes: 480,
    description: ''
  })
  dialogVisible.value = true
}

// 顯示編輯對話框
function showEditDialog(row) {
  isEdit.value = true
  Object.assign(formData, {
    id: row.id,
    department: row.department,
    route_code: row.route_code,
    route_name: row.route_name,
    standard_minutes: row.standard_minutes,
    description: row.description || ''
  })
  dialogVisible.value = true
}

// 提交表單
async function handleSubmit() {
  try {
    await formRef.value.validate()

    if (isEdit.value) {
      await store.updateRouteStandardTime(formData.id, {
        route_name: formData.route_name,
        standard_minutes: formData.standard_minutes,
        description: formData.description
      })
      ElMessage.success('更新成功')
    } else {
      await store.createRouteStandardTime(formData)
      ElMessage.success('建立成功')
    }

    dialogVisible.value = false
    loadData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(store.error || '操作失敗')
    }
  }
}

// 刪除
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `確定要刪除勤務「${row.route_code}」嗎？`,
      '刪除確認',
      { type: 'warning' }
    )

    await store.deleteRouteStandardTime(row.id)
    ElMessage.success('刪除成功')
    loadData()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(store.error || '刪除失敗')
    }
  }
}

// 顯示匯入對話框
function showImportDialog() {
  importDepartment.value = filters.department || ''
  importFile.value = null
  updateExisting.value = true
  importDialogVisible.value = true
}

// 檔案選擇
function handleFileChange(file) {
  importFile.value = file.raw
}

// 匯入
async function handleImport() {
  try {
    const result = await store.importRouteStandardTimes(
      importFile.value,
      importDepartment.value,
      updateExisting.value
    )

    if (result.errors.length > 0) {
      ElMessage.warning(`匯入完成，但有 ${result.errors.length} 筆錯誤`)
    } else {
      ElMessage.success(`匯入成功！新增 ${result.created} 筆，更新 ${result.updated} 筆`)
    }

    importDialogVisible.value = false
    loadData()
  } catch (err) {
    ElMessage.error(store.error || '匯入失敗')
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.route-standard-times {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.page-header .subtitle {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.toolbar-right {
  display: flex;
  gap: 12px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.ml-2 {
  margin-left: 8px;
}

.text-gray-500 {
  color: #909399;
}
</style>
