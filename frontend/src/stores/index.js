/**
 * Pinia Store 配置
 * 對應 tasks.md T028: 設定 Pinia Store
 *
 * 功能：
 * - 狀態管理初始化
 * - Store 集中匯出
 */

import { createPinia } from 'pinia'

// 建立 Pinia 實例
const pinia = createPinia()

// 匯出 stores
export { useAuthStore } from './auth'
// export { useEmployeesStore } from './employees'      // TODO: T057
// export { useSystemSettingsStore } from './systemSettings'  // TODO: T041
// export { useDrivingStatsStore } from './drivingStats'  // TODO: T117

export default pinia
