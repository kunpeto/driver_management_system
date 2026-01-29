<template>
  <div class="barcode-generator-page">
    <!-- 頁面標題 -->
    <div class="page-header">
      <h1>條碼生成器</h1>
      <p class="subtitle">生成各種格式的條碼，可用於文件識別和 PDF 處理</p>
    </div>

    <!-- 本機 API 狀態 -->
    <el-alert
      v-if="!localApiConnected"
      title="本機 API 未連線"
      type="warning"
      description="條碼生成功能需要本機桌面應用程式支援。請確認應用程式已啟動。"
      show-icon
      :closable="false"
      class="connection-alert"
    />

    <el-row :gutter="20" v-if="localApiConnected">
      <!-- 左側：生成表單 -->
      <el-col :span="12">
        <el-card class="generator-card">
          <template #header>
            <span>條碼設定</span>
          </template>

          <el-form
            ref="formRef"
            :model="formData"
            :rules="rules"
            label-width="100px"
            label-position="top"
          >
            <!-- 快速生成：部門條碼 -->
            <el-divider content-position="left">快速生成</el-divider>

            <el-form-item label="部門">
              <el-radio-group v-model="quickDepartment" @change="generateQuickBarcode">
                <el-radio-button label="淡海">淡海 (TH)</el-radio-button>
                <el-radio-button label="安坑">安坑 (AK)</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-form-item label="識別碼">
              <el-input
                v-model="quickIdentifier"
                placeholder="輸入識別碼，如 12345"
                @input="generateQuickBarcode"
              >
                <template #prepend>
                  {{ quickDepartment === '淡海' ? 'TH-' : 'AK-' }}
                </template>
              </el-input>
            </el-form-item>

            <!-- 自訂生成 -->
            <el-divider content-position="left">自訂條碼</el-divider>

            <el-form-item label="條碼內容" prop="data">
              <el-input
                v-model="formData.data"
                placeholder="輸入條碼內容"
                clearable
              />
            </el-form-item>

            <el-form-item label="條碼格式" prop="format">
              <el-select v-model="formData.format" placeholder="選擇格式" style="width: 100%">
                <el-option
                  v-for="fmt in barcodeFormats"
                  :key="fmt.format"
                  :label="`${fmt.name} (${fmt.format})`"
                  :value="fmt.format"
                >
                  <div class="format-option">
                    <span class="format-name">{{ fmt.name }}</span>
                    <span class="format-desc">{{ fmt.description }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>

            <el-form-item label="圖片格式">
              <el-radio-group v-model="formData.image_format">
                <el-radio-button label="png">PNG</el-radio-button>
                <el-radio-button label="svg">SVG</el-radio-button>
              </el-radio-group>
            </el-form-item>

            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="高度 (px)">
                  <el-input-number
                    v-model="formData.height"
                    :min="20"
                    :max="500"
                    :step="10"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="字體大小">
                  <el-input-number
                    v-model="formData.font_size"
                    :min="6"
                    :max="24"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-checkbox v-model="formData.include_text">顯示文字</el-checkbox>
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="generateBarcode" :loading="generating">
                生成條碼
              </el-button>
              <el-button @click="resetForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右側：預覽和下載 -->
      <el-col :span="12">
        <el-card class="preview-card">
          <template #header>
            <div class="card-header">
              <span>條碼預覽</span>
              <el-button
                v-if="barcodeImage"
                size="small"
                type="primary"
                @click="downloadBarcode"
              >
                下載
              </el-button>
            </div>
          </template>

          <div class="preview-area">
            <div v-if="barcodeImage" class="barcode-preview">
              <img :src="barcodeImage" :alt="formData.data" />
              <p class="barcode-data">{{ lastGeneratedData }}</p>
            </div>
            <div v-else class="preview-placeholder">
              <el-icon :size="48"><picture /></el-icon>
              <p>條碼預覽將顯示在這裡</p>
            </div>
          </div>

          <!-- 錯誤訊息 -->
          <el-alert
            v-if="errorMessage"
            :title="errorMessage"
            type="error"
            show-icon
            closable
            @close="errorMessage = ''"
            class="error-alert"
          />
        </el-card>

        <!-- 格式說明 -->
        <el-card class="format-info-card">
          <template #header>
            <span>格式說明</span>
          </template>

          <div v-if="selectedFormatInfo" class="format-details">
            <h4>{{ selectedFormatInfo.name }}</h4>
            <p>{{ selectedFormatInfo.description }}</p>
            <p><strong>資料格式：</strong>{{ selectedFormatInfo.data_pattern }}</p>
            <p><strong>範例：</strong><code>{{ selectedFormatInfo.example }}</code></p>
          </div>
          <div v-else class="format-details">
            <p class="text-muted">選擇條碼格式以查看說明</p>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 批次生成 -->
    <el-card class="batch-card" v-if="localApiConnected">
      <template #header>
        <span>批次生成</span>
      </template>

      <el-form label-width="100px" inline>
        <el-form-item label="部門">
          <el-select v-model="batchDepartment" placeholder="選擇部門">
            <el-option label="淡海" value="淡海" />
            <el-option label="安坑" value="安坑" />
          </el-select>
        </el-form-item>
        <el-form-item label="起始編號">
          <el-input-number v-model="batchStart" :min="1" />
        </el-form-item>
        <el-form-item label="數量">
          <el-input-number v-model="batchCount" :min="1" :max="100" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="generateBatch" :loading="batchGenerating">
            批次生成
          </el-button>
        </el-form-item>
      </el-form>

      <!-- 批次結果 -->
      <div v-if="batchResults.length" class="batch-results">
        <el-divider />
        <div class="batch-grid">
          <div
            v-for="(item, index) in batchResults"
            :key="index"
            class="batch-item"
          >
            <img :src="item.image" :alt="item.data" />
            <span class="batch-item-data">{{ item.data }}</span>
          </div>
        </div>
        <div class="batch-actions">
          <el-button @click="downloadBatchAsZip">下載全部 (ZIP)</el-button>
          <el-button @click="batchResults = []">清除</el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Picture } from '@element-plus/icons-vue'

// 本機 API 基礎 URL（從環境變數讀取）
const LOCAL_API_BASE = import.meta.env.VITE_LOCAL_API_URL || 'http://localhost:8001'

// 表單資料
const formRef = ref(null)
const formData = ref({
  data: '',
  format: 'code128',
  image_format: 'png',
  height: 100,
  font_size: 10,
  include_text: true
})

// 驗證規則
const rules = {
  data: [
    { required: true, message: '請輸入條碼內容', trigger: 'blur' }
  ],
  format: [
    { required: true, message: '請選擇條碼格式', trigger: 'change' }
  ]
}

// 狀態
const localApiConnected = ref(false)
const generating = ref(false)
const barcodeImage = ref('')
const lastGeneratedData = ref('')
const errorMessage = ref('')
const barcodeFormats = ref([])

// 快速生成
const quickDepartment = ref('淡海')
const quickIdentifier = ref('')

// 批次生成
const batchDepartment = ref('淡海')
const batchStart = ref(1)
const batchCount = ref(10)
const batchGenerating = ref(false)
const batchResults = ref([])

// 計算屬性
const selectedFormatInfo = computed(() => {
  return barcodeFormats.value.find(f => f.format === formData.value.format)
})

// 檢查本機 API 連線
const checkLocalApi = async () => {
  try {
    const response = await fetch(`${LOCAL_API_BASE}/health`, {
      method: 'GET',
      mode: 'cors'
    })
    localApiConnected.value = response.ok

    if (response.ok) {
      // 載入支援的格式
      await loadBarcodeFormats()
    }
  } catch (error) {
    localApiConnected.value = false
    console.warn('本機 API 未連線:', error)
  }
}

// 載入條碼格式列表
const loadBarcodeFormats = async () => {
  try {
    const response = await fetch(`${LOCAL_API_BASE}/api/barcode/formats`)
    if (response.ok) {
      barcodeFormats.value = await response.json()
    }
  } catch (error) {
    console.error('載入格式列表失敗:', error)
  }
}

// 快速生成部門條碼
const generateQuickBarcode = () => {
  if (!quickIdentifier.value) return

  const prefix = quickDepartment.value === '淡海' ? 'TH' : 'AK'
  formData.value.data = `${prefix}-${quickIdentifier.value}`
  generateBarcode()
}

// 生成條碼
const generateBarcode = async () => {
  if (!formData.value.data) {
    ElMessage.warning('請輸入條碼內容')
    return
  }

  generating.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(`${LOCAL_API_BASE}/api/barcode/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData.value)
    })

    const data = await response.json()

    if (data.success) {
      barcodeImage.value = data.data_uri
      lastGeneratedData.value = data.data
      ElMessage.success('條碼生成成功')
    } else {
      errorMessage.value = data.error_message || '生成失敗'
      ElMessage.error(errorMessage.value)
    }
  } catch (error) {
    errorMessage.value = error.message
    ElMessage.error('生成失敗: ' + error.message)
  } finally {
    generating.value = false
  }
}

// 下載條碼
const downloadBarcode = () => {
  if (!barcodeImage.value) return

  const link = document.createElement('a')
  link.href = barcodeImage.value
  link.download = `barcode_${lastGeneratedData.value}.${formData.value.image_format}`
  link.click()
}

// 重置表單
const resetForm = () => {
  formData.value = {
    data: '',
    format: 'code128',
    image_format: 'png',
    height: 100,
    font_size: 10,
    include_text: true
  }
  barcodeImage.value = ''
  lastGeneratedData.value = ''
  errorMessage.value = ''
  quickIdentifier.value = ''
}

// 批次生成
const generateBatch = async () => {
  batchGenerating.value = true
  batchResults.value = []

  const prefix = batchDepartment.value === '淡海' ? 'TH' : 'AK'

  try {
    for (let i = 0; i < batchCount.value; i++) {
      const identifier = batchStart.value + i
      const barcodeData = `${prefix}-${identifier.toString().padStart(5, '0')}`

      const response = await fetch(`${LOCAL_API_BASE}/api/barcode/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          data: barcodeData,
          format: 'code128',
          image_format: 'png',
          include_text: true
        })
      })

      const data = await response.json()
      if (data.success) {
        batchResults.value.push({
          data: barcodeData,
          image: data.data_uri
        })
      }
    }

    ElMessage.success(`已生成 ${batchResults.value.length} 個條碼`)
  } catch (error) {
    ElMessage.error('批次生成失敗: ' + error.message)
  } finally {
    batchGenerating.value = false
  }
}

// 下載批次結果為 ZIP
const downloadBatchAsZip = () => {
  // 簡化版：逐一下載
  // 完整版應使用 JSZip 打包
  ElMessage.info('正在下載條碼...')

  batchResults.value.forEach((item, index) => {
    setTimeout(() => {
      const link = document.createElement('a')
      link.href = item.image
      link.download = `${item.data}.png`
      link.click()
    }, index * 200)
  })
}

// 頁面載入
onMounted(() => {
  checkLocalApi()
  setInterval(checkLocalApi, 30000)
})
</script>

<style scoped>
.barcode-generator-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
}

.subtitle {
  margin: 0;
  color: #909399;
}

.connection-alert {
  margin-bottom: 20px;
}

.generator-card,
.preview-card,
.format-info-card,
.batch-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.format-option {
  display: flex;
  flex-direction: column;
}

.format-name {
  font-weight: 500;
}

.format-desc {
  font-size: 12px;
  color: #909399;
}

.preview-area {
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  padding: 20px;
}

.barcode-preview {
  text-align: center;
}

.barcode-preview img {
  max-width: 100%;
  height: auto;
}

.barcode-data {
  margin-top: 12px;
  font-family: monospace;
  font-size: 14px;
  color: #606266;
}

.preview-placeholder {
  text-align: center;
  color: #909399;
}

.preview-placeholder p {
  margin-top: 8px;
}

.error-alert {
  margin-top: 16px;
}

.format-details h4 {
  margin: 0 0 8px 0;
}

.format-details p {
  margin: 4px 0;
  font-size: 14px;
}

.format-details code {
  background: #f5f7fa;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.text-muted {
  color: #909399;
}

.batch-results {
  margin-top: 16px;
}

.batch-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.batch-item {
  text-align: center;
  padding: 8px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.batch-item img {
  max-width: 100%;
  height: auto;
}

.batch-item-data {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  font-family: monospace;
  color: #606266;
}

.batch-actions {
  display: flex;
  gap: 12px;
}
</style>
