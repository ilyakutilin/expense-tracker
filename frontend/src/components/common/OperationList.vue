<script setup lang="ts">
// TODO: Implement operations stores
import { useExpensesStore } from '@/stores/expenses' // Adapt per your store structure
import { useIncomeStore } from '@/stores/income'
import { computed, watch } from 'vue'
// Import other stores as needed

const props = defineProps<{ type: string; date: string }>()

// Map tab types to store fetch methods
const storeMap = {
  expenses: useExpensesStore(),
  income: useIncomeStore(),
  // TODO: Add transfer/exchange stores
}

watch(
  () => [props.type, props.date],
  ([type, date]) => {
    const store = storeMap[type as keyof typeof storeMap]
    if (store?.fetchByDate) store.fetchByDate(date) // TODO: Implement this action in stores
  },
  { immediate: true }
)

// TODO: Get items from relevant store (implement filtered getter in stores)
const items = computed(() => {
  const store = storeMap[props.type as keyof typeof storeMap]
  return store?.itemsForDate?.(props.date) || []
})
</script>

<template>
  <div class="mt-6">
    <h3 class="text-lg font-medium mb-3 capitalize">{{ type }} for {{ date }}</h3>
    <div v-if="items.length === 0" class="text-gray-500">No operations</div>
    <div v-else class="space-y-2">
      <div v-for="item in items" :key="item.id" class="p-3 border rounded">
        <!-- Render operation details -->
        <div class="font-medium">{{ item.description }}</div>
        <div class="text-gray-600">{{ item.amount }} • {{ item.category }}</div>
      </div>
    </div>
  </div>
</template>
