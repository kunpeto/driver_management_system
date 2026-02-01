<template>
  <div class="pending-profiles-page">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>未結案專區</h1>
      <el-button :loading="loading" @click="handleRefresh">
        <el-icon><Refresh /></el-icon>
        重新載入
      </el-button>
    </div>

    <!-- 統計區 -->
    <PendingStatistics :stats="pendingStats" />

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

        <el-form-item v-if="isAdmin" label="部門">
          <el-select v-model="filters.department" clearable placeholder="全部部門">
            <el-option label="淡海" value="淡海" />
            <el-option label="安坑" value="安坑" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜尋</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 未結案列表 -->
    <el-card v-loading="loading">
      <el-table
        :data="profiles"
        stripe
        empty-text="目前沒有未結案的履歷"
        @row-click="handleRowClick"
      >
        <el-table-column prop="event_date" label="事件日期" width="120" sortable />
        <el-table-column label="員工" width="150">
          <template #default="{ row }">
            <span>{{ row.employee_name }}</span>
            <span class="employee-no">({{ row.employee_no }})</span>
          </template>
        </el-table-column>
        <el-table-column label="類型" width="120">
          <template #default="{ row }">
            <el-tag :type="PROFILE_TYPES[row.profile_type]?.color || 'info'" size="small">
              {{ PROFILE_TYPES[row.profile_type]?.label || row.profile_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="event_location" label="地點" width="120" />
        <el-table-column prop="event_title" label="標題" show-overflow-tooltip />
        <el-table-column label="等待天數" width="100">
          <template #default="{ row }">
            <span :class="getWaitingClass(row.event_date)">
              {{ calculateWaitingDays(row.event_date) }} 天
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              @click.stop="openUploadDialog(row)"
            >
              <el-icon><Upload /></el-icon>
              上傳 PDF
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分頁 -->
      <div v-if="profiles.length > 0" class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          :page-size="pagination.pageSize"
          :total="total"
          layout="total, prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- PDF 上傳對話框 -->
    <PdfUploadDialog
      v-model="showUploadDialog"
      :profile-id="selectedProfileId"
      @uploaded="handleUploaded"
    />
  </div>
</template>

<script setup>
/**
 * 未結案專區頁面
 * Phase 14 T193
 */
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Upload } from '@element-plus/icons-vue'
import { useProfilesStore } from '@/stores/profiles'
import { useAuthStore } from '@/stores/auth'
import PendingStatistics from '@/components/profiles/PendingStatistics.vue'
import PdfUploadDialog from '@/components/profiles/PdfUploadDialog.vue'

const profilesStore = useProfilesStore()
const authStore = useAuthStore()

// 狀態
const loading = ref(false)
const profiles = ref([])
const total = ref(0)
const pendingStats = ref({
  total: 0,
  by_type: {},
  oldest_pending_date: null,
  this_month_completed: 0,
  this_month_total: 0,
  completion_rate: 0
})

const filters = reactive({
  profile_type: null,
  department: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  skip: 0
})

const showUploadDialog = ref(false)
const selectedProfileId = ref(null)

// 履歷類型設定
const PROFILE_TYPES = {
  event_investigation: { label: '事件調查', color: 'danger' },
  personnel_interview: { label: '人員訪談', color: 'warning' },
  corrective_measures: { label: '矯正措施', color: 'success' },
  assessment_notice: { label: '考核通知', color: 'primary' }
}

// 計算屬性
const isAdmin = computed(() => authStore.isAdmin)

// 載入資料
async function loadData() {
  loading.value = true

  try {
    const params = {
      ...filters,
      skip: pagination.skip,
      limit: pagination.pageSize
    }

    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === '') {
        delete params[key]
      }
    })

    await profilesStore.fetchPendingProfiles(params)
    profiles.value = profilesStore.profiles
    total.value = profilesStore.total || profiles.value.length

    // 載入統計
    await profilesStore.fetchPendingStats(filters.department)
    pendingStats.value = profilesStore.pendingStats

  } catch (err) {
    ElMessage.error('載入資料失敗')
    console.error(err)
  } finally {
    loading.value = false
  }
}

// 搜尋
function handleSearch() {
  pagination.page = 1
  pagination.skip = 0
  loadData()
}

// 重置
function handleReset() {
  filters.profile_type = null
  filters.department = null
  pagination.page = 1
  pagination.skip = 0
  loadData()
}

// 重新載入
function handleRefresh() {
  loadData()
}

// 分頁變更
function handlePageChange(page) {
  pagination.page = page
  pagination.skip = (page - 1) * pagination.pageSize
  loadData()
}

// 點擊列
function handleRowClick(row) {
  // 可以跳轉到履歷詳情
  console.log('Row clicked:', row)
}

// 開啟上傳對話框
function openUploadDialog(profile) {
  selectedProfileId.value = profile.id
  showUploadDialog.value = true
}

// 上傳完成
function handleUploaded({ profileId }) {
  showUploadDialog.value = false
  ElMessage.success('上傳完成，履歷已從未結案列表移除')
  loadData()
}

// 計算等待天數
function calculateWaitingDays(eventDate) {
  if (!eventDate) return 0
  const event = new Date(eventDate)
  const today = new Date()
  const diffTime = today - event
  return Math.floor(diffTime / (1000 * 60 * 60 * 24))
}

// 取得等待天數樣式
function getWaitingClass(eventDate) {
  const days = calculateWaitingDays(eventDate)
  if (days > 14) return 'waiting-danger'
  if (days > 7) return 'waiting-warning'
  return 'waiting-normal'
}

// 初始化
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.pending-profiles-page {
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
  color: #303133;
}

.filter-card {
  margin-bottom: 20px;
}

.employee-no {
  color: #909399;
  font-size: 12px;
  margin-left: 4px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.waiting-normal {
  color: #67c23a;
}

.waiting-warning {
  color: #e6a23c;
  font-weight: 500;
}

.waiting-danger {
  color: #f56c6c;
  font-weight: 600;
}
</style>
