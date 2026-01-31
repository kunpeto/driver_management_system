/**
 * API 服務層（重新導出）
 *
 * 此檔案為向後相容層，實際實作在 @/utils/api.js
 * 新程式碼應直接從 @/utils/api.js 導入
 *
 * @deprecated 建議直接使用 import { cloudApi, localApi } from '@/utils/api'
 */

// 從 utils/api.js 重新導出所有內容
export {
  cloudApi,
  localApi,
  checkLocalApiHealth,
  checkCloudApiHealth
} from '@/utils/api'

// 預設導出 cloudApi
export { default } from '@/utils/api'
