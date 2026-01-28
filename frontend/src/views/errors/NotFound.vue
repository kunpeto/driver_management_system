<template>
  <div class="error-page">
    <el-result
      icon="warning"
      title="404"
      sub-title="找不到您要的頁面"
    >
      <template #extra>
        <el-button type="primary" @click="goHome">返回首頁</el-button>
        <el-button @click="goBack">返回上一頁</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push({ name: 'dashboard' })
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.error-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
}
</style>
