<template>
  <div class="pending-statistics">
    <el-row :gutter="16">
      <!-- 總未結案數 -->
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon pending">
              <el-icon :size="32"><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">待處理</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 本月完成率 -->
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon success">
              <el-icon :size="32"><TrendCharts /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ completionPercentage }}%</div>
              <div class="stat-label">本月完成率</div>
            </div>
          </div>
          <div class="stat-detail">
            {{ stats.this_month_completed }} / {{ stats.this_month_total }}
          </div>
        </el-card>
      </el-col>

      <!-- 最舊未結案 -->
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-content">
            <div class="stat-icon warning">
              <el-icon :size="32"><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ oldestDateDisplay }}</div>
              <div class="stat-label">最舊未結案</div>
            </div>
          </div>
          <div v-if="daysOverdue > 0" class="stat-detail warning-text">
            已逾 {{ daysOverdue }} 天
          </div>
        </el-card>
      </el-col>

      <!-- 各類型分佈 -->
      <el-col :span="6">
        <el-card shadow="hover" class="stat-card type-distribution">
          <div class="stat-title">類型分佈</div>
          <div class="type-list">
            <div v-for="(count, type) in stats.by_type" :key="type" class="type-item">
              <el-tag :type="getTypeColor(type)" size="small">
                {{ getTypeLabel(type) }}
              </el-tag>
              <span class="type-count">{{ count }}</span>
            </div>
            <div v-if="Object.keys(stats.by_type || {}).length === 0" class="empty-text">
              無未結案
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/**
 * 未結案統計元件
 * Phase 14 T195
 */
import { computed } from 'vue'
import { Document, TrendCharts, Calendar } from '@element-plus/icons-vue'

const props = defineProps({
  stats: {
    type: Object,
    default: () => ({
      total: 0,
      by_type: {},
      oldest_pending_date: null,
      this_month_completed: 0,
      this_month_total: 0,
      completion_rate: 0
    })
  }
})

// 履歷類型設定
const PROFILE_TYPES = {
  event_investigation: { label: '事件調查', color: 'danger' },
  personnel_interview: { label: '人員訪談', color: 'warning' },
  corrective_measures: { label: '矯正措施', color: 'success' },
  assessment_notice: { label: '考核通知', color: 'primary' },
  basic: { label: '基本', color: 'info' }
}

// 計算完成率百分比
const completionPercentage = computed(() => {
  return Math.round((props.stats.completion_rate || 0) * 100)
})

// 最舊日期顯示
const oldestDateDisplay = computed(() => {
  if (!props.stats.oldest_pending_date) return '-'
  return props.stats.oldest_pending_date
})

// 計算逾期天數
const daysOverdue = computed(() => {
  if (!props.stats.oldest_pending_date) return 0
  const oldest = new Date(props.stats.oldest_pending_date)
  const today = new Date()
  const diffTime = today - oldest
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  return Math.max(0, diffDays - 7) // 超過 7 天視為逾期
})

// 取得類型標籤
function getTypeLabel(type) {
  return PROFILE_TYPES[type]?.label || type
}

// 取得類型顏色
function getTypeColor(type) {
  return PROFILE_TYPES[type]?.color || 'info'
}
</script>

<style scoped>
.pending-statistics {
  margin-bottom: 20px;
}

.stat-card {
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-icon.pending {
  background: linear-gradient(135deg, #f56c6c, #e6a23c);
}

.stat-icon.success {
  background: linear-gradient(135deg, #67c23a, #95d475);
}

.stat-icon.warning {
  background: linear-gradient(135deg, #e6a23c, #f5a623);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

.stat-detail {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  text-align: right;
}

.warning-text {
  color: #e6a23c;
  font-weight: 500;
}

.stat-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 12px;
  font-weight: 500;
}

.type-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.type-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.type-count {
  font-weight: 600;
  color: #303133;
}

.empty-text {
  color: #909399;
  font-size: 13px;
  text-align: center;
  padding: 8px 0;
}
</style>
