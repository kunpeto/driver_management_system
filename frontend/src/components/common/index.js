/**
 * 共用元件索引
 * 對應 tasks.md T031: 建立 UI 元件庫封裝
 *
 * 匯出所有共用元件，方便統一引用
 */

// 基礎元件
export { default as AppButton } from './AppButton.vue'
export { default as AppInput } from './AppInput.vue'
export { default as AppModal } from './AppModal.vue'
export { default as AppCard } from './AppCard.vue'
export { default as AppTable } from './AppTable.vue'
export { default as AppPagination } from './AppPagination.vue'

// 狀態元件
export { default as LoadingSpinner } from './LoadingSpinner.vue'
export { default as EmptyState } from './EmptyState.vue'
export { default as ConnectionStatus } from './ConnectionStatus.vue'

// 佈局元件
export { default as PageHeader } from './PageHeader.vue'
export { default as SideMenu } from './SideMenu.vue'
