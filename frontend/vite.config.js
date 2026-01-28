import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  base: '/driver_management_system/',
  server: {
    port: 5173,
    host: true
  }
})
