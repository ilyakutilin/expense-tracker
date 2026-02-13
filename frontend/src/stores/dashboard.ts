import { defineStore } from 'pinia'
import { onMounted, ref } from 'vue'

export const useDashboardStore = defineStore('dashboard', () => {
  // Default to today (YYYY-MM-DD)
  const today = new Date().toISOString().split('T')[0]

  const selectedDate = ref(today)
  const activeTab = ref<'expenses' | 'income' | 'transfer' | 'exchange'>('expenses')

  // Auto-update date to today on mount
  onMounted(() => {
    selectedDate.value = today
  })

  const setToday = () => {
    selectedDate.value = today
  }

  return {
    selectedDate,
    activeTab,
    setToday,
  }
})
