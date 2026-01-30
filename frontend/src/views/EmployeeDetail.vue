<template>
  <div class="employee-detail-page">
    <div class="page-header">
      <el-button @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <h1>員工詳情</h1>
    </div>

    <el-card v-loading="loading">
      <template v-if="employee">
        <el-descriptions title="基本資訊" :column="2" border>
          <el-descriptions-item label="員工編號">{{ employee.employee_id }}</el-descriptions-item>
          <el-descriptions-item label="姓名">{{ employee.employee_name }}</el-descriptions-item>
          <el-descriptions-item label="部門">{{ employee.current_department }}</el-descriptions-item>
          <el-descriptions-item label="入職年月">{{ employee.hire_year_month }}</el-descriptions-item>
          <el-descriptions-item label="聯絡電話">{{ employee.contact_phone || '—' }}</el-descriptions-item>
          <el-descriptions-item label="狀態">
            <el-tag :type="employee.is_active ? 'success' : 'info'">
              {{ employee.is_active ? '在職' : '離職' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h3>考核摘要</h3>
        <AssessmentSummary
          v-if="employee"
          :employee-id="employee.id"
          :year="currentYear"
        />
      </template>
      <el-empty v-else description="員工不存在" />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { cloudApi } from '@/services/api'
import AssessmentSummary from '@/components/assessments/AssessmentSummary.vue'

const route = useRoute()
const loading = ref(false)
const employee = ref(null)
const currentYear = new Date().getFullYear()

async function loadEmployee() {
  const id = route.params.id
  if (!id) return

  loading.value = true
  try {
    const response = await cloudApi.get(`/api/employees/${id}`)
    employee.value = response.data
  } catch (err) {
    console.error('載入員工資料失敗:', err)
    employee.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadEmployee()
})
</script>

<style scoped>
.employee-detail-page {
  padding: 20px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
}

h3 {
  margin: 16px 0;
}
</style>
