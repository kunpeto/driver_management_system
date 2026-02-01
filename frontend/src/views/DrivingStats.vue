<template>
  <div class="driving-stats">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>駕駛時數統計</h1>
      <p class="subtitle">查詢員工每日駕駛時數與季度累計統計</p>
    </div>

    <!-- 篩選條件 -->
    <el-card class="filter-card">
      <el-form :inline="true">
        <el-form-item label="部門">
          <el-select
            v-model="filters.department"
            placeholder="選擇部門"
            clearable
            @change="handleFilterChange"
          >
            <el-option label="淡海" value="淡海" />
            <el-option label="安坑" value="安坑" />
          </el-select>
        </el-form-item>

        <el-form-item label="年份">
          <el-select v-model="filters.year" @change="handleFilterChange">
            <el-option
              v-for="y in years"
              :key="y"
              :label="`${y} 年`"
              :value="y"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="季度">
          <el-select v-model="filters.quarter" @change="handleFilterChange">
            <el-option label="Q1 (1-3月)" :value="1" />
            <el-option label="Q2 (4-6月)" :value="2" />
            <el-option label="Q3 (7-9月)" :value="3" />
            <el-option label="Q4 (10-12月)" :value="4" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadQuarterStats">
            查詢季度統計
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 季度統計摘要 -->
    <el-row v-if="departmentStats" :gutter="16" class="summary-cards">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">員工人數</div>
            <div class="stat-value">{{ departmentStats.total_employees }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">季度標籤</div>
            <div class="stat-value">{{ filters.year }} Q{{ filters.quarter }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">部門</div>
            <div class="stat-value">{{ filters.department || '全部' }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">資格門檻</div>
            <div class="stat-value">300 小時</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 員工季度統計表格 -->
    <el-card v-loading="store.loading" class="data-card">
      <template #header>
        <div class="card-header">
          <span>季度駕駛時數統計</span>
        </div>
      </template>

      <el-table :data="departmentStats?.employees || []" stripe border>
        <el-table-column type="index" label="#" width="50" />
        <el-table-column prop="employee_code" label="員工編號" width="120" />
        <el-table-column prop="employee_name" label="姓名" width="100" />
        <el-table-column label="總時數" width="100" align="right">
          <template #default="{ row }">
            {{ row.total_hours.toFixed(1) }} h
          </template>
        </el-table-column>
        <el-table-column label="R班加成" width="100" align="right">
          <template #default="{ row }">
            {{ (row.holiday_work_bonus_minutes / 60).toFixed(1) }} h
          </template>
        </el-table-column>
        <el-table-column label="有效時數" width="100" align="right">
          <template #default="{ row }">
            <span :class="row.effective_hours >= 300 ? 'text-success' : 'text-warning'">
              {{ row.effective_hours.toFixed(1) }} h
            </span>
          </template>
        </el-table-column>
        <el-table-column label="出勤天數" width="100" align="center">
          <template #default="{ row }">
            {{ row.work_days }} 天
          </template>
        </el-table-column>
        <el-table-column label="事件數" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.incident_count > 0 ? 'danger' : 'success'" size="small">
              {{ row.incident_count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="資格" width="80" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.effective_hours >= 300 ? 'success' : 'info'"
              size="small"
            >
              {{ row.effective_hours >= 300 ? '符合' : '不符' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useDrivingStatsStore } from '@/stores/drivingStats'

const store = useDrivingStatsStore()

// 篩選條件
const filters = reactive({
  department: '淡海',
  year: new Date().getFullYear(),
  quarter: Math.ceil((new Date().getMonth() + 1) / 3)
})

// 年份選項
const years = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

// 部門統計資料
const departmentStats = computed(() => store.departmentQuarterStats)

// 篩選變更
function handleFilterChange() {
  // 自動重新查詢
}

// 載入季度統計
async function loadQuarterStats() {
  if (!filters.department) {
    return
  }

  await store.loadDepartmentQuarterStats(
    filters.department,
    filters.year,
    filters.quarter
  )
}

onMounted(() => {
  loadQuarterStats()
})
</script>

<style scoped>
.driving-stats {
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

.filter-card {
  margin-bottom: 16px;
}

.summary-cards {
  margin-bottom: 16px;
}

.stat-card {
  text-align: center;
  padding: 12px 0;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.data-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.text-success {
  color: #67c23a;
  font-weight: bold;
}

.text-warning {
  color: #e6a23c;
}
</style>
