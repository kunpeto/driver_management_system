import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSystemStore = defineStore('system', () => {
  const settings = ref({})
  const loading = ref(false)
  const localApiAvailable = ref(false)

  function setSettings(data) {
    settings.value = data
  }

  function setLoading(status) {
    loading.value = status
  }

  function setLocalApiAvailable(status) {
    localApiAvailable.value = status
  }

  return {
    settings,
    loading,
    localApiAvailable,
    setSettings,
    setLoading,
    setLocalApiAvailable
  }
})
