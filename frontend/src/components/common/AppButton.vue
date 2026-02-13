<script setup lang="ts">
defineProps<{
  buttonText: string
}>()
</script>

<template>
  <button class="w-full bg-primary text-white py-2 rounded-lg hover:bg-blue-600 transition">
    {{ buttonText }}
  </button>
</template>
