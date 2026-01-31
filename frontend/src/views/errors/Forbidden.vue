<template>
  <div class="error-page">
    <div class="error-content">
      <div class="error-code">403</div>
      <h1 class="error-title">權限不足</h1>
      <p class="error-message">您沒有權限存取此頁面。</p>
      <div class="error-actions">
        <AppButton @click="goBack">返回上一頁</AppButton>
        <AppButton type="primary" @click="goHome">回到首頁</AppButton>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import AppButton from '@/components/common/AppButton.vue'

const router = useRouter()

function goBack() {
  router.back()
}

function goHome() {
  router.push('/dashboard')
}
</script>

<style scoped>
.error-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: var(--color-background-soft);
}

.error-content {
  text-align: center;
  max-width: 400px;
}

.error-code {
  font-size: 120px;
  font-weight: 700;
  color: #ff9800;
  line-height: 1;
  margin-bottom: 16px;
}

.error-title {
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 12px;
}

.error-message {
  font-size: 16px;
  color: var(--color-text-light);
  margin: 0 0 32px;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
