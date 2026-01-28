/**
 * Vue Router 配置
 * 對應 tasks.md T027: 設定 Vue Router
 *
 * 功能：
 * - 路由表定義
 * - 導航守衛（認證、權限檢查）
 * - 延遲載入（Code Splitting）
 */

import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// 路由表
const routes = [
  // ============================================================
  // 公開路由（不需登入）
  // ============================================================
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/Login.vue'),
    meta: {
      requiresAuth: false,
      title: '登入'
    }
  },

  // ============================================================
  // 需要認證的路由
  // ============================================================
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard.vue'),
    meta: {
      requiresAuth: true,
      title: '儀表板'
    }
  },

  // 員工管理
  {
    path: '/employees',
    name: 'employees',
    component: () => import('@/views/Employees.vue'),
    meta: {
      requiresAuth: true,
      title: '員工列表'
    }
  },
  {
    path: '/employees/:id',
    name: 'employee-detail',
    component: () => import('@/views/EmployeeDetail.vue'),
    meta: {
      requiresAuth: true,
      title: '員工詳情'
    }
  },

  // 班表管理
  {
    path: '/schedules',
    name: 'schedules',
    component: () => import('@/views/Schedules.vue'),
    meta: {
      requiresAuth: true,
      title: '班表查詢'
    }
  },

  // 駕駛時數
  {
    path: '/driving-stats',
    name: 'driving-stats',
    component: () => import('@/views/DrivingStats.vue'),
    meta: {
      requiresAuth: true,
      title: '駕駛時數'
    }
  },
  {
    path: '/driving-competition',
    name: 'driving-competition',
    component: () => import('@/views/DrivingCompetition.vue'),
    meta: {
      requiresAuth: true,
      title: '駕駛競賽排名'
    }
  },

  // PDF 處理
  {
    path: '/pdf-upload',
    name: 'pdf-upload',
    component: () => import('@/views/PdfUpload.vue'),
    meta: {
      requiresAuth: true,
      title: 'PDF 上傳'
    }
  },
  {
    path: '/barcode-generator',
    name: 'barcode-generator',
    component: () => import('@/views/BarcodeGenerator.vue'),
    meta: {
      requiresAuth: true,
      title: '條碼生成'
    }
  },

  // ============================================================
  // 管理員專用路由
  // ============================================================
  {
    path: '/system-settings',
    name: 'system-settings',
    component: () => import('@/views/SystemSettings.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: '系統設定'
    }
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('@/views/Users.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: '使用者管理'
    }
  },
  {
    path: '/google-services',
    name: 'google-services',
    component: () => import('@/views/GoogleServices.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: 'Google 服務'
    }
  },
  {
    path: '/route-standard-times',
    name: 'route-standard-times',
    component: () => import('@/views/RouteStandardTimes.vue'),
    meta: {
      requiresAuth: true,
      requiresAdmin: true,
      title: '勤務標準時間'
    }
  },

  // ============================================================
  // 錯誤頁面
  // ============================================================
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/errors/Forbidden.vue'),
    meta: {
      requiresAuth: false,
      title: '權限不足'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/views/errors/NotFound.vue'),
    meta: {
      requiresAuth: false,
      title: '頁面不存在'
    }
  }
]

// 建立路由器
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // 回到上一頁時恢復滾動位置
    if (savedPosition) {
      return savedPosition
    }
    // 否則滾動到頂部
    return { top: 0 }
  }
})

// ============================================================
// 導航守衛
// ============================================================

// 全域前置守衛
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 1. 設定頁面標題
  const baseTitle = '司機員管理系統'
  document.title = to.meta.title ? `${to.meta.title} | ${baseTitle}` : baseTitle

  // 2. 檢查認證狀態
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // 需要登入但未登入，重定向到登入頁
    return next({
      name: 'login',
      query: { redirect: to.fullPath }
    })
  }

  // 3. 檢查管理員權限
  if (to.meta.requiresAdmin && authStore.user?.role !== 'admin') {
    // 需要管理員權限但沒有，重定向到 403 頁面
    return next({ name: 'forbidden' })
  }

  // 4. 已登入使用者訪問登入頁，重定向到儀表板
  if (to.name === 'login' && authStore.isAuthenticated) {
    return next({ name: 'dashboard' })
  }

  next()
})

// 全域後置守衛
router.afterEach((to, from) => {
  // 可用於記錄頁面瀏覽、分析等
  console.debug(`[Router] ${from.path} -> ${to.path}`)
})

// 路由錯誤處理
router.onError((error) => {
  console.error('[Router Error]', error)

  // 處理 chunk 載入失敗（常見於部署後版本更新）
  if (error.message.includes('Failed to fetch dynamically imported module')) {
    window.location.reload()
  }
})

export default router
