<template>
  <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
    <el-form-item label="事件概述">
      <el-input
        v-model="formData.event_summary"
        type="textarea"
        :rows="4"
        placeholder="描述事件發生的時間、地點、經過、結果狀況"
      />
    </el-form-item>

    <el-form-item label="矯正行動" prop="corrective_actions">
      <el-input
        v-model="formData.corrective_actions"
        type="textarea"
        :rows="4"
        placeholder="詳細描述矯正措施"
      />
    </el-form-item>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="負責人">
          <el-input v-model="formData.responsible_person" placeholder="負責人姓名" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="完成期限">
          <el-date-picker
            v-model="formData.completion_deadline"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="選擇期限"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="完成狀態">
      <el-radio-group v-model="formData.completion_status">
        <el-radio-button label="pending">待處理</el-radio-button>
        <el-radio-button label="in_progress">進行中</el-radio-button>
        <el-radio-button label="completed">已完成</el-radio-button>
      </el-radio-group>
    </el-form-item>
  </el-form>
</template>

<script setup>
/**
 * 矯正措施表單
 * 對應 tasks.md T155: 建立矯正措施表單
 */
import { ref, watch } from 'vue'

const emit = defineEmits(['data-change'])

const formRef = ref()

const formData = ref({
  event_summary: '',
  corrective_actions: '',
  responsible_person: '',
  completion_deadline: null,
  completion_status: 'pending'
})

const rules = {
  corrective_actions: [{ required: true, message: '請填寫矯正行動', trigger: 'blur' }]
}

watch(formData, (val) => {
  emit('data-change', val)
}, { deep: true, immediate: true })

function validate() {
  return formRef.value?.validate()
}

defineExpose({ validate })
</script>
