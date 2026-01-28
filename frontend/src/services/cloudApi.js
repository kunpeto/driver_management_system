import { cloudApi } from './api'

// 認證相關 API
export const authApi = {
  login(username, password) {
    return cloudApi.post('/auth/login', { username, password })
  },

  refreshToken() {
    return cloudApi.post('/auth/refresh')
  }
}

// 員工管理 API
export const employeeApi = {
  getAll(params = {}) {
    return cloudApi.get('/employees', { params })
  },

  getById(id) {
    return cloudApi.get(`/employees/${id}`)
  },

  create(data) {
    return cloudApi.post('/employees', data)
  },

  update(id, data) {
    return cloudApi.put(`/employees/${id}`, data)
  },

  delete(id) {
    return cloudApi.delete(`/employees/${id}`)
  }
}

// 系統設定 API
export const systemApi = {
  getSettings(params = {}) {
    return cloudApi.get('/system-settings', { params })
  },

  updateSetting(id, data) {
    return cloudApi.put(`/system-settings/${id}`, data)
  }
}

// 健康檢查
export const healthApi = {
  check() {
    return cloudApi.get('/health')
  }
}
