<template>
  <div class="app-input">
    <label v-if="label" :for="inputId" class="app-input__label">
      {{ label }}
      <span v-if="required" class="app-input__required">*</span>
    </label>
    <el-input
      :id="inputId"
      v-model="inputValue"
      :type="type"
      :placeholder="placeholder"
      :disabled="disabled"
      :readonly="readonly"
      :clearable="clearable"
      :show-password="type === 'password'"
      :prefix-icon="prefixIcon"
      :suffix-icon="suffixIcon"
      :maxlength="maxlength"
      :show-word-limit="showWordLimit"
      @input="onInput"
      @change="onChange"
      @blur="onBlur"
      @focus="onFocus"
    />
    <div v-if="error" class="app-input__error">
      {{ error }}
    </div>
    <div v-if="hint && !error" class="app-input__hint">
      {{ hint }}
    </div>
  </div>
</template>

<script setup>
/**
 * 輸入框元件
 * 封裝 Element Plus Input，添加標籤和錯誤訊息支援
 */

import { computed, ref } from 'vue'

const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  readonly: {
    type: Boolean,
    default: false
  },
  required: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: true
  },
  prefixIcon: {
    type: [String, Object],
    default: null
  },
  suffixIcon: {
    type: [String, Object],
    default: null
  },
  maxlength: {
    type: Number,
    default: null
  },
  showWordLimit: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  hint: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'input', 'change', 'blur', 'focus'])

// 生成唯一 ID
const inputId = ref(`input-${Math.random().toString(36).substr(2, 9)}`)

// 雙向綁定
const inputValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// 事件處理
const onInput = (value) => emit('input', value)
const onChange = (value) => emit('change', value)
const onBlur = (event) => emit('blur', event)
const onFocus = (event) => emit('focus', event)
</script>

<style scoped>
.app-input {
  margin-bottom: 16px;
}

.app-input__label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.app-input__required {
  color: #f56c6c;
  margin-left: 4px;
}

.app-input__error {
  margin-top: 4px;
  font-size: 12px;
  color: #f56c6c;
}

.app-input__hint {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
</style>
