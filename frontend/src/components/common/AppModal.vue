<template>
  <el-dialog
    v-model="visible"
    :title="title"
    :width="width"
    :close-on-click-modal="closeOnClickModal"
    :close-on-press-escape="closeOnPressEscape"
    :show-close="showClose"
    :before-close="handleClose"
    :destroy-on-close="destroyOnClose"
    @open="$emit('open')"
    @opened="$emit('opened')"
    @close="$emit('close')"
    @closed="$emit('closed')"
  >
    <!-- 內容 -->
    <slot />

    <!-- 底部按鈕 -->
    <template #footer>
      <slot name="footer">
        <div class="dialog-footer">
          <el-button @click="handleCancel">
            {{ cancelText }}
          </el-button>
          <el-button
            type="primary"
            :loading="loading"
            :disabled="confirmDisabled"
            @click="handleConfirm"
          >
            {{ confirmText }}
          </el-button>
        </div>
      </slot>
    </template>
  </el-dialog>
</template>

<script setup>
/**
 * 對話框元件
 * 封裝 Element Plus Dialog，統一樣式和行為
 */

import { computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: ''
  },
  width: {
    type: String,
    default: '500px'
  },
  closeOnClickModal: {
    type: Boolean,
    default: false
  },
  closeOnPressEscape: {
    type: Boolean,
    default: true
  },
  showClose: {
    type: Boolean,
    default: true
  },
  destroyOnClose: {
    type: Boolean,
    default: false
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  confirmText: {
    type: String,
    default: '確認'
  },
  loading: {
    type: Boolean,
    default: false
  },
  confirmDisabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:modelValue',
  'confirm',
  'cancel',
  'open',
  'opened',
  'close',
  'closed'
])

// 雙向綁定
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 關閉前的回調
const handleClose = (done) => {
  if (!props.loading) {
    done()
  }
}

// 取消按鈕
const handleCancel = () => {
  if (!props.loading) {
    emit('cancel')
    visible.value = false
  }
}

// 確認按鈕
const handleConfirm = () => {
  emit('confirm')
}
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
