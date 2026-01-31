<template>
  <el-form ref="formRef" :model="formData" :rules="rules" label-width="120px">
    <el-divider content-position="left">班表資訊</el-divider>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-button type="primary" size="small" :loading="loadingShifts" @click="lookupShifts">
          自動帶入班表
        </el-button>
        <span v-if="shiftSource" style="margin-left: 10px; color: #909399; font-size: 12px">
          (資料來源: {{ shiftSource }})
        </span>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 15px">
      <el-col :span="8">
        <el-form-item label="前2天班別">
          <el-input v-model="formData.shift_before_2days" placeholder="例：0905G" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="前1天班別">
          <el-input v-model="formData.shift_before_1day" placeholder="例：R" />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="事件當天">
          <el-input v-model="formData.shift_event_day" placeholder="例：0730G" />
        </el-form-item>
      </el-col>
    </el-row>

    <el-divider content-position="left">訪談資訊</el-divider>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-form-item label="訪談人員">
          <el-input v-model="formData.interviewer" placeholder="訪談人員姓名" />
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="訪談日期">
          <el-date-picker
            v-model="formData.interview_date"
            type="date"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <el-form-item label="訪談內容">
      <el-input
        v-model="formData.interview_content"
        type="textarea"
        :rows="4"
        placeholder="詳細記錄訪談內容"
      />
    </el-form-item>

    <el-divider content-position="left">訪談結果</el-divider>

    <el-form-item label="勾選項目">
      <el-checkbox-group v-model="interviewResults">
        <el-checkbox label="ir_1">駕駛執照規定班別符合</el-checkbox>
        <el-checkbox label="ir_2">人員工作規定</el-checkbox>
        <el-checkbox label="ir_3">操作程序正確</el-checkbox>
        <el-checkbox label="ir_4">人員注意或作</el-checkbox>
        <el-checkbox label="ir_5">設備檢測正常</el-checkbox>
        <el-checkbox label="ir_6">人員規範熟練</el-checkbox>
        <el-checkbox label="ir_7">其他</el-checkbox>
      </el-checkbox-group>
    </el-form-item>

    <el-form-item label="其他說明" v-if="interviewResults.includes('ir_7')">
      <el-input v-model="formData.interview_result_data.ir_other_text" />
    </el-form-item>

    <el-divider content-position="left">後續行動</el-divider>

    <el-form-item label="勾選項目">
      <el-checkbox-group v-model="followUpActions">
        <el-checkbox label="fa_1">加強駕駛班前訓練</el-checkbox>
        <el-checkbox label="fa_2">列入駕駛缺點管</el-checkbox>
        <el-checkbox label="fa_3">培訓複訓</el-checkbox>
        <el-checkbox label="fa_4">追蹤作業執行</el-checkbox>
        <el-checkbox label="fa_5">設備維修</el-checkbox>
        <el-checkbox label="fa_6">人員改善教訓</el-checkbox>
        <el-checkbox label="fa_7">其他</el-checkbox>
      </el-checkbox-group>
    </el-form-item>

    <el-form-item label="其他說明" v-if="followUpActions.includes('fa_7')">
      <el-input v-model="formData.follow_up_action_data.fa_other_text" />
    </el-form-item>

    <el-divider content-position="left">結論</el-divider>

    <el-form-item label="結論">
      <el-input
        v-model="formData.conclusion"
        type="textarea"
        :rows="3"
        placeholder="訪談結論"
      />
    </el-form-item>
  </el-form>
</template>

<script setup>
/**
 * 人員訪談表單
 * 對應 tasks.md T154: 建立人員訪談表單
 */
import { ref, watch, computed } from 'vue'
import { useProfilesStore } from '@/stores/profiles'

const props = defineProps({
  profile: Object
})

const emit = defineEmits(['data-change'])

const profilesStore = useProfilesStore()
const formRef = ref()
const loadingShifts = ref(false)
const shiftSource = ref('')

const formData = ref({
  hire_date: null,
  shift_before_2days: '',
  shift_before_1day: '',
  shift_event_day: '',
  interview_content: '',
  interviewer: '',
  interview_date: null,
  interview_result_data: {
    ir_1: false, ir_2: false, ir_3: false, ir_4: false,
    ir_5: false, ir_6: false, ir_7: false, ir_other_text: ''
  },
  follow_up_action_data: {
    fa_1: false, fa_2: false, fa_3: false, fa_4: false,
    fa_5: false, fa_6: false, fa_7: false, fa_other_text: ''
  },
  conclusion: ''
})

const rules = {}

// 訪談結果勾選（用於 checkbox-group）
const interviewResults = computed({
  get() {
    const results = []
    for (let i = 1; i <= 7; i++) {
      if (formData.value.interview_result_data[`ir_${i}`]) {
        results.push(`ir_${i}`)
      }
    }
    return results
  },
  set(val) {
    for (let i = 1; i <= 7; i++) {
      formData.value.interview_result_data[`ir_${i}`] = val.includes(`ir_${i}`)
    }
  }
})

// 後續行動勾選
const followUpActions = computed({
  get() {
    const actions = []
    for (let i = 1; i <= 7; i++) {
      if (formData.value.follow_up_action_data[`fa_${i}`]) {
        actions.push(`fa_${i}`)
      }
    }
    return actions
  },
  set(val) {
    for (let i = 1; i <= 7; i++) {
      formData.value.follow_up_action_data[`fa_${i}`] = val.includes(`fa_${i}`)
    }
  }
})

// 自動帶入班表
async function lookupShifts() {
  if (!props.profile?.employee_id || !props.profile?.event_date) return

  loadingShifts.value = true
  try {
    const result = await profilesStore.lookupSchedule(
      props.profile.employee_id,
      props.profile.event_date
    )
    if (result) {
      formData.value.shift_before_2days = result.shift_before_2days || ''
      formData.value.shift_before_1day = result.shift_before_1day || ''
      formData.value.shift_event_day = result.shift_event_day || ''
      shiftSource.value = result.source
    }
  } catch (err) {
    console.error('班表查詢失敗:', err)
  } finally {
    loadingShifts.value = false
  }
}

// 監聽資料變化
watch(formData, (val) => {
  emit('data-change', val)
}, { deep: true, immediate: true })

function validate() {
  return formRef.value?.validate()
}

defineExpose({ validate })
</script>

<style scoped>
.el-checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
</style>
