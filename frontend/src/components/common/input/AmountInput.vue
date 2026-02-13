<script setup lang="ts">
interface Props {
  label?: string
}

const { label = 'Сумма' } = defineProps<Props>()
</script>
<template>
  <div class="mb-4">
    <label class="block text-sm font-medium text-gray-700 mb-1">{{ label }}</label>
    <div class="flex">
      <input
        type="number"
        step="0.01"
        class="flex-1 border border-gray-300 rounded-l-lg p-2 focus:ring-primary focus:border-primary"
      />
      <button type="button" class="bg-gray-200 text-gray-700 px-3 rounded-r-lg hover:bg-gray-300">
        =
      </button>
    </div>
  </div>
</template>
