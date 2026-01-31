<template>
  <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
    <el-form-item label="員工" prop="employee_id">
      <el-select
        v-model="formData.employee_id"
        filterable
        remote
        :remote-method="searchEmployees"
        placeholder="輸入姓名或編號搜尋"
        style="width: 100%"
      >
        <el-option
          v-for="emp in employees"
          :key="emp.id"
          :label="`${emp.employee_id} ${emp.employee_name}`"
          :value="emp.id"
        />
      </el-select>
    </el-form-item>

    <el-form-item label="事件日期" prop="event_date">
      <el-date-picker
        v-model="formData.event_date"
        type="date"
        placeholder="選擇日期"
        value-format="YYYY-MM-DD"
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="事件時間">
      <el-time-picker
        v-model="formData.event_time"
        placeholder="選擇時間"
        format="HH:mm"
        value-format="HH:mm"
        style="width: 100%"
      />
    </el-form-item>

    <el-form-item label="部門" prop="department">
      <el-select v-model="formData.department" placeholder="選擇部門" style="width: 100%">
        <el-option label="淡海" value="淡海" />
        <el-option label="安坑" value="安坑" />
      </el-select>
    </el-form-item>

    <el-form-item label="事件地點">
      <el-input v-model="formData.event_location" placeholder="例：淡水站" />
    </el-form-item>

    <el-form-item label="列車車號">
      <el-input v-model="formData.train_number" placeholder="例：1234" />
    </el-form-item>

    <el-form-item label="事件標題">
      <el-input v-model="formData.event_title" placeholder="簡述事件" />
    </el-form-item>

    <el-form-item label="事件描述">
      <el-input
        v-model="formData.event_description"
        type="textarea"
        :rows="4"
        placeholder="詳細描述事件經過"
      />
    </el-form-item>

    <el-form-item label="資料來源">
      <el-input v-model="formData.data_source" placeholder="例：路巡、監視器、旅客申訴" />
    </el-form-item>

    <el-form-item label="考核項目">
      <el-input v-model="formData.assessment_item" placeholder="例：D01 遲到" />
    </el-form-item>

    <el-form-item label="考核分數">
      <el-input-number v-model="formData.assessment_score" :min="-100" :max="100" />
    </el-form-item>

    <el-form-item>
      <el-button type="primary" @click="handleSubmit">{{ isEdit ? '更新' : '建立' }}</el-button>
      <el-button @click="$emit('cancel')">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
/**
 * 基本履歷表單
 * 對應 tasks.md T151: 建立基本履歷新增表單
 */
import { ref, computed, onMounted, watch } from 'vue'
import { cloudApi } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  profile: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['submit', 'cancel'])

const authStore = useAuthStore()
const formRef = ref()
const employees = ref([])

const isEdit = computed(() => !!props.profile)

const formData = ref({
  employee_id: null,
  event_date: null,
  event_time: null,
  department: authStore.user?.department || '淡海',
  event_location: '',
  train_number: '',
  event_title: '',
  event_description: '',
  data_source: '',
  assessment_item: '',
  assessment_score: null
})

const rules = {
  employee_id: [{ required: true, message: '請選擇員工', trigger: 'change' }],
  event_date: [{ required: true, message: '請選擇事件日期', trigger: 'change' }],
  department: [{ required: true, message: '請選擇部門', trigger: 'change' }]
}

// 編輯模式時填入資料
watch(() => props.profile, (val) => {
  if (val) {
    formData.value = {
      employee_id: val.employee_id,
      event_date: val.event_date,
      event_time: val.event_time,
      department: val.department,
      event_location: val.event_location || '',
      train_number: val.train_number || '',
      event_title: val.event_title || '',
      event_description: val.event_description || '',
      data_source: val.data_source || '',
      assessment_item: val.assessment_item || '',
      assessment_score: val.assessment_score
    }
  }
}, { immediate: true })

// 搜尋員工
async function searchEmployees(query) {
  if (!query) {
    employees.value = []
    return
  }
  try {
    const response = await cloudApi.get('/employees', {
      params: { search: query, limit: 20 }
    })
    employees.value = response.data
  } catch (err) {
    console.error('搜尋員工失敗:', err)
  }
}

// 提交表單
async function handleSubmit() {
  try {
    await formRef.value.validate()
    emit('submit', formData.value)
  } catch (err) {
    console.error('表單驗證失敗:', err)
  }
}

onMounted(() => {
  // 如果是編輯模式，載入員工資訊
  if (props.profile && props.profile.employee_id) {
    cloudApi.get('/employees', {
      params: { id: props.profile.employee_id }
    }).then(res => {
      if (res.data.length > 0) {
        employees.value = res.data
      }
    }).catch(() => {})
  }
})
</script>
