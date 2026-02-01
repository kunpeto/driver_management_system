<template>
  <form class="transfer-form" @submit.prevent="handleSubmit">
    <!-- 員工資訊 -->
    <div class="employee-info">
      <div class="info-row">
        <span class="label">員工：</span>
        <span class="value">{{ employee.employee_name }} ({{ employee.employee_id }})</span>
      </div>
      <div class="info-row">
        <span class="label">現職部門：</span>
        <span :class="['dept-badge', getDeptClass(employee.current_department)]">
          {{ employee.current_department }}
        </span>
      </div>
    </div>

    <!-- 調動資訊 -->
    <div class="form-section">
      <!-- 目標部門 -->
      <div class="form-group">
        <label class="form-label required">調動至</label>
        <select
          v-model="form.to_department"
          class="form-select"
          :class="{ error: errors.to_department }"
        >
          <option value="">請選擇部門</option>
          <option
            v-for="dept in availableDepartments"
            :key="dept"
            :value="dept"
          >
            {{ dept }}
          </option>
        </select>
        <p v-if="errors.to_department" class="form-error">
          {{ errors.to_department }}
        </p>
      </div>

      <!-- 調動日期 -->
      <div class="form-group">
        <label class="form-label required">生效日期</label>
        <input
          v-model="form.transfer_date"
          type="date"
          class="form-input"
          :class="{ error: errors.transfer_date }"
        />
        <p v-if="errors.transfer_date" class="form-error">
          {{ errors.transfer_date }}
        </p>
      </div>

      <!-- 調動原因 -->
      <div class="form-group">
        <label class="form-label">調動原因</label>
        <textarea
          v-model="form.reason"
          class="form-textarea"
          placeholder="選填，說明調動原因"
          rows="3"
        ></textarea>
      </div>
    </div>

    <!-- 調動預覽 -->
    <div v-if="form.to_department" class="transfer-preview">
      <div class="preview-title">調動預覽</div>
      <div class="preview-content">
        <span :class="['dept-badge', getDeptClass(employee.current_department)]">
          {{ employee.current_department }}
        </span>
        <span class="arrow">→</span>
        <span :class="['dept-badge', getDeptClass(form.to_department)]">
          {{ form.to_department }}
        </span>
      </div>
    </div>

    <!-- 提交錯誤訊息 -->
    <div v-if="submitError" class="submit-error">
      {{ submitError }}
    </div>

    <!-- 操作按鈕 -->
    <div class="form-actions">
      <AppButton type="button" @click="$emit('cancel')">
        取消
      </AppButton>
      <AppButton type="submit" :loading="saving" variant="primary">
        確認調動
      </AppButton>
    </div>
  </form>
</template>

<script setup>
import { ref, computed } from 'vue'
import { DEPARTMENT_LIST } from '@/constants/departments'
import AppButton from '@/components/common/AppButton.vue'

const props = defineProps({
  employee: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['submit', 'cancel'])

// 所有部門（從常數取得）
const allDepartments = DEPARTMENT_LIST.map(d => d.value)

// 表單資料
const form = ref({
  to_department: '',
  transfer_date: new Date().toISOString().split('T')[0],
  reason: ''
})

// 表單錯誤
const errors = ref({})

// 提交錯誤（API 回傳的錯誤）
const submitError = ref(null)

// 儲存中狀態
const saving = ref(false)

// 可選部門（排除現職部門）
const availableDepartments = computed(() => {
  return allDepartments.filter(dept => dept !== props.employee.current_department)
})

// 方法
function getDeptClass(department) {
  return department === '淡海' ? 'danhai' : 'ankeng'
}

// 驗證表單
function validateForm() {
  errors.value = {}
  let valid = true

  if (!form.value.to_department) {
    errors.value.to_department = '請選擇目標部門'
    valid = false
  }

  if (!form.value.transfer_date) {
    errors.value.transfer_date = '請選擇生效日期'
    valid = false
  }

  return valid
}

// 提交表單
async function handleSubmit() {
  if (!validateForm()) return

  saving.value = true
  submitError.value = null

  try {
    const submitData = {
      to_department: form.value.to_department,
      transfer_date: form.value.transfer_date,
      reason: form.value.reason || null
    }

    emit('submit', submitData)
  } catch (err) {
    console.error('調動提交錯誤:', err)
    submitError.value = err.response?.data?.detail || err.message || '發生未知錯誤'
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.transfer-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.employee-info {
  background: var(--color-background-soft);
  padding: 16px;
  border-radius: 8px;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  color: var(--color-text-light);
  font-size: 14px;
}

.info-row .value {
  font-weight: 500;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-label {
  font-weight: 500;
  font-size: 14px;
  color: var(--color-text);
}

.form-label.required::after {
  content: ' *';
  color: #ef5350;
}

.form-select,
.form-input {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-background);
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-select:focus,
.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-select.error,
.form-input.error {
  border-color: #ef5350;
}

.form-textarea {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-background);
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
}

.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-error {
  font-size: 12px;
  color: #ef5350;
  margin: 0;
}

.transfer-preview {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  border: 2px dashed var(--color-border);
}

.preview-title {
  font-size: 12px;
  color: var(--color-text-light);
  margin-bottom: 12px;
}

.preview-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.arrow {
  font-size: 20px;
  color: var(--color-text-light);
}

.dept-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
}

.dept-badge.danhai {
  background: #e3f2fd;
  color: #1976d2;
}

.dept-badge.ankeng {
  background: #fff3e0;
  color: #f57c00;
}

.submit-error {
  color: #ef5350;
  background: #ffebee;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 14px;
  margin-top: 8px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}
</style>
