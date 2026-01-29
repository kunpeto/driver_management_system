<template>
  <div class="driving-competition">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>駕駛競賽排名</h1>
      <p class="subtitle">查詢季度駕駛競賽排名，包含資格狀態與獎金金額</p>
    </div>

    <!-- 篩選條件 -->
    <el-card class="filter-card">
      <el-form :inline="true">
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

        <el-form-item label="部門">
          <el-select
            v-model="filters.department"
            placeholder="全部"
            clearable
            @change="handleFilterChange"
          >
            <el-option label="淡海" value="淡海" />
            <el-option label="安坑" value="安坑" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadRanking">
            查詢排名
          </el-button>
          <el-button
            v-if="isAdmin"
            type="warning"
            @click="handleCalculate"
            :loading="store.saving"
          >
            重新計算
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 統計摘要 -->
    <el-row :gutter="16" class="summary-cards" v-if="ranking">
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">總人數</div>
            <div class="stat-value">{{ ranking.stats.total_employees }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">符合資格</div>
            <div class="stat-value text-success">{{ ranking.stats.qualified_count }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">獲獎人數</div>
            <div class="stat-value text-warning">{{ ranking.stats.bonus_recipients }}</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div class="stat-card">
            <div class="stat-label">獎金總額</div>
            <div class="stat-value">{{ formatMoney(ranking.stats.total_bonus) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 獎金說明 -->
    <el-alert
      type="info"
      :closable="false"
      class="bonus-info"
      v-if="bonusTiers"
    >
      <template #title>
        <strong>獎金規則</strong>
      </template>
      <div class="bonus-rules">
        <div class="rule-item">
          <strong>資格門檻：</strong>季度累計 ≥ {{ bonusTiers.qualification_hours }} 小時 且 季末在職
        </div>
        <div class="rule-item">
          <strong>淡海（前5名）：</strong>
          {{ bonusTiers.rules['淡海'].amounts.join(' / ') }} 元
        </div>
        <div class="rule-item">
          <strong>安坑（前3名）：</strong>
          {{ bonusTiers.rules['安坑'].amounts.join(' / ') }} 元
        </div>
      </div>
    </el-alert>

    <!-- 排名表格 -->
    <el-card class="data-card" v-loading="store.loading">
      <template #header>
        <div class="card-header">
          <span>{{ ranking?.quarter_label || '' }} 競賽排名</span>
        </div>
      </template>

      <el-table :data="ranking?.rankings || []" stripe border>
        <el-table-column label="排名" width="70" align="center">
          <template #default="{ row }">
            <div class="rank-badge" :class="getRankClass(row.rank_in_department)">
              {{ row.rank_in_department }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="department" label="部門" width="80" />
        <el-table-column prop="employee_code" label="員工編號" width="120" />
        <el-table-column prop="employee_name" label="姓名" width="100" />
        <el-table-column label="有效時數" width="120" align="right">
          <template #default="{ row }">
            {{ row.effective_hours.toFixed(1) }} h
          </template>
        </el-table-column>
        <el-table-column label="事件數" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.incident_count > 0 ? 'danger' : 'success'" size="small">
              {{ row.incident_count }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="積分" width="100" align="right">
          <template #default="{ row }">
            <strong>{{ row.final_score.toFixed(1) }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="資格" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_qualified ? 'success' : 'info'" size="small">
              {{ row.is_qualified ? '符合' : '不符' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="季末在職" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_employed_on_last_day ? 'success' : 'danger'" size="small">
              {{ row.is_employed_on_last_day ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="獎金" width="100" align="right">
          <template #default="{ row }">
            <span v-if="row.bonus_amount > 0" class="bonus-amount">
              {{ formatMoney(row.bonus_amount) }}
            </span>
            <span v-else class="no-bonus">-</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useDrivingStatsStore } from '@/stores/drivingStats'

const authStore = useAuthStore()
const store = useDrivingStatsStore()

// 篩選條件
const filters = reactive({
  year: new Date().getFullYear(),
  quarter: Math.ceil((new Date().getMonth() + 1) / 3),
  department: null
})

// 年份選項
const years = computed(() => {
  const currentYear = new Date().getFullYear()
  return Array.from({ length: 5 }, (_, i) => currentYear - i)
})

// 排名資料
const ranking = computed(() => store.competitionRanking)

// 獎金階層
const bonusTiers = computed(() => store.bonusTiers)

// 是否為管理員
const isAdmin = computed(() => authStore.isAdmin)

// 篩選變更
function handleFilterChange() {
  loadRanking()
}

// 載入排名
async function loadRanking() {
  await store.loadCompetitionRanking(
    filters.year,
    filters.quarter,
    filters.department
  )
}

// 手動計算
async function handleCalculate() {
  try {
    await ElMessageBox.confirm(
      `確定要重新計算 ${filters.year} Q${filters.quarter} 的競賽排名嗎？\n這將覆蓋現有的排名資料。`,
      '計算確認',
      { type: 'warning' }
    )

    const result = await store.calculateRanking(filters.year, filters.quarter)

    if (result.errors.length > 0) {
      ElMessage.warning(`計算完成，但有錯誤：${result.errors.join(', ')}`)
    } else {
      ElMessage.success(`計算完成！共處理 ${result.total_processed} 位員工`)
    }
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(store.error || '計算失敗')
    }
  }
}

// 格式化金額
function formatMoney(amount) {
  return `$${amount.toLocaleString()}`
}

// 取得排名樣式
function getRankClass(rank) {
  if (rank === 1) return 'rank-gold'
  if (rank === 2) return 'rank-silver'
  if (rank === 3) return 'rank-bronze'
  return ''
}

onMounted(async () => {
  await store.loadBonusTiers()
  await loadRanking()
})
</script>

<style scoped>
.driving-competition {
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

.text-success {
  color: #67c23a;
}

.text-warning {
  color: #e6a23c;
}

.bonus-info {
  margin-bottom: 16px;
}

.bonus-rules {
  margin-top: 8px;
}

.rule-item {
  margin-bottom: 4px;
}

.data-card {
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.rank-badge {
  width: 32px;
  height: 32px;
  line-height: 32px;
  border-radius: 50%;
  background: #f0f2f5;
  font-weight: bold;
  margin: 0 auto;
}

.rank-gold {
  background: linear-gradient(135deg, #ffd700, #ffec8b);
  color: #8b6914;
}

.rank-silver {
  background: linear-gradient(135deg, #c0c0c0, #e8e8e8);
  color: #4a4a4a;
}

.rank-bronze {
  background: linear-gradient(135deg, #cd7f32, #daa520);
  color: #5c3317;
}

.bonus-amount {
  color: #67c23a;
  font-weight: bold;
}

.no-bonus {
  color: #c0c4cc;
}
</style>
