<template>
  <el-dialog :model-value="modelValue" title="轉換履歷類型" width="800px" @close="handleClose">
    <el-alert
      v-if="profile?.profile_type !== 'basic'"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 20px"
    >
      此履歷已轉換為「{{ PROFILE_TYPES[profile?.profile_type]?.label }}」，無法再次轉換。
    </el-alert>

    <template v-else>
      <el-steps :active="step" finish-status="success" style="margin-bottom: 30px">
        <el-step title="選擇類型" />
        <el-step title="填寫資料" />
        <el-step title="確認轉換" />
      </el-steps>

      <!-- 步驟 1：選擇類型 -->
      <div v-if="step === 0">
        <el-radio-group v-model="targetType" class="type-selection">
          <el-radio-button
            v-for="(config, key) in convertibleTypes"
            :key="key"
            :label="key"
          >
            {{ config.label }}
          </el-radio-button>
        </el-radio-group>
        <p v-if="targetType" class="type-hint">
          {{ typeDescriptions[targetType] }}
        </p>
      </div>

      <!-- 步驟 2：填寫資料 -->
      <div v-if="step === 1">
        <component
          :is="formComponent"
          v-if="formComponent"
          ref="subFormRef"
          :profile="profile"
          @data-change="handleFormDataChange"
        />
      </div>

      <!-- 步驟 3：確認 -->
      <div v-if="step === 2">
        <el-descriptions title="轉換確認" :column="1" border>
          <el-descriptions-item label="履歷 ID">{{ profile?.id }}</el-descriptions-item>
          <el-descriptions-item label="員工">{{ profile?.employee_name }}</el-descriptions-item>
          <el-descriptions-item label="事件日期">{{ profile?.event_date }}</el-descriptions-item>
          <el-descriptions-item label="目標類型">
            <el-tag :type="PROFILE_TYPES[targetType]?.color">
              {{ PROFILE_TYPES[targetType]?.label }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          style="margin-top: 20px"
        >
          轉換後將無法恢復為基本履歷，請確認資料無誤。
        </el-alert>
      </div>
    </template>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button v-if="step > 0" @click="prevStep">上一步</el-button>
      <el-button
        v-if="step < 2 && profile?.profile_type === 'basic'"
        type="primary"
        :disabled="step === 0 && !targetType"
        @click="nextStep"
      >
        下一步
      </el-button>
      <el-button
        v-if="step === 2"
        type="primary"
        :loading="converting"
        @click="handleConvert"
      >
        確認轉換
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * 履歷類型轉換對話框
 * 對應 tasks.md T152: 建立履歷類型轉換對話框
 */
import { ref, computed, watch, shallowRef, markRaw } from 'vue'
import { ElMessage } from 'element-plus'
import { useProfilesStore, PROFILE_TYPES } from '@/stores/profiles'
import EventInvestigationForm from './EventInvestigationForm.vue'
import PersonnelInterviewForm from './PersonnelInterviewForm.vue'
import CorrectiveMeasuresForm from './CorrectiveMeasuresForm.vue'
import AssessmentNoticeForm from './AssessmentNoticeForm.vue'

const props = defineProps({
  modelValue: Boolean,
  profile: Object
})

const emit = defineEmits(['update:modelValue', 'converted'])

const profilesStore = useProfilesStore()

const step = ref(0)
const targetType = ref('')
const formData = ref({})
const converting = ref(false)
const subFormRef = ref()

// 可轉換的類型（排除 basic）
const convertibleTypes = computed(() => {
  const types = { ...PROFILE_TYPES }
  delete types.basic
  return types
})

// 類型說明
const typeDescriptions = {
  event_investigation: '用於記錄事件調查詳情，包含原因分析、改善建議、責任判定等。',
  personnel_interview: '用於記錄人員訪談內容，系統會自動帶入員工班表資訊。',
  corrective_measures: '用於記錄矯正措施，包含事件概述、矯正行動、完成期限等。',
  assessment_notice: '用於產生考核加分或扣分通知單。'
}

// 表單元件對應
const formComponents = {
  event_investigation: markRaw(EventInvestigationForm),
  personnel_interview: markRaw(PersonnelInterviewForm),
  corrective_measures: markRaw(CorrectiveMeasuresForm),
  assessment_notice: markRaw(AssessmentNoticeForm)
}

const formComponent = computed(() => formComponents[targetType.value])

// 重置狀態
watch(() => props.modelValue, (val) => {
  if (val) {
    step.value = 0
    targetType.value = ''
    formData.value = {}
  }
})

function handleClose() {
  emit('update:modelValue', false)
}

function nextStep() {
  if (step.value === 1 && subFormRef.value?.validate) {
    subFormRef.value.validate().then(() => {
      step.value++
    }).catch(() => {})
  } else {
    step.value++
  }
}

function prevStep() {
  step.value--
}

function handleFormDataChange(data) {
  formData.value = data
}

async function handleConvert() {
  converting.value = true
  try {
    await profilesStore.convertProfile(props.profile.id, targetType.value, formData.value)
    ElMessage.success('履歷轉換成功')
    emit('converted')
    handleClose()
  } catch (err) {
    ElMessage.error(err.message || '轉換失敗')
  } finally {
    converting.value = false
  }
}
</script>

<style scoped>
.type-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.type-hint {
  margin-top: 20px;
  color: #909399;
  font-size: 14px;
}
</style>
