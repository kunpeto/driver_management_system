<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 標題 -->
      <div class="login-header">
        <h1 class="login-title">司機員管理系統</h1>
        <p class="login-subtitle">新北捷運輕軌營運處車務中心</p>
      </div>

      <!-- 登入表單 -->
      <form class="login-form" @submit.prevent="handleSubmit">
        <!-- 錯誤訊息 -->
        <div v-if="errorMessage" class="error-alert">
          {{ errorMessage }}
        </div>

        <!-- 使用者名稱 -->
        <div class="form-group">
          <label class="form-label">使用者名稱</label>
          <AppInput
            v-model="form.username"
            placeholder="請輸入使用者名稱"
            :disabled="loading"
            autofocus
          >
            <template #prefix>
              <span class="input-icon">👤</span>
            </template>
          </AppInput>
        </div>

        <!-- 密碼 -->
        <div class="form-group">
          <label class="form-label">密碼</label>
          <AppInput
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="請輸入密碼"
            :disabled="loading"
            @keyup.enter="handleSubmit"
          >
            <template #prefix>
              <span class="input-icon">🔒</span>
            </template>
            <template #suffix>
              <button
                type="button"
                class="password-toggle"
                @click="showPassword = !showPassword"
              >
                {{ showPassword ? '🙈' : '👁️' }}
              </button>
            </template>
          </AppInput>
        </div>

        <!-- 記住我 -->
        <div class="form-group remember-group">
          <label class="checkbox-label">
            <input
              type="checkbox"
              v-model="form.remember"
              :disabled="loading"
            />
            <span>記住我</span>
          </label>
        </div>

        <!-- 登入按鈕 -->
        <div class="form-group">
          <AppButton
            type="submit"
            variant="primary"
            :loading="loading"
            :disabled="!isFormValid"
            block
          >
            登入
          </AppButton>
        </div>
      </form>

      <!-- 頁尾 -->
      <div class="login-footer">
        <p>如需協助，請聯繫系統管理員</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppInput from '@/components/common/AppInput.vue'
import AppButton from '@/components/common/AppButton.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// 表單資料
const form = ref({
  username: '',
  password: '',
  remember: false
})

// 顯示密碼
const showPassword = ref(false)

// 載入狀態
const loading = ref(false)

// 錯誤訊息
const errorMessage = ref('')

// 表單驗證
const isFormValid = computed(() => {
  return form.value.username.trim() !== '' && form.value.password.trim() !== ''
})

// 提交登入
async function handleSubmit() {
  if (!isFormValid.value || loading.value) return

  loading.value = true
  errorMessage.value = ''

  try {
    await authStore.login(
      form.value.username.trim(),
      form.value.password,
      form.value.remember
    )

    // 登入成功，導向原本要去的頁面或首頁
    const redirectTo = route.query.redirect || '/'
    router.push(redirectTo)

  } catch (err) {
    console.error('登入失敗:', err)
    errorMessage.value = err.response?.data?.detail || '登入失敗，請檢查帳號密碼'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 400px;
  background: var(--color-background);
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.login-header {
  padding: 32px 32px 24px;
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0 0 8px;
}

.login-subtitle {
  font-size: 14px;
  margin: 0;
  opacity: 0.9;
}

.login-form {
  padding: 32px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: 8px;
}

.error-alert {
  background: #ffebee;
  color: #c62828;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin-bottom: 20px;
}

.input-icon {
  opacity: 0.5;
  font-size: 16px;
}

.password-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  font-size: 16px;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.password-toggle:hover {
  opacity: 1;
}

.remember-group {
  margin-bottom: 24px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--color-text-light);
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.login-footer {
  padding: 16px 32px 24px;
  text-align: center;
}

.login-footer p {
  font-size: 12px;
  color: var(--color-text-light);
  margin: 0;
}
</style>
