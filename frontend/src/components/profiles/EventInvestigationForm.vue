<template>
  <el-form ref="formRef" :model="formData" :rules="rules" label-width="120px">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="事件時間">
          <el-time-picker
            v-model="formData.incident_time"
            format="HH:mm"
            value-format="HH:mm"
            placeholder="選擇時間"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="調查日期">
          <el-date-picker
            v-model="formData.investigation_date"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="選擇日期"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="詳細地點">
      <el-input v-model="formData.incident_location" placeholder="事件發生的詳細位置" />
    </el-form-item>

    <el-form-item label="目擊者">
      <el-input v-model="formData.witnesses" placeholder="目擊者姓名" />
    </el-form-item>

    <el-form-item label="調查人員">
      <el-input v-model="formData.investigator" placeholder="調查人員姓名" />
    </el-form-item>

    <el-divider content-position="left">事件分析</el-divider>

    <el-form-item label="原因分析">
      <el-input
        v-model="formData.cause_analysis"
        type="textarea"
        :rows="3"
        placeholder="分析事件發生的原因"
      />
    </el-form-item>

    <el-form-item label="過程描述">
      <el-input
        v-model="formData.process_description"
        type="textarea"
        :rows="4"
        placeholder="事件人員自述：異常發生原因與處理經過流程"
      />
    </el-form-item>

    <el-form-item label="改善建議">
      <el-input
        v-model="formData.improvement_suggestions"
        type="textarea"
        :rows="3"
        placeholder="調查人員的改善建議"
      />
    </el-form-item>

    <el-divider content-position="left">責任判定（Phase 9 統計）</el-divider>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-form-item label="是否歸責">
          <el-switch
            v-model="formData.has_responsibility"
            active-text="有責任"
            inactive-text="無責任"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="責任比例" v-if="formData.has_responsibility">
          <el-input-number
            v-model="formData.responsibility_ratio"
            :min="0"
            :max="100"
            :step="10"
          />
          <span style="margin-left: 5px">%</span>
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="事件類別">
          <el-select v-model="formData.category" placeholder="選擇類別">
            <el-option label="S - 安全類" value="S" />
            <el-option label="R - 服務類" value="R" />
            <el-option label="W - 工作類" value="W" />
            <el-option label="O - 營運類" value="O" />
            <el-option label="D - 紀律類" value="D" />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>
  </el-form>
</template>

<script setup>
/**
 * 事件調查表單
 * 對應 tasks.md T153: 建立事件調查表單
 */
import { ref, watch } from 'vue'

const props = defineProps({
  profile: Object
})

const emit = defineEmits(['data-change'])

const formRef = ref()

const formData = ref({
  incident_time: null,
  incident_location: '',
  witnesses: '',
  cause_analysis: '',
  process_description: '',
  improvement_suggestions: '',
  investigator: '',
  investigation_date: null,
  has_responsibility: false,
  responsibility_ratio: 0,
  category: null
})

const rules = {}

// 監聽資料變化並回傳
watch(formData, (val) => {
  emit('data-change', val)
}, { deep: true, immediate: true })

// 暴露驗證方法
function validate() {
  return formRef.value?.validate()
}

defineExpose({ validate })
</script>
