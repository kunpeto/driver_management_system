import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/driver_management_system/',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    port: 5173,
    host: true
  },
  build: {
    // 禁用 sourcemap 避免 CI 環境問題
    sourcemap: false,
    // Code Splitting 配置
    rollupOptions: {
      output: {
        manualChunks: {
          // 將 Vue 生態系統分離
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          // 將 Element Plus 分離（最大的依賴）
          'element-plus': ['element-plus'],
          // 將 Axios 等工具庫分離
          'utils': ['axios', 'dayjs']
        }
      }
    },
    // Chunk 大小警告閾值
    chunkSizeWarningLimit: 500,
    // 啟用 CSS 代碼分割
    cssCodeSplit: true,
    // 生產環境移除 console 和 debugger
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
})
