<script setup lang="ts">
import { useAccountsStore } from '@/stores/accounts'
import { useAuthStore } from '@/stores/auth'
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const accountsStore = useAccountsStore()
const authStore = useAuthStore()
const router = useRouter()

onMounted(() => {
  accountsStore.fetchAccounts()
})

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div class="flex h-16 justify-between items-center">
          <h1 class="text-xl font-bold text-gray-900">Expense Tracker</h1>
          <div class="flex items-center gap-4">
            <RouterLink
              :to="{ name: 'dashboard' }"
              class="text-gray-600 hover:text-gray-900 transition-colors"
            >
              Dashboard
            </RouterLink>
            <button
              class="rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-200 transition-colors"
              @click="handleLogout"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>

    <main class="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-900">Accounts</h2>
        <button
          class="rounded-lg bg-blue-600 px-4 py-2 text-white font-semibold hover:bg-blue-700 transition-colors"
        >
          + Add Account
        </button>
      </div>

      <!-- Loading state -->
      <div v-if="accountsStore.loading" class="text-center py-12">
        <div
          class="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent"
        />
        <p class="mt-2 text-gray-500">Loading accounts...</p>
      </div>

      <!-- Empty state -->
      <div
        v-else-if="accountsStore.accounts.length === 0"
        class="text-center py-12 bg-white rounded-xl shadow"
      >
        <p class="text-gray-500">No accounts yet. Add your first one!</p>
      </div>

      <!-- Accounts list -->
      <div v-else class="space-y-3">
        <div
          v-for="account in accountsStore.accounts"
          :key="account.id"
          class="flex items-center justify-between rounded-xl bg-white p-4 shadow hover:shadow-md transition-shadow"
        >
          <div>
            <p class="font-medium text-gray-900">{{ account.name }}</p>
            <p class="text-sm text-gray-500">{{ account.type }}</p>
          </div>
          <div class="text-right">
            <p class="text-lg font-bold text-gray-900">${{ account.balance }}</p>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
