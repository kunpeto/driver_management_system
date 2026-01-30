<template>
  <div class="document-download">
    <el-button
      :type="buttonType"
      :size="size"
      :loading="downloading"
      :disabled="disabled || !canGenerate"
      @click="handleDownload"
    >
      <el-icon v-if="!downloading"><Download /></el-icon>
      {{ downloading ? '生成中...' : buttonText }}
    </el-button>
    <span v-if="!canGenerate" class="hint">
      (僅已轉換的履歷可生成文件)
    </span>
  </div>
</template>

<script setup>
/**
 * 文件生成與下載元件
 * 對應 tasks.md T158: 實作文件生成與下載功能
 */
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Download } from '@element-plus/icons-vue'
import { useProfilesStore } from '@/stores/profiles'

const props = defineProps({
  profile: {
    type: Object,
    required: true
  },
  buttonText: {
    type: String,
    default: '生成文件'
  },
  buttonType: {
    type: String,
    default: 'success'
  },
  size: {
    type: String,
    default: 'default'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['success', 'error'])

const profilesStore = useProfilesStore()
const downloading = ref(false)

// 是否可以生成文件（僅已轉換的履歷可生成）
const canGenerate = computed(() => {
  return props.profile?.profile_type !== 'basic'
})

async function handleDownload() {
  if (!canGenerate.value) {
    ElMessage.warning('僅已轉換的履歷可生成文件')
    return
  }

  downloading.value = true

  try {
    await profilesStore.generateDocument(props.profile.id)
    ElMessage.success('文件生成成功，已開始下載')
    emit('success')
  } catch (err) {
    const message = err.message || '文件生成失敗'
    ElMessage.error(message)
    emit('error', err)
  } finally {
    downloading.value = false
  }
}
</script>

<style scoped>
.document-download {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.hint {
  font-size: 12px;
  color: #909399;
}
</style>
