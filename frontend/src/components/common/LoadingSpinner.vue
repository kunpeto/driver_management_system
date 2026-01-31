<template>
  <div class="loading-spinner" :class="{ 'loading-spinner--fullscreen': fullscreen }">
    <el-icon class="loading-spinner__icon" :size="size">
      <Loading />
    </el-icon>
    <span v-if="text" class="loading-spinner__text">{{ text }}</span>
  </div>
</template>

<script setup>
/**
 * 載入中元件
 */

import { Loading } from '@element-plus/icons-vue'

defineProps({
  text: {
    type: String,
    default: '載入中...'
  },
  size: {
    type: Number,
    default: 40
  },
  fullscreen: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.loading-spinner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.loading-spinner--fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  z-index: 9999;
}

.loading-spinner__icon {
  animation: spin 1s linear infinite;
  color: #409eff;
}

.loading-spinner__text {
  margin-top: 12px;
  color: #606266;
  font-size: 14px;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
