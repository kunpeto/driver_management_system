import { cloudApi } from './api'

// 認證相關 API
export const authApi = {
  login(username, password) {
    return cloudApi.post('/api/auth/login', { username, password })
  },

  refreshToken() {
    return cloudApi.post('/api/auth/refresh')
  }
}

// 員工管理 API
export const employeeApi = {
  getAll(params = {}) {
    return cloudApi.get('/api/employees', { params })
  },

  getById(id) {
    return cloudApi.get(`/api/employees/${id}`)
  },

  create(data) {
    return cloudApi.post('/api/employees', data)
  },

  update(id, data) {
    return cloudApi.put(`/api/employees/${id}`, data)
  },

  delete(id) {
    return cloudApi.delete(`/api/employees/${id}`)
  }
}

// 系統設定 API
export const systemApi = {
  getSettings(params = {}) {
    return cloudApi.get('/api/settings', { params })
  },

  updateSetting(id, data) {
    return cloudApi.put(`/api/settings/${id}`, data)
  }
}

// 健康檢查
export const healthApi = {
  check() {
    return cloudApi.get('/health')
  }
}
