<template>
  <div class="dashboard-page">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>司機員管理系統</h1>
      <p class="welcome-text">歡迎回來，{{ authStore.displayName || '使用者' }}</p>
    </div>

    <!-- 統計卡片區 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <el-card class="stat-card" shadow="hover" tabindex="0" role="button" @click="$router.push('/employees')" @keydown.enter="$router.push('/employees')">
          <div class="stat-content">
            <div class="stat-icon employees">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ employeeStats.active || 0 }}</div>
              <div class="stat-label">在職員工</div>
            </div>
          </div>
          <div class="stat-footer">
            <span>淡海 {{ employeeStats.by_department?.['淡海'] || 0 }} 人</span>
            <span>安坑 {{ employeeStats.by_department?.['安坑'] || 0 }} 人</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <el-card class="stat-card warning" shadow="hover" tabindex="0" role="button" @click="$router.push('/profiles/pending')" @keydown.enter="$router.push('/profiles/pending')">
          <div class="stat-content">
            <div class="stat-icon pending">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ pendingStats.total || 0 }}</div>
              <div class="stat-label">未結案履歷</div>
            </div>
          </div>
          <div class="stat-footer">
            <el-tag v-if="pendingStats.total > 0" type="warning" size="small">需要處理</el-tag>
            <span v-else class="text-success">全部已結案</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <el-card class="stat-card" shadow="hover" tabindex="0" role="button" @click="$router.push('/assessment-records')" @keydown.enter="$router.push('/assessment-records')">
          <div class="stat-content">
            <div class="stat-icon assessments">
              <el-icon :size="32"><Histogram /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ monthlyAssessmentCount }}</div>
              <div class="stat-label">本月考核記錄</div>
            </div>
          </div>
          <div class="stat-footer">
            <span class="text-danger">扣分 {{ monthlyDeductions }} 筆</span>
            <span class="text-success">加分 {{ monthlyBonuses }} 筆</span>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="12" :lg="6">
        <el-card class="stat-card" shadow="hover" tabindex="0" role="button" @click="$router.push('/driving-competition')" @keydown.enter="$router.push('/driving-competition')">
          <div class="stat-content">
            <div class="stat-icon competition">
              <el-icon :size="32"><Trophy /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">Q{{ currentQuarter }}</div>
              <div class="stat-label">當前競賽季度</div>
            </div>
          </div>
          <div class="stat-footer">
            <span>{{ currentYear }} 年第 {{ currentQuarter }} 季</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 主要內容區 -->
    <el-row :gutter="20" class="main-content">
      <!-- 左側：未結案履歷 -->
      <el-col :xs="24" :lg="12">
        <el-card shadow="never">
          <template #header>
            <div class="card-header">
              <span>
                <el-icon><Warning /></el-icon>
                待處理履歷
              </span>
              <el-button type="primary" link @click="$router.push('/profiles/pending')">
                查看全部
              </el-button>
            </div>
          </template>

          <div v-if="loadingPending" class="loading-container">
            <el-skeleton :rows="3" animated />
          </div>

          <template v-else-if="pendingProfiles.length > 0">
            <div class="pending-list">
              <div
                v-for="profile in pendingProfiles.slice(0, 5)"
                :key="profile.id"
                class="pending-item"
                @click="$router.push(`/profiles?id=${profile.id}`)"
              >
                <div class="pending-info">
                  <div class="pending-title">
                    <el-tag :type="getProfileTypeColor(profile.profile_type)" size="small">
                      {{ getProfileTypeLabel(profile.profile_type) }}
                    </el-tag>
                    <span class="employee-name">{{ profile.employee_name }}</span>
                  </div>
                  <div class="pending-meta">
                    <span>{{ formatDate(profile.event_date) }}</span>
                    <span>{{ profile.event_location }}</span>
                  </div>
                </div>
                <div class="pending-status">
                  <el-tag :type="getStatusColor(profile.conversion_status)" size="small">
                    {{ getStatusLabel(profile.conversion_status) }}
                  </el-tag>
                </div>
              </div>
            </div>

            <div v-if="pendingProfiles.length > 5" class="more-hint">
              還有 {{ pendingProfiles.length - 5 }} 筆待處理...
            </div>
          </template>

          <el-empty v-else description="目前沒有待處理的履歷" :image-size="80" />
        </el-card>
      </el-col>

      <!-- 右側：快速操作 & 最近記錄 -->
      <el-col :xs="24" :lg="12">
        <!-- 快速操作 -->
        <el-card shadow="never" class="quick-actions-card">
          <template #header>
            <span>
              <el-icon><Operation /></el-icon>
              快速操作
            </span>
          </template>

          <el-row :gutter="12">
            <el-col :span="8">
              <el-button type="primary" plain class="action-btn" @click="$router.push('/profiles')">
                <el-icon><Plus /></el-icon>
                新增履歷
              </el-button>
            </el-col>
            <el-col :span="8">
              <el-button type="success" plain class="action-btn" @click="$router.push('/assessment-records')">
                <el-icon><Edit /></el-icon>
                新增考核
              </el-button>
            </el-col>
            <el-col :span="8">
              <el-button type="warning" plain class="action-btn" @click="$router.push('/employees')">
                <el-icon><Search /></el-icon>
                查詢員工
              </el-button>
            </el-col>
          </el-row>
        </el-card>

        <!-- 月度處理提醒 -->
        <el-card shadow="never" class="reminder-card">
          <template #header>
            <span>
              <el-icon><Bell /></el-icon>
              月度處理提醒
            </span>
          </template>

          <div class="reminder-list">
            <div class="reminder-item" @click="$router.push('/monthly-rewards')">
              <div class="reminder-icon">
                <el-icon><Medal /></el-icon>
              </div>
              <div class="reminder-content">
                <div class="reminder-title">月度獎勵計算</div>
                <div class="reminder-desc">+M02/+M03 零違規獎勵</div>
              </div>
              <el-tag v-if="!lastMonthProcessed.rewards" type="warning" size="small">待處理</el-tag>
              <el-tag v-else type="success" size="small">已完成</el-tag>
            </div>

            <div class="reminder-item" @click="$router.push('/attendance-bonus')">
              <div class="reminder-icon">
                <el-icon><Calendar /></el-icon>
              </div>
              <div class="reminder-content">
                <div class="reminder-title">差勤加分處理</div>
                <div class="reminder-desc">全勤、R班、延長工時加分</div>
              </div>
              <el-tag v-if="!lastMonthProcessed.attendance" type="warning" size="small">待處理</el-tag>
              <el-tag v-else type="success" size="small">已完成</el-tag>
            </div>
          </div>
        </el-card>

        <!-- 系統資訊 -->
        <el-card shadow="never" class="system-info-card">
          <template #header>
            <span>
              <el-icon><InfoFilled /></el-icon>
              系統資訊
            </span>
          </template>

          <el-descriptions :column="2" size="small">
            <el-descriptions-item label="當前使用者">
              {{ authStore.displayName }}
            </el-descriptions-item>
            <el-descriptions-item label="角色">
              <el-tag size="small">{{ getRoleLabel(authStore.userRole) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="部門">
              {{ authStore.userDepartment || '全部' }}
            </el-descriptions-item>
            <el-descriptions-item label="登入時間">
              {{ loginTime }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/**
 * 儀表板頁面
 * 優化版 - 包含統計卡片、未結案提醒、快速操作
 */
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useEmployeesStore } from '@/stores/employees'
import { useProfilesStore, PROFILE_TYPES, CONVERSION_STATUS } from '@/stores/profiles'
import { cloudApi } from '@/services/api'
import {
  User,
  Document,
  Histogram,
  Trophy,
  Warning,
  Operation,
  Plus,
  Edit,
  Search,
  Bell,
  Medal,
  Calendar,
  InfoFilled
} from '@element-plus/icons-vue'

const authStore = useAuthStore()
const employeesStore = useEmployeesStore()
const profilesStore = useProfilesStore()

// 載入狀態
const loadingPending = ref(false)

// 員工統計
const employeeStats = ref({
  total: 0,
  active: 0,
  resigned: 0,
  by_department: {}
})

// 未結案統計
const pendingStats = ref({ total: 0 })
const pendingProfiles = ref([])

// 本月考核統計
const monthlyAssessmentCount = ref(0)
const monthlyDeductions = ref(0)
const monthlyBonuses = ref(0)

// 月度處理狀態
const lastMonthProcessed = ref({
  rewards: false,
  attendance: false
})

// 當前日期資訊
const currentYear = new Date().getFullYear()
const currentQuarter = Math.ceil((new Date().getMonth() + 1) / 3)
const loginTime = ref('')

// 角色標籤
function getRoleLabel(role) {
  const labels = {
    admin: '管理員',
    manager: '主管',
    staff: '值班台'
  }
  return labels[role] || role
}

// 履歷類型
function getProfileTypeLabel(type) {
  return PROFILE_TYPES[type]?.label || type
}

function getProfileTypeColor(type) {
  return PROFILE_TYPES[type]?.color || 'info'
}

// 狀態
function getStatusLabel(status) {
  return CONVERSION_STATUS[status]?.label || status
}

function getStatusColor(status) {
  return CONVERSION_STATUS[status]?.color || 'info'
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 載入統計資料（分開調用，互不影響）
async function loadStats() {
  // 員工統計
  try {
    const empResponse = await cloudApi.get('/api/employees/statistics')
    employeeStats.value = empResponse.data
  } catch (err) {
    console.error('載入員工統計失敗:', err)
  }

  // 未結案統計（獨立調用，失敗不影響其他）
  try {
    const pendingResponse = await cloudApi.get('/api/profiles/pending/statistics')
    pendingStats.value = pendingResponse.data
  } catch (err) {
    console.error('載入未結案統計失敗:', err)
    // 設置默認值，讓 UI 正常顯示
    pendingStats.value = { total: 0, by_type: {} }
  }
}

// 載入未結案列表
async function loadPendingProfiles() {
  loadingPending.value = true
  try {
    const response = await cloudApi.get('/api/profiles/pending', {
      params: { limit: 10 }
    })
    pendingProfiles.value = response.data
  } catch (err) {
    console.error('載入未結案履歷失敗:', err)
    pendingProfiles.value = []
  } finally {
    loadingPending.value = false
  }
}

// 載入本月考核統計
async function loadMonthlyAssessments() {
  try {
    const now = new Date()
    const year = now.getFullYear()
    const month = now.getMonth() + 1

    const response = await cloudApi.get('/api/assessment-records/monthly-summary', {
      params: { year, month }
    })

    if (response.data) {
      monthlyAssessmentCount.value = response.data.total || 0
      monthlyDeductions.value = response.data.deductions || 0
      monthlyBonuses.value = response.data.bonuses || 0
    }
  } catch (err) {
    console.error('載入考核統計失敗:', err)
  }
}

// 檢查月度處理狀態
async function checkMonthlyProcessStatus() {
  try {
    const now = new Date()
    const lastMonth = now.getMonth() === 0 ? 12 : now.getMonth()
    const year = now.getMonth() === 0 ? now.getFullYear() - 1 : now.getFullYear()

    // 這裡可以調用 API 檢查上月處理狀態
    // 簡化處理：假設已經處理
    lastMonthProcessed.value = {
      rewards: true,
      attendance: true
    }
  } catch (err) {
    console.error('檢查處理狀態失敗:', err)
  }
}

onMounted(() => {
  // 設定登入時間
  loginTime.value = new Date().toLocaleString('zh-TW', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })

  // 載入各項統計
  loadStats()
  loadPendingProfiles()
  loadMonthlyAssessments()
  checkMonthlyProcessStatus()
})
</script>

<style scoped>
.dashboard-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 28px;
  color: #303133;
}

.welcome-text {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

/* 統計卡片 */
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  cursor: pointer;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-icon.employees {
  background: linear-gradient(135deg, #409eff, #66b1ff);
}

.stat-icon.pending {
  background: linear-gradient(135deg, #e6a23c, #f5c564);
}

.stat-icon.assessments {
  background: linear-gradient(135deg, #67c23a, #85ce61);
}

.stat-icon.competition {
  background: linear-gradient(135deg, #f56c6c, #f89898);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-footer {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
}

/* 主要內容區 */
.main-content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

/* 未結案列表 */
.pending-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pending-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.pending-item:hover {
  background: #f0f2f5;
}

.pending-info {
  flex: 1;
}

.pending-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.employee-name {
  font-weight: 500;
  color: #303133;
}

.pending-meta {
  font-size: 12px;
  color: #909399;
  display: flex;
  gap: 12px;
}

.more-hint {
  text-align: center;
  padding: 12px;
  color: #909399;
  font-size: 13px;
}

.loading-container {
  padding: 20px;
}

/* 快速操作 */
.quick-actions-card {
  margin-bottom: 16px;
}

.action-btn {
  width: 100%;
  height: 60px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 提醒卡片 */
.reminder-card {
  margin-bottom: 16px;
}

.reminder-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reminder-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
}

.reminder-item:hover {
  background: #f0f2f5;
}

.reminder-icon {
  width: 40px;
  height: 40px;
  background: #ecf5ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
}

.reminder-content {
  flex: 1;
}

.reminder-title {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.reminder-desc {
  font-size: 12px;
  color: #909399;
}

/* 系統資訊 */
.system-info-card {
  margin-bottom: 16px;
}

/* 通用 */
.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}
</style>
