<template>
  <div class="assessment-summary">
    <!-- 載入狀態 -->
    <div v-if="loading" class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>

    <template v-else-if="summary">
      <!-- 總分卡片 -->
      <div class="score-card" :class="scoreClass">
        <div class="score-header">
          <span class="score-label">{{ year }} 年度考核總分</span>
          <el-tag v-if="summary.is_current_year" type="success" size="small">本年度</el-tag>
        </div>
        <div class="score-value">
          <span class="score-number">{{ summary.current_score?.toFixed(1) || '80.0' }}</span>
          <span class="score-unit">分</span>
        </div>
        <div v-if="summary.score_change !== 0" class="score-change">
          <span :class="summary.score_change > 0 ? 'positive' : 'negative'">
            {{ summary.score_change > 0 ? '+' : '' }}{{ summary.score_change?.toFixed(1) }} 分
          </span>
          <span class="change-label">（相較起始分 80 分）</span>
        </div>
      </div>

      <!-- 統計摘要 -->
      <el-row :gutter="16" class="stats-row">
        <el-col :span="8">
          <div class="stat-card deduction">
            <div class="stat-icon">
              <el-icon><Minus /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ summary.deduction_count || 0 }}</div>
              <div class="stat-label">扣分記錄</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-card bonus">
            <div class="stat-icon">
              <el-icon><Plus /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ summary.bonus_count || 0 }}</div>
              <div class="stat-label">加分記錄</div>
            </div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="stat-card reward">
            <div class="stat-icon">
              <el-icon><Trophy /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ summary.monthly_rewards_count || 0 }}</div>
              <div class="stat-label">月度獎勵</div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 累計次數統計 -->
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">各類別累計次數</span>
          <el-tooltip content="同類別違規累計加重，累計倍率 = 1 + 0.5 × (N-1)">
            <el-icon class="info-icon"><InfoFilled /></el-icon>
          </el-tooltip>
        </div>

        <div class="cumulative-grid">
          <div
            v-for="cat in cumulativeCategories"
            :key="cat.category"
            class="cumulative-item"
            :class="{ 'has-count': cat.count > 0 }"
          >
            <div class="cat-header">
              <span class="cat-code" :style="{ background: cat.color }">{{ cat.category }}</span>
              <span class="cat-name">{{ cat.label }}</span>
            </div>
            <div class="cat-count">
              <span class="count-value">{{ cat.count }}</span>
              <span class="count-unit">次</span>
            </div>
            <div v-if="cat.count > 0" class="cat-multiplier">
              累計倍率 ×{{ (1 + 0.5 * (cat.count - 1)).toFixed(1) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 月度獎勵統計 -->
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">月度獎勵統計</span>
        </div>

        <div v-if="monthlyRewardsData.length > 0" class="monthly-rewards-list">
          <div
            v-for="reward in monthlyRewardsData"
            :key="reward.year_month"
            class="reward-item"
          >
            <div class="reward-month">{{ formatYearMonth(reward.year_month) }}</div>
            <div class="reward-details">
              <el-tag v-if="reward.full_attendance" type="success" size="small">
                +M02 全勤（+1分）
              </el-tag>
              <el-tag v-if="reward.driving_zero_violation" type="success" size="small">
                +M03 R+S零違規（+1分）
              </el-tag>
              <el-tag v-if="reward.all_zero_violation" type="warning" size="small">
                +M03 全類別零違規（+2分）
              </el-tag>
            </div>
            <div class="reward-points">+{{ reward.total_points }} 分</div>
          </div>
        </div>
        <div v-else class="no-data">
          尚無月度獎勵記錄
        </div>
      </div>

      <!-- 分類統計圖表 -->
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">分類扣分統計</span>
        </div>

        <div class="category-stats">
          <div
            v-for="stat in categoryStats"
            :key="stat.category"
            class="category-bar"
          >
            <div class="bar-label">
              <span class="bar-code" :style="{ background: stat.color }">{{ stat.category }}</span>
              <span class="bar-name">{{ stat.label }}</span>
            </div>
            <div class="bar-container">
              <div
                class="bar-fill"
                :style="{
                  width: `${stat.percentage}%`,
                  background: stat.color
                }"
              ></div>
            </div>
            <div class="bar-value">{{ stat.total_points?.toFixed(1) || 0 }} 分</div>
          </div>
        </div>
      </div>

      <!-- 最近記錄 -->
      <div class="section-card">
        <div class="section-header">
          <span class="section-title">最近考核記錄</span>
          <el-button v-if="onViewAll" type="primary" link size="small" @click="onViewAll">
            查看全部
          </el-button>
        </div>

        <div v-if="recentRecords.length > 0" class="recent-records">
          <div
            v-for="record in recentRecords"
            :key="record.id"
            class="record-item"
          >
            <div class="record-date">{{ formatDate(record.record_date) }}</div>
            <div class="record-info">
              <span class="record-code">{{ record.standard_code }}</span>
              <span class="record-name">{{ record.standard_name }}</span>
            </div>
            <div class="record-points" :class="record.final_points > 0 ? 'positive' : 'negative'">
              {{ record.final_points > 0 ? '+' : '' }}{{ record.final_points?.toFixed(1) }}
            </div>
          </div>
        </div>
        <div v-else class="no-data">
          尚無考核記錄
        </div>
      </div>
    </template>

    <el-empty v-else description="暫無資料" />
  </div>
</template>

<script setup>
/**
 * 員工年度考核摘要元件
 * 對應 tasks.md T189: 建立員工年度考核摘要元件
 */
import { ref, computed, watch, onMounted } from 'vue'
import { Minus, Plus, Trophy, InfoFilled } from '@element-plus/icons-vue'
import { useAssessmentsStore, ASSESSMENT_CATEGORIES } from '@/stores/assessments'

const props = defineProps({
  employeeId: {
    type: Number,
    required: true
  },
  year: {
    type: Number,
    default: () => new Date().getFullYear()
  },
  onViewAll: {
    type: Function,
    default: null
  }
})

const assessmentsStore = useAssessmentsStore()
const loading = ref(false)
const summary = ref(null)
const monthlyRewardsData = ref([])
const recentRecords = ref([])

// 分數等級樣式
const scoreClass = computed(() => {
  const score = summary.value?.current_score || 80
  if (score >= 85) return 'excellent'
  if (score >= 80) return 'good'
  if (score >= 70) return 'fair'
  return 'poor'
})

// 累計類別資料
const cumulativeCategories = computed(() => {
  const categories = ['D', 'W', 'O', 'S', 'R']
  const counters = summary.value?.cumulative_counters || {}

  return categories.map(cat => ({
    category: cat,
    label: ASSESSMENT_CATEGORIES[cat]?.label || cat,
    color: getCategoryColor(cat),
    count: counters[cat] || 0
  }))
})

// 分類統計
const categoryStats = computed(() => {
  const stats = summary.value?.category_stats || {}
  const categories = ['D', 'W', 'O', 'S', 'R']
  const maxPoints = Math.max(...Object.values(stats).map(s => Math.abs(s.total_points || 0)), 1)

  return categories.map(cat => ({
    category: cat,
    label: ASSESSMENT_CATEGORIES[cat]?.label || cat,
    color: getCategoryColor(cat),
    total_points: stats[cat]?.total_points || 0,
    count: stats[cat]?.count || 0,
    percentage: Math.abs(stats[cat]?.total_points || 0) / maxPoints * 100
  }))
})

// 取得類別顏色
function getCategoryColor(category) {
  const colors = {
    D: '#409eff',  // 服勤類 - 藍色
    W: '#f56c6c',  // 酒測類 - 紅色
    O: '#909399',  // 其他類 - 灰色
    S: '#e6a23c',  // 行車類 - 橙色
    R: '#f56c6c'   // 責任類 - 紅色
  }
  return colors[category] || '#909399'
}

// 格式化日期
function formatDate(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}/${date.getDate()}`
}

// 格式化年月
function formatYearMonth(ym) {
  if (!ym) return ''
  const [year, month] = ym.split('-')
  return `${year} 年 ${parseInt(month)} 月`
}

// 載入資料
async function loadSummary() {
  if (!props.employeeId) return

  loading.value = true
  try {
    const result = await assessmentsStore.fetchEmployeeSummary(props.employeeId, props.year)
    summary.value = result

    // 處理最近記錄
    recentRecords.value = (result.recent_records || []).slice(0, 5)

    // 處理月度獎勵
    monthlyRewardsData.value = result.monthly_rewards || []
  } catch (err) {
    console.error('載入考核摘要失敗:', err)
    summary.value = null
  } finally {
    loading.value = false
  }
}

// 監聽參數變化
watch(() => [props.employeeId, props.year], () => {
  loadSummary()
}, { immediate: true })

// 刷新
function refresh() {
  loadSummary()
}

defineExpose({ refresh })
</script>

<style scoped>
.assessment-summary {
  padding: 16px;
}

.loading-state {
  padding: 20px;
}

/* 總分卡片 */
.score-card {
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;
  text-align: center;
  color: #fff;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.score-card.excellent {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.score-card.good {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.score-card.fair {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.score-card.poor {
  background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
}

.score-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.score-label {
  font-size: 14px;
  opacity: 0.9;
}

.score-value {
  display: flex;
  justify-content: center;
  align-items: baseline;
}

.score-number {
  font-size: 48px;
  font-weight: bold;
}

.score-unit {
  font-size: 20px;
  margin-left: 4px;
}

.score-change {
  margin-top: 12px;
  font-size: 14px;
}

.score-change .positive {
  color: #a5f3c6;
}

.score-change .negative {
  color: #fca5a5;
}

.change-label {
  opacity: 0.7;
  margin-left: 4px;
}

/* 統計卡片 */
.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  background: #fff;
  border: 1px solid #eee;
}

.stat-card.deduction {
  border-left: 4px solid #f56c6c;
}

.stat-card.bonus {
  border-left: 4px solid #67c23a;
}

.stat-card.reward {
  border-left: 4px solid #e6a23c;
}

.stat-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 20px;
  margin-right: 12px;
}

.stat-card.deduction .stat-icon {
  background: #fef0f0;
  color: #f56c6c;
}

.stat-card.bonus .stat-icon {
  background: #f0f9eb;
  color: #67c23a;
}

.stat-card.reward .stat-icon {
  background: #fdf6ec;
  color: #e6a23c;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

/* 區塊卡片 */
.section-card {
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
  color: #333;
}

.info-icon {
  color: #999;
  cursor: help;
}

/* 累計次數 */
.cumulative-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}

.cumulative-item {
  padding: 12px;
  border: 1px solid #eee;
  border-radius: 8px;
  text-align: center;
  transition: all 0.2s;
}

.cumulative-item.has-count {
  background: #fffbeb;
  border-color: #fcd34d;
}

.cat-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
}

.cat-code {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  color: #fff;
  font-weight: bold;
  font-size: 14px;
}

.cat-name {
  font-size: 12px;
  color: #666;
}

.cat-count .count-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.cat-count .count-unit {
  font-size: 12px;
  color: #999;
}

.cat-multiplier {
  margin-top: 4px;
  font-size: 11px;
  color: #e6a23c;
}

/* 月度獎勵 */
.monthly-rewards-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.reward-item {
  display: flex;
  align-items: center;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.reward-month {
  min-width: 100px;
  font-weight: 500;
}

.reward-details {
  flex: 1;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.reward-points {
  font-weight: bold;
  color: #67c23a;
}

/* 分類統計 */
.category-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-bar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bar-label {
  min-width: 100px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-code {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  color: #fff;
  font-weight: bold;
  font-size: 12px;
}

.bar-name {
  font-size: 13px;
  color: #666;
}

.bar-container {
  flex: 1;
  height: 20px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s;
}

.bar-value {
  min-width: 70px;
  text-align: right;
  font-weight: 500;
  color: #f56c6c;
}

/* 最近記錄 */
.recent-records {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.record-date {
  min-width: 50px;
  font-size: 13px;
  color: #999;
}

.record-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.record-code {
  font-weight: bold;
  color: #333;
}

.record-name {
  font-size: 13px;
  color: #666;
}

.record-points {
  font-weight: bold;
}

.record-points.positive {
  color: #67c23a;
}

.record-points.negative {
  color: #f56c6c;
}

.no-data {
  padding: 20px;
  text-align: center;
  color: #999;
}

/* 響應式 */
@media (max-width: 768px) {
  .cumulative-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .stats-row .el-col {
    margin-bottom: 12px;
  }
}
</style>
