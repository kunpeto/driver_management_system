<template>
  <div class="profiles-page">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>履歷管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新增履歷
      </el-button>
    </div>

    <!-- 篩選區 -->
    <el-card class="filter-card">
      <el-form :inline="true" @submit.prevent="handleSearch">
        <el-form-item label="類型">
          <el-select v-model="filters.profile_type" clearable placeholder="全部類型">
            <el-option
              v-for="(config, key) in PROFILE_TYPES"
              :key="key"
              :label="config.label"
              :value="key"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="狀態">
          <el-select v-model="filters.conversion_status" clearable placeholder="全部狀態">
            <el-option
              v-for="(config, key) in CONVERSION_STATUS"
              :key="key"
              :label="config.label"
              :value="key"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="日期區間">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="開始日期"
            end-placeholder="結束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>

        <el-form-item label="關鍵字">
          <el-input v-model="filters.keyword" placeholder="搜尋描述、標題" clearable />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜尋</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 履歷列表 -->
    <el-card v-loading="profilesStore.loading">
      <el-table :data="profilesStore.profiles" stripe @row-click="handleRowClick">
        <el-table-column prop="event_date" label="事件日期" width="120" sortable />
        <el-table-column prop="employee_name" label="員工姓名" width="100" />
        <el-table-column label="類型" width="120">
          <template #default="{ row }">
            <el-tag :type="PROFILE_TYPES[row.profile_type]?.color || 'info'" size="small">
              {{ PROFILE_TYPES[row.profile_type]?.label || row.profile_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="狀態" width="100">
          <template #default="{ row }">
            <el-tag :type="CONVERSION_STATUS[row.conversion_status]?.color || 'info'" size="small">
              {{ CONVERSION_STATUS[row.conversion_status]?.label || row.conversion_status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="event_location" label="地點" width="120" />
        <el-table-column prop="train_number" label="車號" width="80" />
        <el-table-column prop="event_title" label="標題" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                v-if="row.profile_type === 'basic'"
                size="small"
                type="primary"
                @click.stop="openConvertDialog(row)"
              >
                轉換
              </el-button>
              <el-button
                v-if="row.profile_type !== 'basic'"
                size="small"
                type="success"
                :loading="profilesStore.generating"
                @click.stop="handleGenerateDocument(row)"
              >
                生成文件
              </el-button>
              <el-button size="small" @click.stop="openEditDialog(row)">編輯</el-button>
              <el-button size="small" type="danger" @click.stop="handleDelete(row)">刪除</el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分頁 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="profilesStore.pagination.page"
          :page-size="profilesStore.pagination.pageSize"
          :total="profilesStore.total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增履歷對話框 -->
    <el-dialog v-model="showCreateDialog" title="新增履歷" width="600px">
      <BasicProfileForm
        v-if="showCreateDialog"
        @submit="handleCreate"
        @cancel="showCreateDialog = false"
      />
    </el-dialog>

    <!-- 編輯履歷對話框 -->
    <el-dialog v-model="showEditDialog" title="編輯履歷" width="600px">
      <BasicProfileForm
        v-if="showEditDialog && selectedProfile"
        :profile="selectedProfile"
        @submit="handleUpdate"
        @cancel="showEditDialog = false"
      />
    </el-dialog>

    <!-- 類型轉換對話框 -->
    <ConversionDialog
      v-model="showConvertDialog"
      :profile="selectedProfile"
      @converted="handleConverted"
    />
  </div>
</template>

<script setup>
/**
 * 履歷列表頁面
 * 對應 tasks.md T150: 建立履歷列表頁面
 */
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useProfilesStore, PROFILE_TYPES, CONVERSION_STATUS } from '@/stores/profiles'
import BasicProfileForm from '@/components/profiles/BasicProfileForm.vue'
import ConversionDialog from '@/components/profiles/ConversionDialog.vue'

const profilesStore = useProfilesStore()

// 對話框狀態
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showConvertDialog = ref(false)
const selectedProfile = ref(null)

// 篩選條件
const filters = ref({
  profile_type: null,
  conversion_status: null,
  keyword: ''
})
const dateRange = ref(null)

// 載入資料
onMounted(() => {
  profilesStore.fetchProfiles()
})

// 監聽日期範圍變化
watch(dateRange, (val) => {
  if (val) {
    filters.value.date_from = val[0]
    filters.value.date_to = val[1]
  } else {
    filters.value.date_from = null
    filters.value.date_to = null
  }
})

// 搜尋
function handleSearch() {
  profilesStore.setFilters(filters.value)
}

// 重置
function handleReset() {
  filters.value = {
    profile_type: null,
    conversion_status: null,
    keyword: ''
  }
  dateRange.value = null
  profilesStore.resetFilters()
  profilesStore.fetchProfiles()
}

// 點擊行
function handleRowClick(row) {
  selectedProfile.value = row
}

// 新增
async function handleCreate(data) {
  try {
    await profilesStore.createProfile(data)
    ElMessage.success('履歷建立成功')
    showCreateDialog.value = false
  } catch (err) {
    ElMessage.error(err.message || '建立失敗')
  }
}

// 更新
async function handleUpdate(data) {
  try {
    await profilesStore.updateProfile(selectedProfile.value.id, data)
    ElMessage.success('履歷更新成功')
    showEditDialog.value = false
  } catch (err) {
    ElMessage.error(err.message || '更新失敗')
  }
}

// 刪除
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm('確定要刪除此履歷嗎？', '確認刪除', {
      confirmButtonText: '確定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await profilesStore.deleteProfile(row.id)
    ElMessage.success('履歷已刪除')
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.message || '刪除失敗')
    }
  }
}

// 開啟編輯對話框
function openEditDialog(row) {
  selectedProfile.value = row
  showEditDialog.value = true
}

// 開啟轉換對話框
function openConvertDialog(row) {
  selectedProfile.value = row
  showConvertDialog.value = true
}

// 轉換完成
function handleConverted() {
  showConvertDialog.value = false
  profilesStore.fetchProfiles()
}

// 生成文件
async function handleGenerateDocument(row) {
  try {
    await profilesStore.generateDocument(row.id)
    ElMessage.success('文件生成成功')
  } catch (err) {
    ElMessage.error(err.message || '文件生成失敗')
  }
}

// 分頁
function handlePageChange(page) {
  profilesStore.setPage(page)
}
</script>

<style scoped>
.profiles-page {
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

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
