<script setup lang="ts">
defineProps<{
  label: string
  placeholder: string
}>()
</script>
<template>
  <div class="mb-4">
    <label class="block text-sm font-medium text-gray-700 mb-1">{{ label }}</label>
    <div class="relative">
      <input
        type="text"
        class="w-full border border-gray-300 rounded-lg p-2 focus:ring-primary focus:border-primary"
        :placeholder="placeholder"
      />
      <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
        <i class="fas fa-chevron-down text-gray-400"></i>
      </div>
    </div>
  </div>
</template>
