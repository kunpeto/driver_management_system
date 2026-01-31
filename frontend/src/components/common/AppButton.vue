<template>
  <el-button
    :type="type"
    :size="size"
    :loading="loading"
    :disabled="disabled"
    :icon="icon"
    @click="$emit('click', $event)"
  >
    <slot />
  </el-button>
</template>

<script setup>
/**
 * 按鈕元件
 * 封裝 Element Plus Button，統一樣式和行為
 */

defineProps({
  type: {
    type: String,
    default: 'default',
    validator: (value) => ['primary', 'success', 'warning', 'danger', 'info', 'default'].includes(value)
  },
  size: {
    type: String,
    default: 'default',
    validator: (value) => ['large', 'default', 'small'].includes(value)
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  icon: {
    type: [String, Object],
    default: null
  }
})

defineEmits(['click'])
</script>
