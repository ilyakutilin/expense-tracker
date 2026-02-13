<script setup lang="ts">
import Sidebar from '@/components/layout/AppSidebar.vue'
import { useAuthStore } from '@/stores/auth'
import { onMounted } from 'vue'
import { Toaster } from 'vue-sonner'

const authStore = useAuthStore()

onMounted(() => {
  if (authStore.isAuthenticated) {
    authStore.fetchUser()
  }
})
</script>

<template>
  <Toaster position="top-right" :duration="3000" rich-colors />
  <Sidebar />
  <main class="ml-60 flex-1 transition-all duration-300">
    <RouterView />
  </main>
</template>
