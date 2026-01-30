<script setup>
/**
 * 應用程式主組件
 * 包含頂部導航、側邊欄和主內容區
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  House,
  User,
  Calendar,
  Document,
  Setting,
  Histogram,
  Trophy,
  Upload,
  UserFilled,
  List,
  Medal,
  Grid,
  Connection,
  ArrowDown
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 是否顯示側邊欄（登入頁不顯示）
const showLayout = computed(() => {
  return route.meta.requiresAuth !== false && authStore.isLoggedIn
})

// 選單項目
const menuItems = computed(() => {
  const items = [
    { index: '/dashboard', title: '儀表板', icon: House },
    { index: '/employees', title: '員工管理', icon: User },
    { index: '/schedules', title: '班表查詢', icon: Calendar },
    { index: '/profiles', title: '事件履歷', icon: Document },
    {
      index: 'assessment-group',
      title: '考核系統',
      icon: Histogram,
      children: [
        { index: '/assessment-records', title: '考核記錄', icon: List },
        { index: '/monthly-rewards', title: '月度獎勵', icon: Medal },
        { index: '/attendance-bonus', title: '差勤加分', icon: Calendar }
      ]
    },
    {
      index: 'driving-group',
      title: '駕駛統計',
      icon: Trophy,
      children: [
        { index: '/driving-stats', title: '駕駛時數', icon: Histogram },
        { index: '/driving-competition', title: '競賽排名', icon: Trophy }
      ]
    },
    {
      index: 'pdf-group',
      title: 'PDF 工具',
      icon: Upload,
      children: [
        { index: '/pdf-upload', title: 'PDF 上傳', icon: Upload },
        { index: '/barcode-generator', title: '條碼生成', icon: Grid }
      ]
    }
  ]

  // 管理員選單
  if (authStore.isAdmin) {
    items.push({
      index: 'admin-group',
      title: '系統管理',
      icon: Setting,
      children: [
        { index: '/users', title: '使用者管理', icon: UserFilled },
        { index: '/assessment-standards', title: '考核標準', icon: List },
        { index: '/route-standard-times', title: '勤務標準時間', icon: Calendar },
        { index: '/google-services', title: 'Google 服務', icon: Connection },
        { index: '/system-settings', title: '系統設定', icon: Setting }
      ]
    })
  }

  return items
})

// 處理登出
async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<template>
  <!-- 登入頁：無佈局 -->
  <router-view v-if="!showLayout" />

  <!-- 主應用佈局 -->
  <el-container v-else class="app-container">
    <!-- 側邊欄 -->
    <el-aside width="220px" class="app-aside">
      <div class="logo-container">
        <h2>司機員管理</h2>
      </div>

      <el-menu
        :default-active="route.path"
        router
        class="app-menu"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <template v-for="item in menuItems" :key="item.index">
          <!-- 有子選單 -->
          <el-sub-menu v-if="item.children" :index="item.index">
            <template #title>
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </template>
            <el-menu-item
              v-for="child in item.children"
              :key="child.index"
              :index="child.index"
            >
              <el-icon><component :is="child.icon" /></el-icon>
              <span>{{ child.title }}</span>
            </el-menu-item>
          </el-sub-menu>

          <!-- 無子選單 -->
          <el-menu-item v-else :index="item.index">
            <el-icon><component :is="item.icon" /></el-icon>
            <span>{{ item.title }}</span>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <!-- 主內容區 -->
    <el-container>
      <!-- 頂部欄 -->
      <el-header class="app-header">
        <div class="header-left">
          <span class="page-title">{{ route.meta.title || '司機員管理系統' }}</span>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleLogout">
            <span class="user-info">
              <el-avatar :size="32" :icon="UserFilled" />
              <span class="username">{{ authStore.user?.display_name || '使用者' }}</span>
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  {{ authStore.user?.username || '未知' }}
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  登出
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 主內容 -->
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style>
/* 全域樣式 */
html, body, #app {
  height: 100%;
  margin: 0;
  padding: 0;
}

.app-container {
  height: 100%;
}

/* 側邊欄 */
.app-aside {
  background-color: #304156;
  overflow-y: auto;
}

.logo-container {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #263445;
}

.logo-container h2 {
  color: #fff;
  font-size: 18px;
  margin: 0;
}

.app-menu {
  border-right: none;
}

/* 頂部欄 */
.app-header {
  background-color: #fff;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.username {
  font-size: 14px;
  color: #606266;
}

/* 主內容區 */
.app-main {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

/* 頁面過渡動畫 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
