<template>
  <div class="bonus-process-result">
    <!-- 統計區 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="4">
        <div class="stat-box">
          <div class="stat-value">{{ result.total_employees }}</div>
          <div class="stat-label">處理人數</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box success">
          <div class="stat-value">{{ result.m01_count }}</div>
          <div class="stat-label">全勤 +M01</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box success">
          <div class="stat-value">{{ result.m02_count }}</div>
          <div class="stat-label">行車零違規 +M02</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box success">
          <div class="stat-value">{{ result.m03_count }}</div>
          <div class="stat-label">全項目零違規 +M03</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box warning">
          <div class="stat-value">{{ result.a01_count }}</div>
          <div class="stat-label">R班 +A01</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box warning">
          <div class="stat-value">{{ result.a02_count }}</div>
          <div class="stat-label">國定假日 +A02</div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="stats-row">
      <el-col :span="4">
        <div class="stat-box info">
          <div class="stat-value">{{ result.a03_count }}</div>
          <div class="stat-label">延長1h +A03</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box info">
          <div class="stat-value">{{ result.a04_count }}</div>
          <div class="stat-label">延長2h +A04</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box info">
          <div class="stat-value">{{ result.a05_count }}</div>
          <div class="stat-label">延長3h +A05</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box info">
          <div class="stat-value">{{ result.a06_count }}</div>
          <div class="stat-label">延長4h +A06</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box muted">
          <div class="stat-value">{{ result.skipped_count }}</div>
          <div class="stat-label">跳過（已存在）</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-box primary">
          <div class="stat-value">+{{ totalPoints }}</div>
          <div class="stat-label">總加分</div>
        </div>
      </el-col>
    </el-row>

    <!-- 警告訊息 -->
    <el-alert
      v-if="result.warnings?.length > 0"
      type="warning"
      :closable="false"
      style="margin-top: 16px"
    >
      <template #title>
        <span>處理警告 ({{ result.warnings.length }} 則)</span>
      </template>
      <ul class="warning-list">
        <li v-for="(warn, idx) in result.warnings.slice(0, 5)" :key="idx">
          {{ warn }}
        </li>
        <li v-if="result.warnings.length > 5">
          ... 還有 {{ result.warnings.length - 5 }} 則警告
        </li>
      </ul>
    </el-alert>

    <!-- 錯誤訊息 -->
    <el-alert
      v-if="result.errors?.length > 0"
      type="error"
      :closable="false"
      style="margin-top: 16px"
    >
      <template #title>
        <span>處理錯誤 ({{ result.errors.length }} 則)</span>
      </template>
      <ul class="error-list">
        <li v-for="(err, idx) in result.errors" :key="idx">
          {{ err }}
        </li>
      </ul>
    </el-alert>

    <!-- 詳細記錄列表 -->
    <div v-if="result.records?.length > 0" class="records-section">
      <div class="records-header">
        <span>詳細記錄 ({{ result.records.length }} 筆)</span>
        <el-switch
          v-model="showSkipped"
          active-text="顯示跳過記錄"
          inactive-text="隱藏跳過記錄"
        />
      </div>

      <el-table :data="filteredRecords" border stripe max-height="400" size="small">
        <el-table-column prop="standard_code" label="代碼" width="80">
          <template #default="{ row }">
            <el-tag :type="getTagType(row.standard_code)" size="small">
              {{ row.standard_code }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="employee_name" label="員工" width="100" />
        <el-table-column prop="employee_code" label="員編" width="120" />
        <el-table-column prop="record_date" label="日期" width="110" />
        <el-table-column prop="points" label="分數" width="80" align="center">
          <template #default="{ row }">
            <span class="points-value">+{{ row.points }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="說明" min-width="200" />
        <el-table-column label="狀態" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.created" type="success" size="small">已建立</el-tag>
            <el-tag v-else type="info" size="small">{{ row.skipped_reason || '跳過' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
/**
 * 差勤處理結果元件
 * 對應 tasks.md T204: 建立差勤處理結果元件
 */
import { ref, computed } from 'vue'

const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

const showSkipped = ref(false)

// 過濾後的記錄
const filteredRecords = computed(() => {
  if (!props.result.records) return []
  if (showSkipped.value) {
    return props.result.records
  }
  return props.result.records.filter(r => r.created)
})

// 總加分
const totalPoints = computed(() => {
  const r = props.result
  return (
    (r.m01_count || 0) * 3 +
    (r.m02_count || 0) * 1 +
    (r.m03_count || 0) * 2 +
    (r.a01_count || 0) * 3 +
    (r.a02_count || 0) * 1 +
    (r.a03_count || 0) * 0.5 +
    (r.a04_count || 0) * 1 +
    (r.a05_count || 0) * 1.5 +
    (r.a06_count || 0) * 2
  ).toFixed(1)
})

// 根據代碼取得 Tag 類型
function getTagType(code) {
  if (code.startsWith('+M')) return 'success'
  if (code === '+A01' || code === '+A02') return 'warning'
  return 'info'
}
</script>

<style scoped>
.bonus-process-result {
  padding: 8px 0;
}

.stats-row {
  margin-bottom: 16px;
}

.stat-box {
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  text-align: center;
}

.stat-box.success {
  background: #f0f9eb;
  border-left: 3px solid #67c23a;
}

.stat-box.warning {
  background: #fdf6ec;
  border-left: 3px solid #e6a23c;
}

.stat-box.info {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.stat-box.primary {
  background: #e6f4ff;
  border-left: 3px solid #1890ff;
}

.stat-box.muted {
  background: #f5f5f5;
  border-left: 3px solid #909399;
}

.stat-box .stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-box .stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.warning-list,
.error-list {
  margin: 8px 0 0 0;
  padding-left: 20px;
}

.warning-list li,
.error-list li {
  margin-bottom: 4px;
}

.records-section {
  margin-top: 20px;
}

.records-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-weight: bold;
}

.points-value {
  font-weight: bold;
  color: #67c23a;
}
</style>
