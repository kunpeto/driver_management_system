<template>
  <div class="dashboard-page">
    <h1>司機員管理系統</h1>
    <p>歡迎使用系統</p>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>員工管理</span>
          </template>
          <router-link to="/employees">
            <el-button type="primary">前往員工列表</el-button>
          </router-link>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>事件履歷</span>
          </template>
          <router-link to="/profiles">
            <el-button type="primary">前往履歷管理</el-button>
          </router-link>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span>考核記錄</span>
          </template>
          <router-link to="/assessment-records">
            <el-button type="primary">前往考核管理</el-button>
          </router-link>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
/**
 * 儀表板頁面
 */
</script>

<style scoped>
.dashboard-page {
  padding: 20px;
}

h1 {
  margin-bottom: 20px;
}

.el-card {
  margin-bottom: 20px;
}
</style>
