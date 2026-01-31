<template>
  <div class="monthly-rewards-page">
    <div class="page-header">
      <h1>月度獎勵管理</h1>
      <div class="header-hint">
        系統於每月結束後自動計算當月獎勵，或可手動執行計算
      </div>
    </div>

    <!-- 獎勵規則說明 -->
    <el-card shadow="never" class="rules-card">
      <template #header>
        <span>獎勵規則說明</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="12">
          <div class="rule-item">
            <div class="rule-header">
              <el-tag type="success" size="large">+M02</el-tag>
              <span class="rule-name">R+S 零違規獎勵</span>
              <span class="rule-points">+1 分</span>
            </div>
            <div class="rule-desc">
              當月 R 類（責任類）與 S 類（行車類）無任何扣分記錄
            </div>
          </div>
        </el-col>
        <el-col :span="12">
          <div class="rule-item">
            <div class="rule-header">
              <el-tag type="warning" size="large">+M03</el-tag>
              <span class="rule-name">全類別零違規獎勵</span>
              <span class="rule-points">+2 分</span>
            </div>
            <div class="rule-desc">
              當月所有類別（D、W、O、S、R）皆無扣分記錄
            </div>
          </div>
        </el-col>
      </el-row>
      <div class="rule-note">
        <el-icon><InfoFilled /></el-icon>
        兩種獎勵可同時獲得，最高當月可獲得 +3 分
      </div>
    </el-card>

    <!-- 計算控制區 -->
    <el-card shadow="never" class="control-card">
      <el-row :gutter="20" align="middle">
        <el-col :span="4">
          <el-select v-model="selectedYear" placeholder="年度" style="width: 100%">
            <el-option
              v-for="y in yearOptions"
              :key="y"
              :label="`${y} 年`"
              :value="y"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="selectedMonth" placeholder="月份" style="width: 100%">
            <el-option
              v-for="m in 12"
              :key="m"
              :label="`${m} 月`"
              :value="m"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" :loading="calculating" @click="previewRewards">
            <el-icon><View /></el-icon>
            預覽計算
          </el-button>
        </el-col>
        <el-col :span="4">
          <el-button type="success" :loading="executing" @click="executeCalculation">
            <el-icon><Check /></el-icon>
            執行計算
          </el-button>
        </el-col>
        <el-col :span="8">
          <el-select v-model="filterDepartment" placeholder="部門篩選" clearable @change="loadRewards">
            <el-option label="淡海" value="淡海" />
            <el-option label="安坑" value="安坑" />
          </el-select>
        </el-col>
      </el-row>
    </el-card>

    <!-- 預覽結果 -->
    <el-card v-if="previewResult" shadow="never" class="preview-card">
      <template #header>
        <div class="preview-header">
          <span>{{ selectedYear }} 年 {{ selectedMonth }} 月 計算預覽</span>
          <el-tag type="warning">預覽模式（尚未寫入）</el-tag>
        </div>
      </template>

      <el-row :gutter="20" class="preview-stats">
        <el-col :span="6">
          <div class="stat-box">
            <div class="stat-value">{{ previewResult.total_employees }}</div>
            <div class="stat-label">參與人數</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box success">
            <div class="stat-value">{{ previewResult.m02_count }}</div>
            <div class="stat-label">+M02 獲得者</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box warning">
            <div class="stat-value">{{ previewResult.m03_count }}</div>
            <div class="stat-label">+M03 獲得者</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-box info">
            <div class="stat-value">+{{ previewResult.total_points }}</div>
            <div class="stat-label">總發放分數</div>
          </div>
        </el-col>
      </el-row>

      <el-table :data="previewResult.details" border stripe max-height="400">
        <el-table-column prop="employee_name" label="員工" width="120" />
        <el-table-column prop="department" label="部門" width="80" />
        <el-table-column label="+M02" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.qualifies_m02" type="success" size="small">符合</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="+M03" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.qualifies_m03" type="warning" size="small">符合</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="預計獎勵" width="100" align="center">
          <template #default="{ row }">
            <span class="reward-points">+{{ row.total_points }}</span>
          </template>
        </el-table-column>
        <el-table-column label="當月扣分記錄" min-width="200">
          <template #default="{ row }">
            <template v-if="row.deduction_records?.length > 0">
              <el-tag
                v-for="record in row.deduction_records"
                :key="record.id"
                type="danger"
                size="small"
                style="margin: 2px"
              >
                {{ record.standard_code }}
              </el-tag>
            </template>
            <span v-else class="text-success">無扣分記錄</span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 歷史獎勵記錄 -->
    <el-card shadow="never">
      <template #header>
        <span>{{ selectedYear }} 年 月度獎勵記錄</span>
      </template>

      <el-table v-loading="loading" :data="rewardsList" border stripe>
        <el-table-column prop="year_month" label="月份" width="120">
          <template #default="{ row }">
            {{ formatYearMonth(row.year_month) }}
          </template>
        </el-table-column>
        <el-table-column prop="employee_name" label="員工" width="120" />
        <el-table-column prop="department" label="部門" width="80" />
        <el-table-column label="+M02" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.driving_zero_violation" type="success" size="small">+1</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="+M03" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.all_zero_violation" type="warning" size="small">+2</el-tag>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="total_points" label="總獎勵" width="100" align="center">
          <template #default="{ row }">
            <span class="reward-points">+{{ row.total_points }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="calculated_at" label="計算時間" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.calculated_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div v-if="rewardsList.length === 0 && !loading" class="no-data">
        <el-empty description="尚無獎勵記錄" />
      </div>
    </el-card>

    <!-- 年度統計 -->
    <el-card shadow="never" class="yearly-stats-card">
      <template #header>
        <span>{{ selectedYear }} 年 獎勵統計</span>
      </template>

      <el-row :gutter="20">
        <el-col :span="8">
          <div class="yearly-stat">
            <div class="stat-icon success">
              <el-icon><Trophy /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ yearlyStats.m02_total }}</div>
              <div class="stat-label">+M02 發放次數</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="yearly-stat">
            <div class="stat-icon warning">
              <el-icon><Star /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ yearlyStats.m03_total }}</div>
              <div class="stat-label">+M03 發放次數</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="yearly-stat">
            <div class="stat-icon primary">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">+{{ yearlyStats.total_points }}</div>
              <div class="stat-label">總發放分數</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
/**
 * 月度獎勵管理頁面
 * 對應 tasks.md T190: 建立月度獎勵管理頁面
 */
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Check, InfoFilled, Trophy, Star, Coin } from '@element-plus/icons-vue'
import { useAssessmentsStore } from '@/stores/assessments'

const assessmentsStore = useAssessmentsStore()

// 狀態
const loading = ref(false)
const calculating = ref(false)
const executing = ref(false)

// 選擇的年月
const currentDate = new Date()
const selectedYear = ref(currentDate.getFullYear())
const selectedMonth = ref(currentDate.getMonth() + 1)
const filterDepartment = ref('')

// 年份選項
const yearOptions = computed(() => {
  const years = []
  for (let y = currentDate.getFullYear(); y >= currentDate.getFullYear() - 5; y--) {
    years.push(y)
  }
  return years
})

// 預覽結果
const previewResult = ref(null)

// 獎勵列表
const rewardsList = ref([])

// 年度統計
const yearlyStats = ref({
  m02_total: 0,
  m03_total: 0,
  total_points: 0
})

// 格式化年月
function formatYearMonth(ym) {
  if (!ym) return ''
  const [year, month] = ym.split('-')
  return `${year} 年 ${parseInt(month)} 月`
}

// 格式化日期時間
function formatDateTime(dt) {
  if (!dt) return ''
  const date = new Date(dt)
  return `${date.getFullYear()}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 預覽計算
async function previewRewards() {
  calculating.value = true
  try {
    const result = await assessmentsStore.previewMonthlyRewards(selectedYear.value, selectedMonth.value)
    previewResult.value = result
  } catch (err) {
    ElMessage.error('預覽失敗: ' + (err.response?.data?.detail || err.message))
  } finally {
    calculating.value = false
  }
}

// 執行計算
async function executeCalculation() {
  try {
    await ElMessageBox.confirm(
      `確定要計算 ${selectedYear.value} 年 ${selectedMonth.value} 月的月度獎勵？這將為符合條件的員工新增考核記錄。`,
      '執行確認',
      { type: 'warning' }
    )
  } catch {
    return
  }

  executing.value = true
  try {
    const result = await assessmentsStore.calculateMonthlyRewards(selectedYear.value, selectedMonth.value)
    ElMessage.success(`計算完成！發放 ${result.created_count || 0} 筆獎勵`)
    previewResult.value = null
    loadRewards()
  } catch (err) {
    ElMessage.error('計算失敗: ' + (err.response?.data?.detail || err.message))
  } finally {
    executing.value = false
  }
}

// 載入獎勵記錄
async function loadRewards() {
  loading.value = true
  try {
    const result = await assessmentsStore.fetchMonthlyRewards(selectedYear.value, null)
    rewardsList.value = result || []

    // 計算年度統計
    let m02 = 0, m03 = 0, total = 0
    for (const r of rewardsList.value) {
      if (r.driving_zero_violation) m02++
      if (r.all_zero_violation) m03++
      total += r.total_points || 0
    }
    yearlyStats.value = {
      m02_total: m02,
      m03_total: m03,
      total_points: total
    }
  } catch (err) {
    console.error('載入獎勵記錄失敗:', err)
    rewardsList.value = []
  } finally {
    loading.value = false
  }
}

// 監聽年份變化
watch(selectedYear, () => {
  loadRewards()
  previewResult.value = null
})

onMounted(() => {
  loadRewards()
})
</script>

<style scoped>
.monthly-rewards-page {
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.header-hint {
  color: #909399;
  font-size: 14px;
}

/* 規則卡片 */
.rules-card {
  margin-bottom: 20px;
}

.rule-item {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.rule-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.rule-name {
  font-weight: bold;
  font-size: 16px;
}

.rule-points {
  margin-left: auto;
  font-weight: bold;
  color: #67c23a;
  font-size: 18px;
}

.rule-desc {
  color: #666;
  font-size: 14px;
}

.rule-note {
  margin-top: 16px;
  padding: 12px;
  background: #ecf5ff;
  border-radius: 4px;
  color: #409eff;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 控制卡片 */
.control-card {
  margin-bottom: 20px;
}

/* 預覽卡片 */
.preview-card {
  margin-bottom: 20px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.preview-stats {
  margin-bottom: 20px;
}

.stat-box {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  text-align: center;
}

.stat-box.success {
  background: #f0f9eb;
  border-left: 4px solid #67c23a;
}

.stat-box.warning {
  background: #fdf6ec;
  border-left: 4px solid #e6a23c;
}

.stat-box.info {
  background: #ecf5ff;
  border-left: 4px solid #409eff;
}

.stat-box .stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-box .stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 4px;
}

.text-muted {
  color: #c0c4cc;
}

.text-success {
  color: #67c23a;
}

.reward-points {
  font-weight: bold;
  color: #67c23a;
}

.no-data {
  padding: 40px 0;
}

/* 年度統計卡片 */
.yearly-stats-card {
  margin-top: 20px;
}

.yearly-stat {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f9fafb;
  border-radius: 8px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 24px;
  margin-right: 16px;
}

.stat-icon.success {
  background: #e8f5e9;
  color: #4caf50;
}

.stat-icon.warning {
  background: #fff8e1;
  color: #ff9800;
}

.stat-icon.primary {
  background: #e3f2fd;
  color: #2196f3;
}

.stat-info .stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-info .stat-label {
  font-size: 14px;
  color: #999;
}
</style>
