<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { toast } from 'vue-sonner'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')

async function handleLogin() {
  error.value = ''
  try {
    await authStore.login({ username: username.value, password: password.value })
    toast.success('Welcome back!')
    router.push({ name: 'dashboard' })
  } catch (e: unknown) {
    console.error('Login error:', e)
    error.value = 'Invalid credentials. Please try again.'
    toast.error('Login failed')
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="w-full max-w-md space-y-8 p-8 bg-white rounded-xl shadow-lg">
      <div class="text-center">
        <h1 class="text-3xl font-bold text-gray-900">Expense Tracker</h1>
        <p class="mt-2 text-gray-600">Sign in to your account</p>
      </div>

      <form class="space-y-6" @submit.prevent="handleLogin">
        <div v-if="error" class="p-3 text-sm text-red-700 bg-red-100 rounded-lg">
          {{ error }}
        </div>

        <div>
          <label for="username" class="block text-sm font-medium text-gray-700"> Username </label>
          <input
            id="username"
            v-model="username"
            type="text"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700"> Password </label>
          <input
            id="password"
            v-model="password"
            type="password"
            required
            class="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <button
          type="submit"
          :disabled="authStore.loading"
          class="w-full rounded-lg bg-blue-600 px-4 py-2 text-white font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {{ authStore.loading ? 'Signing in...' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>
