<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <!-- Sidebar Navigation -->
  <aside
    id="sidebar"
    class="sidebar-open transition-sidebar bg-white shadow-lg h-screen flex flex-col z-10 fixed"
  >
    <div class="p-4 border-b">
      <h1 class="text-xl font-bold text-primary">Учёт расходов</h1>
    </div>

    <nav class="flex-1 py-4 overflow-y-auto">
      <ul class="space-y-1 px-2">
        <li>
          <a href="#" class="flex items-center p-3 rounded-lg bg-blue-50 text-primary font-medium">
            <i class="fas fa-home mr-3"></i> Главная
          </a>
        </li>
        <li>
          <a href="#" class="flex items-center p-3 rounded-lg text-gray-700 hover:bg-gray-100">
            <i class="fas fa-money-bill-wave mr-3"></i> Отчеты
          </a>
        </li>
        <li>
          <a href="#" class="flex items-center p-3 rounded-lg text-gray-700 hover:bg-gray-100">
            <i class="fas fa-plus-circle mr-3"></i> Операции
          </a>
        </li>
        <li>
          <a href="#" class="flex items-center p-3 rounded-lg text-gray-700 hover:bg-gray-100">
            <i class="fas fa-plus-circle mr-3"></i> Счета
          </a>
        </li>
        <li>
          <a href="#" class="flex items-center p-3 rounded-lg text-gray-700 hover:bg-gray-100">
            <i class="fas fa-exchange-alt mr-3"></i> Теги
          </a>
        </li>
        <li>
          <a href="#" class="flex items-center p-3 rounded-lg text-gray-700 hover:bg-gray-100">
            <i class="fas fa-coins mr-3"></i> Валюты
          </a>
        </li>
      </ul>
    </nav>

    <!-- User Login Block -->
    <div class="p-4 border-t bg-gray-50">
      <div class="flex items-center">
        <div class="mr-3">
          <div class="bg-gray-200 border-2 border-dashed rounded-xl w-10 h-10"></div>
        </div>
        <div class="flex-1">
          <p class="font-medium">Hard Coded Name</p>
          <p class="text-sm text-gray-500">{{ authStore.user?.email }}</p>
        </div>
        <button class="text-gray-500 hover:text-red-500" @click="handleLogout">
          <i class="fas fa-sign-out-alt"></i>
        </button>
      </div>
    </div>
  </aside>
</template>
