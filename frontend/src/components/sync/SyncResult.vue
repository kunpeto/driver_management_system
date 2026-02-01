<template>
  <div :class="['sync-result', result.success ? 'success' : 'error']">
    <div class="result-header">
      <span class="result-icon">{{ result.success ? '✓' : '✗' }}</span>
      <span class="result-title">
        {{ result.success ? '同步完成' : '同步失敗' }}
      </span>
      <button class="dismiss-btn" @click="emit('dismiss')">×</button>
    </div>

    <div class="result-body">
      <!-- 成功統計 -->
      <div v-if="result.success" class="stats-grid">
        <div class="stat-item">
          <span class="stat-value">{{ result.total_rows || 0 }}</span>
          <span class="stat-label">總筆數</span>
        </div>
        <div class="stat-item success">
          <span class="stat-value">{{ result.success_count || 0 }}</span>
          <span class="stat-label">新增/更新</span>
        </div>
        <div v-if="result.error_count" class="stat-item">
          <span class="stat-value error">{{ result.error_count }}</span>
          <span class="stat-label">錯誤</span>
        </div>
      </div>

      <!-- 失敗訊息 -->
      <div v-else class="error-message">
        <p>{{ result.message || result.error || '同步過程發生錯誤' }}</p>
      </div>

      <!-- 部門結果（全部門同步時） -->
      <div v-if="result.results" class="department-results">
        <h4>各部門結果</h4>
        <div class="dept-list">
          <div
            v-for="(deptResult, dept) in result.results"
            :key="dept"
            :class="['dept-item', deptResult.success ? 'success' : 'error']"
          >
            <span class="dept-name">{{ dept }}</span>
            <span class="dept-status">
              {{ deptResult.success ? '成功' : '失敗' }}
            </span>
            <span v-if="deptResult.success" class="dept-count">
              {{ deptResult.success_count || 0 }} 筆
            </span>
          </div>
        </div>
      </div>

      <!-- 警告訊息 -->
      <div v-if="result.warnings?.length > 0" class="warnings">
        <h4>警告</h4>
        <ul>
          <li v-for="(warning, idx) in result.warnings.slice(0, 5)" :key="idx">
            {{ warning }}
          </li>
          <li v-if="result.warnings.length > 5">
            ...還有 {{ result.warnings.length - 5 }} 個警告
          </li>
        </ul>
      </div>

      <!-- 錯誤詳情 -->
      <div v-if="result.error_details?.length > 0" class="error-details">
        <h4>錯誤詳情</h4>
        <ul>
          <li v-for="(error, idx) in result.error_details.slice(0, 5)" :key="idx">
            {{ error }}
          </li>
          <li v-if="result.error_details.length > 5">
            ...還有 {{ result.error_details.length - 5 }} 個錯誤
          </li>
        </ul>
      </div>
    </div>

    <div class="result-footer">
      <span v-if="result.batch_id" class="batch-id">
        批次 ID: {{ result.batch_id.slice(0, 8) }}...
      </span>
      <span v-if="result.department" class="sync-time">
        {{ result.department }} {{ result.year }}/{{ result.month }}
      </span>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  result: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['dismiss'])
</script>

<style scoped>
.sync-result {
  border-radius: 8px;
  padding: 16px;
  margin: 16px 0;
}

.sync-result.success {
  background: #e8f5e9;
  border: 1px solid #a5d6a7;
}

.sync-result.error {
  background: #ffebee;
  border: 1px solid #ef9a9a;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.result-icon {
  font-size: 20px;
}

.sync-result.success .result-icon {
  color: #4caf50;
}

.sync-result.error .result-icon {
  color: #f44336;
}

.result-title {
  font-weight: 500;
  font-size: 16px;
}

.dismiss-btn {
  margin-left: auto;
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: var(--color-text-light);
  padding: 0 4px;
}

.dismiss-btn:hover {
  color: var(--color-text);
}

.result-body {
  margin-bottom: 12px;
}

/* 統計網格 */
.stats-grid {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 24px;
  font-weight: bold;
  color: var(--color-text);
}

.stat-value.error {
  color: #f44336;
}

.stat-item.success .stat-value {
  color: #4caf50;
}

.stat-label {
  font-size: 12px;
  color: var(--color-text-light);
}

/* 錯誤訊息 */
.error-message {
  color: #c62828;
}

.error-message p {
  margin: 0;
}

/* 部門結果 */
.department-results {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.department-results h4 {
  font-size: 13px;
  margin-bottom: 8px;
}

.dept-list {
  display: flex;
  gap: 12px;
}

.dept-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 13px;
}

.dept-item.success {
  background: rgba(76, 175, 80, 0.1);
}

.dept-item.error {
  background: rgba(244, 67, 54, 0.1);
}

.dept-name {
  font-weight: 500;
}

.dept-status {
  font-size: 12px;
}

.dept-item.success .dept-status {
  color: #4caf50;
}

.dept-item.error .dept-status {
  color: #f44336;
}

.dept-count {
  font-size: 12px;
  color: var(--color-text-light);
}

/* 警告與錯誤 */
.warnings,
.error-details {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.warnings h4 {
  color: #ff8f00;
  font-size: 13px;
  margin-bottom: 8px;
}

.error-details h4 {
  color: #f44336;
  font-size: 13px;
  margin-bottom: 8px;
}

.warnings ul,
.error-details ul {
  margin: 0;
  padding-left: 20px;
  font-size: 12px;
  color: var(--color-text-light);
}

.warnings li,
.error-details li {
  margin-bottom: 4px;
}

/* 頁腳 */
.result-footer {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--color-text-light);
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.batch-id {
  font-family: monospace;
}
</style>
