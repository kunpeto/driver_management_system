import { localApi } from './api'

// Word 文件生成
export const wordApi = {
  generate(templateType, data) {
    return localApi.post('/api/generate-word', {
      template_type: templateType,
      data
    })
  }
}

// 條碼生成
export const barcodeApi = {
  generate(profileId, department, format = 'code128') {
    return localApi.post('/api/generate-barcode', {
      profile_id: profileId,
      department,
      format
    })
  }
}

// PDF 掃描
export const pdfApi = {
  scan(file) {
    const formData = new FormData()
    formData.append('file', file)
    return localApi.post('/api/scan-pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

// Google Drive 上傳
export const driveApi = {
  upload(file, folderId) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('folder_id', folderId)
    return localApi.post('/api/upload-to-drive', formData, {
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
