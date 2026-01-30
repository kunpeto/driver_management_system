<template>
  <div class="fault-responsibility-checklist">
    <!-- 表單標題 -->
    <div class="form-header">
      <h3 class="form-title">故障延誤責任判定查核表</h3>
      <div class="form-subtitle">（R02-R05 專用）</div>
    </div>

    <el-form ref="formRef" :model="formData" :rules="rules" label-position="top">
      <!-- 第一區塊：時間軸記錄 -->
      <div class="form-section">
        <div class="section-header">
          <span class="section-number">壹</span>
          <span class="section-title">事件時間軸記錄</span>
        </div>

        <div class="timeline-grid">
          <div class="timeline-row">
            <div class="timeline-label">
              <span class="time-code">T0</span>
              <span class="time-desc">事件/故障發生時間</span>
            </div>
            <div class="timeline-input">
              <el-time-picker
                v-model="formData.time_t0"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                placeholder="選擇時間"
                style="width: 100%"
              />
            </div>
          </div>

          <div class="timeline-row">
            <div class="timeline-label">
              <span class="time-code">T1</span>
              <span class="time-desc">司機員察覺異常時間</span>
            </div>
            <div class="timeline-input">
              <el-time-picker
                v-model="formData.time_t1"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                placeholder="選擇時間"
                style="width: 100%"
              />
            </div>
          </div>

          <div class="timeline-row">
            <div class="timeline-label">
              <span class="time-code">T2</span>
              <span class="time-desc">開始通報/處理時間</span>
            </div>
            <div class="timeline-input">
              <el-time-picker
                v-model="formData.time_t2"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                placeholder="選擇時間"
                style="width: 100%"
              />
            </div>
          </div>

          <div class="timeline-row">
            <div class="timeline-label">
              <span class="time-code">T3</span>
              <span class="time-desc">故障排除完成時間</span>
            </div>
            <div class="timeline-input">
              <el-time-picker
                v-model="formData.time_t3"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                placeholder="選擇時間"
                style="width: 100%"
              />
            </div>
          </div>

          <div class="timeline-row">
            <div class="timeline-label">
              <span class="time-code">T4</span>
              <span class="time-desc">恢復正常運轉時間</span>
            </div>
            <div class="timeline-input">
              <el-time-picker
                v-model="formData.time_t4"
                format="HH:mm:ss"
                value-format="HH:mm:ss"
                placeholder="選擇時間"
                style="width: 100%"
              />
            </div>
          </div>
        </div>

        <!-- 延誤時間 -->
        <div class="delay-section">
          <div class="delay-label">總延誤時間（依 OCC 計算或 T4-T0）</div>
          <div class="delay-input-group">
            <el-input-number
              v-model="delayMinutes"
              :min="0"
              :max="999"
              :precision="0"
              controls-position="right"
            />
            <span class="delay-unit">分</span>
            <el-input-number
              v-model="delaySeconds"
              :min="0"
              :max="59"
              :precision="0"
              controls-position="right"
            />
            <span class="delay-unit">秒</span>
            <span class="delay-total">（共 {{ formData.delay_seconds }} 秒）</span>
          </div>
        </div>
      </div>

      <!-- 第二區塊：9 項疏失查核表 -->
      <div class="form-section">
        <div class="section-header">
          <span class="section-number">貳</span>
          <span class="section-title">疏失項目查核表（9 項）</span>
        </div>

        <div class="checklist-instruction">
          請依據事件調查結果，勾選司機員於本次事件中存在之疏失項目：
        </div>

        <div class="checklist-table">
          <div class="checklist-header">
            <div class="col-check">勾選</div>
            <div class="col-num">項次</div>
            <div class="col-item">疏失項目</div>
          </div>

          <div
            v-for="(item, index) in checklistItems"
            :key="item.key"
            class="checklist-row"
            :class="{ 'checked': formData.checklist_results[item.key] }"
          >
            <div class="col-check">
              <el-checkbox
                v-model="formData.checklist_results[item.key]"
                size="large"
              />
            </div>
            <div class="col-num">{{ index + 1 }}</div>
            <div class="col-item">{{ item.label }}</div>
          </div>
        </div>

        <!-- 疏失統計 -->
        <div class="fault-summary">
          <div class="fault-count">
            <span class="fault-label">疏失項數：</span>
            <span class="fault-value" :class="faultCountClass">{{ faultCount }} / 9 項</span>
          </div>
        </div>
      </div>

      <!-- 第三區塊：責任判定結果 -->
      <div class="form-section result-section">
        <div class="section-header">
          <span class="section-number">參</span>
          <span class="section-title">責任判定結果</span>
        </div>

        <div class="result-grid">
          <div class="result-item">
            <div class="result-label">責任程度</div>
            <div class="result-value" :class="responsibilityClass">
              {{ responsibilityResult.level || '—' }}
            </div>
          </div>

          <div class="result-item">
            <div class="result-label">責任係數</div>
            <div class="result-value coefficient">
              {{ responsibilityResult.coefficient !== null ? responsibilityResult.coefficient.toFixed(1) : '—' }}
            </div>
          </div>

          <div class="result-item wide">
            <div class="result-label">計算說明</div>
            <div class="result-formula">
              <template v-if="faultCount > 0">
                疏失 {{ faultCount }} 項 →
                <span v-if="faultCount >= 7">7~9 項 = 完全責任（×1.0）</span>
                <span v-else-if="faultCount >= 4">4~6 項 = 主要責任（×0.7）</span>
                <span v-else>1~3 項 = 次要責任（×0.3）</span>
              </template>
              <template v-else>
                尚未勾選疏失項目
              </template>
            </div>
          </div>
        </div>

        <!-- 責任程度參考表 -->
        <div class="responsibility-reference">
          <div class="reference-title">責任程度對照表</div>
          <div class="reference-table">
            <div class="ref-row header">
              <div class="ref-cell">疏失項數</div>
              <div class="ref-cell">責任程度</div>
              <div class="ref-cell">責任係數</div>
            </div>
            <div class="ref-row" :class="{ active: faultCount >= 7 }">
              <div class="ref-cell">7 ~ 9 項</div>
              <div class="ref-cell danger">完全責任</div>
              <div class="ref-cell">×1.0</div>
            </div>
            <div class="ref-row" :class="{ active: faultCount >= 4 && faultCount <= 6 }">
              <div class="ref-cell">4 ~ 6 項</div>
              <div class="ref-cell warning">主要責任</div>
              <div class="ref-cell">×0.7</div>
            </div>
            <div class="ref-row" :class="{ active: faultCount >= 1 && faultCount <= 3 }">
              <div class="ref-cell">1 ~ 3 項</div>
              <div class="ref-cell info">次要責任</div>
              <div class="ref-cell">×0.3</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 第四區塊：備註 -->
      <div class="form-section">
        <div class="section-header">
          <span class="section-number">肆</span>
          <span class="section-title">備註</span>
        </div>

        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="3"
          placeholder="如有需要補充說明之事項，請填寫於此"
          class="notes-input"
        />
      </div>

      <!-- 分數計算預覽 -->
      <div v-if="basePoints !== null" class="score-preview">
        <div class="preview-title">分數計算預覽</div>
        <div class="preview-formula">
          <div class="formula-row">
            <span class="formula-label">基本扣分：</span>
            <span class="formula-value">{{ basePoints }} 分</span>
          </div>
          <div class="formula-row">
            <span class="formula-label">責任係數：</span>
            <span class="formula-value">× {{ responsibilityResult.coefficient || 0 }}</span>
          </div>
          <div class="formula-row">
            <span class="formula-label">實際扣分：</span>
            <span class="formula-value">= {{ actualPoints.toFixed(1) }} 分</span>
          </div>
          <div v-if="cumulativeCount > 1" class="formula-row">
            <span class="formula-label">累計倍率：</span>
            <span class="formula-value">× {{ cumulativeMultiplier.toFixed(1) }}（第 {{ cumulativeCount }} 次）</span>
          </div>
          <div class="formula-row final">
            <span class="formula-label">最終扣分：</span>
            <span class="formula-value">{{ finalPoints.toFixed(1) }} 分</span>
          </div>
        </div>
      </div>
    </el-form>
  </div>
</template>

<script setup>
/**
 * R02-R05 責任判定查核表
 * 對應 tasks.md T188: 建立 R02-R05 責任判定查核表元件
 * 設計參考官方表單/PDF 格式
 */
import { ref, computed, watch } from 'vue'
import { FAULT_CHECKLIST_ITEMS, RESPONSIBILITY_LEVELS } from '@/stores/assessments'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  basePoints: {
    type: Number,
    default: null
  },
  cumulativeCount: {
    type: Number,
    default: 1
  }
})

const emit = defineEmits(['update:modelValue', 'responsibility-change'])

const formRef = ref()

// 9 項疏失查核項目
const checklistItems = FAULT_CHECKLIST_ITEMS

// 表單資料
const formData = ref({
  time_t0: null,
  time_t1: null,
  time_t2: null,
  time_t3: null,
  time_t4: null,
  delay_seconds: 0,
  checklist_results: {
    awareness_delay: false,
    report_delay: false,
    unfamiliar_procedure: false,
    wrong_operation: false,
    slow_action: false,
    unconfirmed_result: false,
    no_progress_report: false,
    repeated_error: false,
    mental_state_issue: false
  },
  notes: ''
})

const rules = {}

// 延誤時間計算
const delayMinutes = computed({
  get: () => Math.floor(formData.value.delay_seconds / 60),
  set: (val) => {
    formData.value.delay_seconds = val * 60 + (formData.value.delay_seconds % 60)
  }
})

const delaySeconds = computed({
  get: () => formData.value.delay_seconds % 60,
  set: (val) => {
    formData.value.delay_seconds = Math.floor(formData.value.delay_seconds / 60) * 60 + val
  }
})

// 疏失項數計算
const faultCount = computed(() => {
  return Object.values(formData.value.checklist_results).filter(Boolean).length
})

const faultCountClass = computed(() => {
  if (faultCount.value >= 7) return 'danger'
  if (faultCount.value >= 4) return 'warning'
  if (faultCount.value >= 1) return 'info'
  return ''
})

// 責任判定結果
const responsibilityResult = computed(() => {
  const count = faultCount.value
  if (count >= 7) {
    return { level: '完全責任', coefficient: 1.0 }
  } else if (count >= 4) {
    return { level: '主要責任', coefficient: 0.7 }
  } else if (count >= 1) {
    return { level: '次要責任', coefficient: 0.3 }
  }
  return { level: null, coefficient: null }
})

const responsibilityClass = computed(() => {
  const level = responsibilityResult.value.level
  if (level === '完全責任') return 'danger'
  if (level === '主要責任') return 'warning'
  if (level === '次要責任') return 'info'
  return ''
})

// 分數計算
const actualPoints = computed(() => {
  if (props.basePoints === null || !responsibilityResult.value.coefficient) return 0
  return props.basePoints * responsibilityResult.value.coefficient
})

const cumulativeMultiplier = computed(() => {
  if (props.cumulativeCount <= 1) return 1.0
  return 1.0 + 0.5 * (props.cumulativeCount - 1)
})

const finalPoints = computed(() => {
  return actualPoints.value * cumulativeMultiplier.value
})

// 初始化資料
watch(() => props.modelValue, (val) => {
  if (val && Object.keys(val).length > 0) {
    formData.value = {
      ...formData.value,
      ...val,
      checklist_results: {
        ...formData.value.checklist_results,
        ...(val.checklist_results || {})
      }
    }
  }
}, { immediate: true, deep: true })

// 資料變更時同步
watch(formData, (val) => {
  emit('update:modelValue', {
    ...val,
    fault_count: faultCount.value,
    responsibility_level: responsibilityResult.value.level,
    responsibility_coefficient: responsibilityResult.value.coefficient
  })

  emit('responsibility-change', {
    faultCount: faultCount.value,
    level: responsibilityResult.value.level,
    coefficient: responsibilityResult.value.coefficient
  })
}, { deep: true })

// 驗證
function validate() {
  return formRef.value?.validate()
}

// 取得資料
function getData() {
  return {
    ...formData.value,
    fault_count: faultCount.value,
    responsibility_level: responsibilityResult.value.level,
    responsibility_coefficient: responsibilityResult.value.coefficient
  }
}

defineExpose({ validate, getData })
</script>

<style scoped>
.fault-responsibility-checklist {
  background: #fff;
  border: 2px solid #333;
  padding: 0;
  font-family: "Microsoft JhengHei", "微軟正黑體", sans-serif;
}

/* 表單標題 */
.form-header {
  background: #f5f5f5;
  border-bottom: 2px solid #333;
  padding: 16px;
  text-align: center;
}

.form-title {
  margin: 0;
  font-size: 20px;
  font-weight: bold;
  letter-spacing: 2px;
}

.form-subtitle {
  margin-top: 4px;
  font-size: 14px;
  color: #666;
}

/* 區塊樣式 */
.form-section {
  border-bottom: 1px solid #ccc;
  padding: 16px 20px;
}

.form-section:last-child {
  border-bottom: none;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px dashed #999;
}

.section-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: #333;
  color: #fff;
  font-size: 14px;
  font-weight: bold;
  margin-right: 10px;
}

.section-title {
  font-size: 16px;
  font-weight: bold;
}

/* 時間軸 */
.timeline-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.timeline-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.timeline-label {
  display: flex;
  align-items: center;
  width: 220px;
  gap: 10px;
}

.time-code {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: #409eff;
  color: #fff;
  font-weight: bold;
  border-radius: 4px;
}

.time-desc {
  font-size: 14px;
}

.timeline-input {
  flex: 1;
  max-width: 200px;
}

/* 延誤時間 */
.delay-section {
  margin-top: 20px;
  padding: 16px;
  background: #fff9e6;
  border: 1px solid #f0c000;
  border-radius: 4px;
}

.delay-label {
  font-weight: bold;
  margin-bottom: 10px;
}

.delay-input-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.delay-unit {
  font-size: 14px;
  color: #666;
}

.delay-total {
  margin-left: 16px;
  font-size: 14px;
  color: #999;
}

/* 查核表說明 */
.checklist-instruction {
  margin-bottom: 16px;
  padding: 10px;
  background: #f0f9ff;
  border-left: 4px solid #409eff;
  font-size: 14px;
}

/* 查核表表格 */
.checklist-table {
  border: 1px solid #333;
}

.checklist-header {
  display: flex;
  background: #333;
  color: #fff;
  font-weight: bold;
}

.checklist-row {
  display: flex;
  border-bottom: 1px solid #ddd;
  transition: background 0.2s;
}

.checklist-row:last-child {
  border-bottom: none;
}

.checklist-row:hover {
  background: #f5f5f5;
}

.checklist-row.checked {
  background: #fff3f3;
}

.col-check {
  width: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  border-right: 1px solid #ddd;
}

.col-num {
  width: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 8px;
  border-right: 1px solid #ddd;
  font-weight: bold;
}

.col-item {
  flex: 1;
  padding: 12px 16px;
  display: flex;
  align-items: center;
}

.checklist-header .col-check,
.checklist-header .col-num,
.checklist-header .col-item {
  border-right-color: #555;
}

/* 疏失統計 */
.fault-summary {
  margin-top: 16px;
  padding: 12px 16px;
  background: #f5f5f5;
  border-radius: 4px;
  text-align: right;
}

.fault-count {
  font-size: 16px;
}

.fault-label {
  color: #666;
}

.fault-value {
  font-weight: bold;
  margin-left: 8px;
}

.fault-value.danger { color: #f56c6c; }
.fault-value.warning { color: #e6a23c; }
.fault-value.info { color: #409eff; }

/* 結果區塊 */
.result-section {
  background: #fafafa;
}

.result-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.result-item {
  padding: 16px;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.result-item.wide {
  grid-column: 1 / -1;
}

.result-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.result-value {
  font-size: 24px;
  font-weight: bold;
}

.result-value.danger { color: #f56c6c; }
.result-value.warning { color: #e6a23c; }
.result-value.info { color: #409eff; }
.result-value.coefficient { color: #333; }

.result-formula {
  font-size: 14px;
  color: #666;
}

/* 責任程度參考表 */
.responsibility-reference {
  margin-top: 16px;
}

.reference-title {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.reference-table {
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.ref-row {
  display: flex;
  border-bottom: 1px solid #ddd;
}

.ref-row:last-child {
  border-bottom: none;
}

.ref-row.header {
  background: #f5f5f5;
  font-weight: bold;
}

.ref-row.active {
  background: #fff9e6;
  font-weight: bold;
}

.ref-cell {
  flex: 1;
  padding: 10px 16px;
  text-align: center;
  border-right: 1px solid #ddd;
}

.ref-cell:last-child {
  border-right: none;
}

.ref-cell.danger { color: #f56c6c; font-weight: bold; }
.ref-cell.warning { color: #e6a23c; font-weight: bold; }
.ref-cell.info { color: #409eff; font-weight: bold; }

/* 備註輸入 */
.notes-input {
  font-family: inherit;
}

/* 分數計算預覽 */
.score-preview {
  margin: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.preview-title {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 12px;
}

.preview-formula {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.formula-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.formula-row.final {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(255,255,255,0.3);
  font-size: 18px;
  font-weight: bold;
}

.formula-label {
  opacity: 0.9;
}

.formula-value {
  font-weight: 500;
}
</style>
