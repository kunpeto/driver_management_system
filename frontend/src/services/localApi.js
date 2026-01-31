import { localApi } from './api'

// Word 文件生成
// 注意：此功能目前尚未在 desktop_app 後端實作
// TODO: 需在 desktop_app 中實作 word_generator.py 和對應路由
export const wordApi = {
  generate(templateType, data) {
    return localApi.post('/api/word/generate', {
      template_type: templateType,
      data
    })
  }
}

// 條碼生成
export const barcodeApi = {
  generate(profileId, department, format = 'code128') {
    return localApi.post('/api/barcode/generate', {
      profile_id: profileId,
      department,
      format
    })
  }
}

// PDF 掃描與處理
export const pdfApi = {
  scan(file) {
    const formData = new FormData()
    formData.append('file', file)
    return localApi.post('/api/pdf/scan', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  split(file) {
    const formData = new FormData()
    formData.append('file', file)
    return localApi.post('/api/pdf/split', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  },

  process(file, department) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('department', department)
    return localApi.post('/api/pdf/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

// Google Drive 上傳
// 注意：此功能目前尚未在 desktop_app 後端實作
// TODO: 需在 desktop_app 中實作 drive_uploader.py 和對應路由
export const driveApi = {
  upload(file, folderId) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder_id', folderId)
    return localApi.post('/api/drive/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

// 健康檢查
export const localHealthApi = {
  check() {
    return localApi.get('/health')
  }
}
