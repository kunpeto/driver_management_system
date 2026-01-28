<template>
  <div class="page-header">
    <div class="page-header__main">
      <el-breadcrumb v-if="breadcrumb.length" separator="/">
        <el-breadcrumb-item
          v-for="item in breadcrumb"
          :key="item.path"
          :to="item.path ? { path: item.path } : null"
        >
          {{ item.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>

      <h1 class="page-header__title">{{ title }}</h1>

      <p v-if="description" class="page-header__description">
        {{ description }}
      </p>
    </div>

    <div v-if="$slots.actions" class="page-header__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
/**
 * 頁面標題元件
 */

defineProps({
  title: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  breadcrumb: {
    type: Array,
    default: () => []
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.page-header__main {
  flex: 1;
}

.page-header__title {
  margin: 12px 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.page-header__description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.page-header__actions {
  display: flex;
  gap: 12px;
  margin-left: 24px;
}
</style>
