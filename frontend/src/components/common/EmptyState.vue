<template>
  <div class="empty-state">
    <el-empty :description="description" :image-size="imageSize">
      <template v-if="$slots.default" #default>
        <slot />
      </template>
    </el-empty>
  </div>
</template>

<script setup>
/**
 * 空狀態元件
 */

defineProps({
  description: {
    type: String,
    default: '暫無資料'
  },
  imageSize: {
    type: Number,
    default: 120
  }
})
</script>

<style scoped>
.empty-state {
  padding: 40px;
}
</style>
