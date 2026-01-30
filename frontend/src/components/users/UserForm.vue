<template>
  <form class="user-form" @submit.prevent="handleSubmit">
    <!-- 使用者名稱 -->
    <div class="form-group">
      <label class="form-label required">使用者名稱</label>
      <AppInput
        v-model="form.username"
        :disabled="isEditMode"
        placeholder="3-50 個字元"
        :error="errors.username"
      />
      <p class="form-hint" v-if="!isEditMode">
        登入時使用的帳號名稱，建立後不可變更
      </p>
    </div>

    <!-- 密碼（僅新增時） -->
    <div class="form-group" v-if="!isEditMode">
      <label class="form-label required">密碼</label>
      <AppInput
        v-model="form.password"
        type="password"
        placeholder="至少 8 個字元，含大小寫字母和數字"
        :error="errors.password"
      />
    </div>

    <!-- 顯示名稱 -->
    <div class="form-group">
      <label class="form-label required">顯示名稱</label>
      <AppInput
        v-model="form.display_name"
        placeholder="使用者的顯示名稱"
        :error="errors.display_name"
      />
    </div>

    <!-- 電子郵件 -->
    <div class="form-group">
      <label class="form-label">電子郵件</label>
      <AppInput
        v-model="form.email"
        type="email"
        placeholder="選填"
        :error="errors.email"
      />
    </div>

    <!-- 角色 -->
    <div class="form-group">
      <label class="form-label required">角色</label>
      <select
        v-model="form.role"
        class="form-select"
        :class="{ error: errors.role }"
        @change="handleRoleChange"
      >
        <option value="">請選擇角色</option>
        <option value="admin">管理員</option>
        <option value="manager">主管</option>
        <option value="staff">值班台人員</option>
      </select>
      <p class="form-error" v-if="errors.role">{{ errors.role }}</p>
      <div class="role-description" v-if="form.role">
        <p v-if="form.role === 'admin'">管理員：可存取所有功能，管理使用者帳號</p>
        <p v-else-if="form.role === 'manager'">主管：可查看和編輯所有部門的資料</p>
        <p v-else-if="form.role === 'staff'">值班台人員：僅能編輯自己部門的資料</p>
      </div>
    </div>

    <!-- 部門（非 admin 必填） -->
    <div class="form-group" v-if="form.role !== 'admin'">
      <label class="form-label required">部門</label>
      <select
        v-model="form.department"
        class="form-select"
        :class="{ error: errors.department }"
      >
        <option value="">請選擇部門</option>
        <option value="淡海">淡海</option>
        <option value="安坑">安坑</option>
      </select>
      <p class="form-error" v-if="errors.department">{{ errors.department }}</p>
    </div>

    <!-- 是否啟用 -->
    <div class="form-group">
      <label class="checkbox-label">
        <input type="checkbox" v-model="form.is_active" />
        <span>啟用帳號</span>
      </label>
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
        {{ isEditMode ? '更新' : '建立' }}
      </AppButton>
    </div>
  </form>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import AppInput from '@/components/common/AppInput.vue'
import AppButton from '@/components/common/AppButton.vue'

const props = defineProps({
  user: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

// 表單資料
const form = ref({
  username: '',
  password: '',
  display_name: '',
  email: '',
  role: '',
  department: '',
  is_active: true
})

// 表單錯誤
const errors = ref({})

// 提交錯誤
const submitError = ref(null)

// 儲存中
const saving = ref(false)

// 是否為編輯模式
const isEditMode = computed(() => !!props.user)

// 初始化表單
onMounted(() => {
  if (props.user) {
    form.value = {
      username: props.user.username || '',
      password: '',
      display_name: props.user.display_name || '',
      email: props.user.email || '',
      role: props.user.role || '',
      department: props.user.department || '',
      is_active: props.user.is_active ?? true
    }
  }
})

// 監聽 user 變化
watch(() => props.user, (newVal) => {
  if (newVal) {
    form.value = {
      username: newVal.username || '',
      password: '',
      display_name: newVal.display_name || '',
      email: newVal.email || '',
      role: newVal.role || '',
      department: newVal.department || '',
      is_active: newVal.is_active ?? true
    }
  } else {
    resetForm()
  }
}, { immediate: true })

// 角色變更時清除部門（如果是 admin）
function handleRoleChange() {
  if (form.value.role === 'admin') {
    form.value.department = ''
  }
}

// 驗證表單
function validateForm() {
  errors.value = {}
  let valid = true

  // 使用者名稱（僅新增時）
  if (!isEditMode.value) {
    if (!form.value.username) {
      errors.value.username = '請輸入使用者名稱'
      valid = false
    } else if (form.value.username.length < 3) {
      errors.value.username = '使用者名稱至少需要 3 個字元'
      valid = false
    }
  }

  // 密碼（僅新增時）
  if (!isEditMode.value) {
    if (!form.value.password) {
      errors.value.password = '請輸入密碼'
      valid = false
    } else {
      // 與後端 password.py 的 is_password_strong 規則一致
      const password = form.value.password
      if (password.length < 8) {
        errors.value.password = '密碼長度至少需要 8 個字元'
        valid = false
      } else if (!/[A-Z]/.test(password)) {
        errors.value.password = '密碼需要包含至少一個大寫字母'
        valid = false
      } else if (!/[a-z]/.test(password)) {
        errors.value.password = '密碼需要包含至少一個小寫字母'
        valid = false
      } else if (!/\d/.test(password)) {
        errors.value.password = '密碼需要包含至少一個數字'
        valid = false
      }
    }
  }

  // 顯示名稱
  if (!form.value.display_name) {
    errors.value.display_name = '請輸入顯示名稱'
    valid = false
  }

  // 角色
  if (!form.value.role) {
    errors.value.role = '請選擇角色'
    valid = false
  }

  // 部門（非 admin 必填）
  if (form.value.role !== 'admin' && !form.value.department) {
    errors.value.department = '請選擇部門'
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
      display_name: form.value.display_name,
      email: form.value.email || null,
      role: form.value.role,
      department: form.value.role === 'admin' ? null : form.value.department,
      is_active: form.value.is_active
    }

    // 新增時加入 username 和 password
    if (!isEditMode.value) {
      submitData.username = form.value.username
      submitData.password = form.value.password
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
    username: '',
    password: '',
    display_name: '',
    email: '',
    role: '',
    department: '',
    is_active: true
  }
  errors.value = {}
}
</script>

<style scoped>
.user-form {
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

.role-description {
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--color-background-soft);
  border-radius: 4px;
}

.role-description p {
  font-size: 12px;
  color: var(--color-text-light);
  margin: 0;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.submit-error {
  color: #ef5350;
  background: #ffebee;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 14px;
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
