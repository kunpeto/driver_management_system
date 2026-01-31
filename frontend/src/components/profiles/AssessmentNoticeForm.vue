<template>
  <el-form ref="formRef" :model="formData" :rules="rules" label-width="100px">
    <el-form-item label="考核類型" prop="assessment_type">
      <el-radio-group v-model="formData.assessment_type">
        <el-radio-button label="加分">
          <el-icon><Plus /></el-icon> 加分
        </el-radio-button>
        <el-radio-button label="扣分">
          <el-icon><Minus /></el-icon> 扣分
        </el-radio-button>
      </el-radio-group>
    </el-form-item>

    <el-form-item label="考核項目">
      <el-input v-model="formData.assessment_item" placeholder="例：D01 遲到、+M01 全勤" />
    </el-form-item>

    <el-form-item label="考核分數">
      <el-input-number
        v-model="formData.assessment_score"
        :min="formData.assessment_type === '扣分' ? -100 : 1"
        :max="formData.assessment_type === '扣分' ? -1 : 100"
      />
      <span style="margin-left: 10px; color: #909399">
        {{ formData.assessment_type === '加分' ? '(正數)' : '(負數)' }}
      </span>
    </el-form-item>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="核發日期">
          <el-date-picker
            v-model="formData.issue_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="選擇日期"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="核准人">
          <el-input v-model="formData.approver" placeholder="核准人姓名" />
        </el-form-item>
      </el-col>
    </el-row>
  </el-form>
</template>

<script setup>
/**
 * 考核通知表單
 * 對應 tasks.md T156: 建立考核通知表單
 */
import { ref, watch } from 'vue'
import { Plus, Minus } from '@element-plus/icons-vue'

const emit = defineEmits(['data-change'])

const formRef = ref()

const formData = ref({
  assessment_type: '扣分',
  assessment_item: '',
  assessment_score: -1,
  issue_date: null,
  approver: ''
})

const rules = {
  assessment_type: [{ required: true, message: '請選擇考核類型', trigger: 'change' }]
}

// 切換類型時重置分數
watch(() => formData.value.assessment_type, (type) => {
  if (type === '加分') {
    formData.value.assessment_score = Math.abs(formData.value.assessment_score) || 1
  } else {
    formData.value.assessment_score = -Math.abs(formData.value.assessment_score) || -1
  }
})

watch(formData, (val) => {
  emit('data-change', val)
}, { deep: true, immediate: true })

function validate() {
  return formRef.value?.validate()
}

defineExpose({ validate })
</script>
