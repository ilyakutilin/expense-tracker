<script setup lang="ts">
import { useDashboardStore } from '@/stores/dashboard'
const dashboard = useDashboardStore()
</script>

<template>
  <div class="mb-4">
    <label class="block text-sm font-medium text-gray-700 mb-1">Дата</label>
    <div class="flex">
      <input
        v-model="dashboard.selectedDate"
        type="date"
        class="flex-1 border border-gray-300 rounded-l-lg p-2 focus:ring-primary focus:border-primary"
      />
      <button
        type="button"
        @click="dashboard.setToday"
        class="bg-gray-200 text-gray-700 px-3 rounded-r-lg hover:bg-gray-300"
      >
        Сегодня
      </button>
    </div>
  </div>
</template>
