<template>
  <div class="attendance-bonus-page">
    <div class="page-header">
      <h1>差勤加分處理</h1>
      <div class="header-hint">
        從班表自動判定全勤、R班出勤、延長工時等加分項目，批次建立考核記錄
      </div>
    </div>

    <!-- 加分規則說明 -->
    <el-card shadow="never" class="rules-card">
      <template #header>
        <span>加分規則說明</span>
      </template>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="rule-section">
            <div class="section-title">+M 月度獎勵</div>
            <div class="rule-item">
              <el-tag type="success" size="small">+M01</el-tag>
              <span>全勤</span>
              <span class="rule-points">+3</span>
            </div>
            <div class="rule-item">
              <el-tag type="success" size="small">+M02</el-tag>
              <span>行車零違規</span>
              <span class="rule-points">+1</span>
            </div>
            <div class="rule-item">
              <el-tag type="success" size="small">+M03</el-tag>
              <span>全項目零違規</span>
              <span class="rule-points">+2</span>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="rule-section">
            <div class="section-title">+A 出勤加分</div>
            <div class="rule-item">
              <el-tag type="warning" size="small">+A01</el-tag>
              <span>R班出勤</span>
              <span class="rule-points">+3</span>
            </div>
            <div class="rule-item">
              <el-tag type="warning" size="small">+A02</el-tag>
              <span>國定假日出勤</span>
              <span class="rule-points">+1</span>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="rule-section">
            <div class="section-title">+A 延長工時</div>
            <div class="rule-item">
              <el-tag type="info" size="small">+A03</el-tag>
              <span>延長 1 小時</span>
              <span class="rule-points">+0.5</span>
            </div>
            <div class="rule-item">
              <el-tag type="info" size="small">+A04</el-tag>
              <span>延長 2 小時</span>
              <span class="rule-points">+1.0</span>
            </div>
            <div class="rule-item">
              <el-tag type="info" size="small">+A05</el-tag>
              <span>延長 3 小時</span>
              <span class="rule-points">+1.5</span>
            </div>
            <div class="rule-item">
              <el-tag type="info" size="small">+A06</el-tag>
              <span>延長 4 小時</span>
              <span class="rule-points">+2.0</span>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 處理控制區 -->
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
          <el-select v-model="selectedDepartment" placeholder="部門" style="width: 100%">
            <el-option label="淡海" value="淡海" />
            <el-option label="安坑" value="安坑" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" :loading="previewing" @click="previewBonus">
            <el-icon><View /></el-icon>
            預覽處理
          </el-button>
        </el-col>
        <el-col :span="4">
          <el-button type="success" :loading="processing" :disabled="!selectedDepartment" @click="processBonus">
            <el-icon><Check /></el-icon>
            執行處理
          </el-button>
        </el-col>
      </el-row>
    </el-card>

    <!-- 處理結果 -->
    <el-card v-if="processResult" shadow="never" class="result-card">
      <template #header>
        <div class="result-header">
          <span>{{ selectedYear }} 年 {{ selectedMonth }} 月 {{ selectedDepartment }} 處理結果</span>
          <el-tag :type="processResult.success ? 'success' : 'danger'">
            {{ processResult.success ? '處理完成' : '處理失敗' }}
          </el-tag>
        </div>
      </template>

      <BonusProcessResult :result="processResult" />
    </el-card>

    <!-- 歷史記錄 -->
    <el-card shadow="never">
      <template #header>
        <span>處理歷史</span>
      </template>

      <el-table v-loading="loadingHistory" :data="historyList" border stripe>
        <el-table-column prop="year" label="年度" width="80" />
        <el-table-column prop="month" label="月份" width="80" />
        <el-table-column prop="department" label="部門" width="100" />
        <el-table-column prop="total_records" label="記錄數" width="100" align="center" />
        <el-table-column prop="processed_at" label="處理時間" min-width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.processed_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="viewMonthStats(row)">
              查看詳情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="historyList.length === 0 && !loadingHistory" class="no-data">
        <el-empty description="尚無處理歷史" />
      </div>
    </el-card>

    <!-- 月度統計對話框 -->
    <el-dialog v-model="showStatsDialog" :title="`${statsYear} 年 ${statsMonth} 月 加分統計`" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="全勤 (+M01)">{{ monthStats.m01_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="行車零違規 (+M02)">{{ monthStats.m02_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="全項目零違規 (+M03)">{{ monthStats.m03_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="R班出勤 (+A01)">{{ monthStats.a01_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="國定假日 (+A02)">{{ monthStats.a02_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="延長工時 1h (+A03)">{{ monthStats.a03_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="延長工時 2h (+A04)">{{ monthStats.a04_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="延長工時 3h (+A05)">{{ monthStats.a05_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="延長工時 4h (+A06)">{{ monthStats.a06_count }} 筆</el-descriptions-item>
        <el-descriptions-item label="總加分記錄">{{ monthStats.total_bonus_records }} 筆</el-descriptions-item>
        <el-descriptions-item label="總加分分數">+{{ monthStats.total_bonus_points?.toFixed(1) }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 差勤加分處理頁面
 * 對應 tasks.md T203: 建立差勤加分處理頁面
 */
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, Check } from '@element-plus/icons-vue'
import { useAttendanceBonusStore } from '@/stores/attendanceBonus'
import BonusProcessResult from '@/components/attendance/BonusProcessResult.vue'

const store = useAttendanceBonusStore()

// 狀態
const previewing = ref(false)
const processing = ref(false)
const loadingHistory = ref(false)

// 選擇的年月部門
const currentDate = new Date()
const selectedYear = ref(currentDate.getFullYear())
const selectedMonth = ref(currentDate.getMonth() + 1)
const selectedDepartment = ref('淡海')

// 年份選項
const yearOptions = computed(() => {
  const years = []
  for (let y = currentDate.getFullYear(); y >= currentDate.getFullYear() - 3; y--) {
    years.push(y)
  }
  return years
})

// 處理結果
const processResult = ref(null)

// 歷史記錄
const historyList = ref([])

// 月度統計對話框
const showStatsDialog = ref(false)
const statsYear = ref(0)
const statsMonth = ref(0)
const monthStats = ref({})

// 格式化日期時間
function formatDateTime(dt) {
  if (!dt) return ''
  const date = new Date(dt)
  return `${date.getFullYear()}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 預覽處理
async function previewBonus() {
  if (!selectedDepartment.value) {
    ElMessage.warning('請選擇部門')
    return
  }

  previewing.value = true
  try {
    const result = await store.previewBonus({
      year: selectedYear.value,
      month: selectedMonth.value,
      department: selectedDepartment.value
    })
    processResult.value = result
    if (!result.success && result.errors?.length > 0) {
      ElMessage.error('預覽失敗: ' + result.errors[0])
    }
  } catch (err) {
    ElMessage.error('預覽失敗: ' + (err.response?.data?.detail || err.message))
  } finally {
    previewing.value = false
  }
}

// 執行處理
async function processBonus() {
  if (!selectedDepartment.value) {
    ElMessage.warning('請選擇部門')
    return
  }

  try {
    await ElMessageBox.confirm(
      `確定要執行 ${selectedYear.value} 年 ${selectedMonth.value} 月 ${selectedDepartment.value} 的差勤加分處理？\n\n這將自動建立加分記錄，已存在的記錄會被跳過。`,
      '執行確認',
      { type: 'warning' }
    )
  } catch {
    return
  }

  processing.value = true
  try {
    const result = await store.processBonus({
      year: selectedYear.value,
      month: selectedMonth.value,
      department: selectedDepartment.value
    })
    processResult.value = result
    if (result.success) {
      const totalCreated = result.m01_count + result.a01_count + result.a02_count +
                          result.a03_count + result.a04_count + result.a05_count + result.a06_count
      ElMessage.success(`處理完成！建立 ${totalCreated} 筆加分記錄，跳過 ${result.skipped_count} 筆已存在記錄`)
      loadHistory()
    } else if (result.errors?.length > 0) {
      ElMessage.error('處理失敗: ' + result.errors[0])
    }
  } catch (err) {
    ElMessage.error('處理失敗: ' + (err.response?.data?.detail || err.message))
  } finally {
    processing.value = false
  }
}

// 載入歷史記錄
async function loadHistory() {
  loadingHistory.value = true
  try {
    const result = await store.fetchHistory({ year: selectedYear.value })
    historyList.value = result || []
  } catch (err) {
    console.error('載入歷史記錄失敗:', err)
    historyList.value = []
  } finally {
    loadingHistory.value = false
  }
}

// 查看月度統計
async function viewMonthStats(row) {
  statsYear.value = row.year
  statsMonth.value = row.month
  try {
    const stats = await store.fetchMonthStats(row.year, row.month, row.department)
    monthStats.value = stats || {}
    showStatsDialog.value = true
  } catch (err) {
    ElMessage.error('載入統計失敗: ' + (err.response?.data?.detail || err.message))
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.attendance-bonus-page {
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

.rule-section {
  padding: 12px;
  background: #f9fafb;
  border-radius: 8px;
  height: 100%;
}

.section-title {
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 12px;
  color: #333;
}

.rule-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 13px;
}

.rule-item:last-child {
  margin-bottom: 0;
}

.rule-points {
  margin-left: auto;
  font-weight: bold;
  color: #67c23a;
}

/* 控制卡片 */
.control-card {
  margin-bottom: 20px;
}

/* 結果卡片 */
.result-card {
  margin-bottom: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.no-data {
  padding: 40px 0;
}
</style>
