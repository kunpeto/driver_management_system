<template>
  <form class="employee-form" @submit.prevent="handleSubmit">
    <!-- 員工編號 -->
    <div class="form-group">
      <label class="form-label required">員工編號</label>
      <AppInput
        v-model="form.employee_id"
        :disabled="isEditMode"
        placeholder="例如：1011M0095"
        :error="errors.employee_id"
      />
      <p class="form-hint" v-if="!isEditMode">
        格式：YYMM + 類型碼 + 4位序號（如 1011M0095）
      </p>
    </div>

    <!-- 姓名 -->
    <div class="form-group">
      <label class="form-label required">姓名</label>
      <AppInput
        v-model="form.employee_name"
        placeholder="員工姓名"
        :error="errors.employee_name"
      />
    </div>

    <!-- 部門 -->
    <div class="form-group">
      <label class="form-label required">部門</label>
      <select
        v-model="form.current_department"
        class="form-select"
        :disabled="isEditMode"
        :class="{ error: errors.current_department }"
      >
        <option value="">請選擇部門</option>
        <option
          v-for="dept in DEPARTMENT_LIST"
          :key="dept.value"
          :value="dept.value"
        >
          {{ dept.label }}
        </option>
      </select>
      <p class="form-error" v-if="errors.current_department">
        {{ errors.current_department }}
      </p>
      <p class="form-hint" v-if="isEditMode">
        部門變更請使用調動功能
      </p>
    </div>

    <!-- 電話 -->
    <div class="form-group">
      <label class="form-label">電話</label>
      <AppInput
        v-model="form.phone"
        placeholder="聯絡電話"
        :error="errors.phone"
      />
    </div>

    <!-- 電子郵件 -->
    <div class="form-group">
      <label class="form-label">電子郵件</label>
      <AppInput
        v-model="form.email"
        type="email"
        placeholder="電子郵件"
        :error="errors.email"
      />
    </div>

    <!-- 緊急聯絡人 -->
    <div class="form-row">
      <div class="form-group">
        <label class="form-label">緊急聯絡人</label>
        <AppInput
          v-model="form.emergency_contact"
          placeholder="緊急聯絡人姓名"
        />
      </div>
      <div class="form-group">
        <label class="form-label">緊急聯絡電話</label>
        <AppInput
          v-model="form.emergency_phone"
          placeholder="緊急聯絡電話"
        />
      </div>
    </div>

    <!-- 提交錯誤訊息 -->
    <div v-if="submitError" class="submit-error">
      {{ submitError }}
    </div>

    <!-- 表單操作 -->
    <div class="form-actions">
      <AppButton type="button" @click="$emit('cancel')">
        取消
      </AppButton>
      <AppButton type="submit" :loading="saving" variant="primary">
        {{ isEditMode ? '更新' : '建立' }}
      </AppButton>
    </div>
  </form>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useEmployeesStore } from '@/stores/employees'
import { DEPARTMENT_LIST } from '@/constants/departments'
import AppInput from '@/components/common/AppInput.vue'
import AppButton from '@/components/common/AppButton.vue'

const props = defineProps({
  employee: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const store = useEmployeesStore()

// 表單資料
const form = ref({
  employee_id: '',
  employee_name: '',
  current_department: '',
  phone: '',
  email: '',
  emergency_contact: '',
  emergency_phone: ''
})

// 表單錯誤
const errors = ref({})

// 提交錯誤（API 回傳的錯誤）
const submitError = ref(null)

// 儲存中狀態
const saving = ref(false)

// 是否為編輯模式
const isEditMode = computed(() => !!props.employee)

// 初始化表單
onMounted(() => {
  if (props.employee) {
    form.value = {
      employee_id: props.employee.employee_id || '',
      employee_name: props.employee.employee_name || '',
      current_department: props.employee.current_department || '',
      phone: props.employee.phone || '',
      email: props.employee.email || '',
      emergency_contact: props.employee.emergency_contact || '',
      emergency_phone: props.employee.emergency_phone || ''
    }
  }
})

// 監聽 employee 變化
watch(() => props.employee, (newVal) => {
  if (newVal) {
    form.value = {
      employee_id: newVal.employee_id || '',
      employee_name: newVal.employee_name || '',
      current_department: newVal.current_department || '',
      phone: newVal.phone || '',
      email: newVal.email || '',
      emergency_contact: newVal.emergency_contact || '',
      emergency_phone: newVal.emergency_phone || ''
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// 驗證表單
function validateForm() {
  errors.value = {}
  let valid = true

  // 員工編號驗證（僅新增時）
  if (!isEditMode.value) {
    if (!form.value.employee_id) {
      errors.value.employee_id = '請輸入員工編號'
      valid = false
    } else if (!/^\d{4}[A-Za-z]\d{4}$/.test(form.value.employee_id)) {
      errors.value.employee_id = '員工編號格式錯誤'
      valid = false
    }
  }

  // 姓名驗證
  if (!form.value.employee_name) {
    errors.value.employee_name = '請輸入姓名'
    valid = false
  }

  // 部門驗證（僅新增時）
  if (!isEditMode.value && !form.value.current_department) {
    errors.value.current_department = '請選擇部門'
    valid = false
  }

  // 電子郵件格式驗證
  if (form.value.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email)) {
    errors.value.email = '電子郵件格式錯誤'
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
    // 檢查員工編號是否已存在（僅新增時）
    if (!isEditMode.value) {
      const exists = await store.checkEmployeeExists(form.value.employee_id)
      if (exists) {
        errors.value.employee_id = '此員工編號已存在'
        saving.value = false
        return
      }
    }

    // 準備提交資料
    const submitData = isEditMode.value
      ? {
          employee_name: form.value.employee_name,
          phone: form.value.phone || null,
          email: form.value.email || null,
          emergency_contact: form.value.emergency_contact || null,
          emergency_phone: form.value.emergency_phone || null
        }
      : {
          employee_id: form.value.employee_id.toUpperCase(),
          employee_name: form.value.employee_name,
          current_department: form.value.current_department,
          phone: form.value.phone || null,
          email: form.value.email || null,
          emergency_contact: form.value.emergency_contact || null,
          emergency_phone: form.value.emergency_phone || null
        }

    emit('submit', submitData)
  } catch (err) {
    console.error('表單提交錯誤:', err)
    submitError.value = err.response?.data?.detail || err.message || '發生未知錯誤'
  } finally {
    saving.value = false
  }
}

// 重置表單
function resetForm() {
  form.value = {
    employee_id: '',
    employee_name: '',
    current_department: '',
    phone: '',
    email: '',
    emergency_contact: '',
    emergency_phone: ''
  }
  errors.value = {}
}
</script>

<style scoped>
.employee-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
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

.form-select {
  padding: 10px 12px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  background: var(--color-background);
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-select:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-select.error {
  border-color: #ef5350;
}

.form-select:disabled {
  background: var(--color-background-soft);
  cursor: not-allowed;
  opacity: 0.7;
}

.form-hint {
  font-size: 12px;
  color: var(--color-text-light);
  margin: 0;
}

.form-error {
  font-size: 12px;
  color: #ef5350;
  margin: 0;
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
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}
</style>
