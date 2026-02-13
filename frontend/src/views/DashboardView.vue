<script setup lang="ts">
import ExchangeForm from '@/components/exchanges/ExchangeForm.vue'
import ExpenseForm from '@/components/expenses/ExpenseForm.vue'
import IncomeForm from '@/components/income/IncomeForm.vue'
import TransferForm from '@/components/transfers/TransferForm.vue'
import { useAuthStore } from '@/stores/auth'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const activeTab = ref('expenses')

const tabs = [
  { key: 'expenses', label: 'Расходы', component: ExpenseForm },
  { key: 'income', label: 'Доходы', component: IncomeForm },
  { key: 'transfer', label: 'Перемещения', component: TransferForm },
  { key: 'exchange', label: 'Обмен валют', component: ExchangeForm },
]

const currentFormComponent = computed(() => {
  const tab = tabs.find(t => t.key === activeTab.value)
  return tab?.component
})

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
    <!-- Left Column -->
    <div class="space-y-6">
      <!-- Add Operation Block -->
      <div class="bg-white rounded-xl shadow-md p-6">
        <!-- Tabs -->
        <div class="flex border-b mb-4">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="{
              'text-primary font-medium border-b-2 border-primary': activeTab === tab.key,
              'text-gray-500 hover:text-gray-700': activeTab !== tab.key,
            }"
            @click="activeTab = tab.key"
            class="py-2 px-4"
          >
            {{ tab.label }}
          </button>
        </div>

        <component :is="currentFormComponent" v-if="currentFormComponent" />
      </div>

      <!-- Operations List -->
      <div class="bg-white rounded-xl shadow-md p-6">
        <h2 class="text-lg font-semibold mb-4">Операции за день</h2>
        <div class="space-y-3">
          <!-- Operation Item -->
          <div
            class="operation-item bg-gray-50 p-3 rounded-lg border border-gray-200 cursor-pointer"
          >
            <div class="flex justify-between items-center">
              <span class="font-medium text-gray-700">Продукты</span>
              <span class="text-sm text-gray-500">Альфа</span>
            </div>
            <div class="text-sm text-gray-600 mt-1">Продукты в Пятёрочке</div>
            <div class="mt-2 flex flex-wrap gap-1">
              <span class="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                >продукты</span
              >
              <span class="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded"
                >каждодневное</span
              >
            </div>
          </div>

          <!-- Operation Item -->
          <div
            class="operation-item bg-gray-50 p-3 rounded-lg border border-gray-200 cursor-pointer"
          >
            <div class="flex justify-between items-center">
              <span class="font-medium text-gray-700">Salary</span>
              <span class="text-sm text-gray-500">Savings</span>
            </div>
            <div class="text-sm text-gray-600 mt-1">Monthly salary deposit</div>
            <div class="mt-2 flex flex-wrap gap-1">
              <span class="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded"
                >income</span
              >
            </div>
          </div>

          <!-- Operation Item -->
          <div
            class="operation-item bg-gray-50 p-3 rounded-lg border border-gray-200 cursor-pointer"
          >
            <div class="flex justify-between items-center">
              <span class="font-medium text-gray-700">Electricity</span>
              <span class="text-sm text-gray-500">Credit Card</span>
            </div>
            <div class="text-sm text-gray-600 mt-1">Monthly electricity bill</div>
            <div class="mt-2 flex flex-wrap gap-1">
              <span class="inline-block bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded"
                >utilities</span
              >
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Column -->
    <div>
      <!-- Accounts and Balances -->
      <div class="bg-white rounded-xl shadow-md p-6 h-full">
        <h2 class="text-lg font-semibold mb-4">Accounts</h2>
        <div class="space-y-2">
          <!-- Account Group -->
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div class="flex justify-between items-center p-3 bg-gray-50 font-medium">
              <span>Bank Accounts</span>
              <button class="text-gray-500 hover:text-gray-700">
                <i class="fas fa-chevron-down"></i>
              </button>
            </div>

            <!-- Nested Accounts -->
            <div class="account-nested">
              <div class="flex justify-between items-center p-3 border-b border-gray-100">
                <span>Checking Account</span>
                <span class="font-medium">$2,450.75</span>
              </div>
              <div class="flex justify-between items-center p-3 border-b border-gray-100">
                <span>Savings Account</span>
                <span class="font-medium">$12,840.50</span>
              </div>
            </div>
          </div>

          <!-- Account Group -->
          <div class="border border-gray-200 rounded-lg overflow-hidden">
            <div class="flex justify-between items-center p-3 bg-gray-50 font-medium">
              <span>Investments</span>
              <button class="text-gray-500 hover:text-gray-700">
                <i class="fas fa-chevron-up"></i>
              </button>
            </div>

            <!-- Nested Accounts -->
            <div class="account-nested">
              <div class="flex justify-between items-center p-3 border-b border-gray-100">
                <span>Stock Portfolio</span>
                <span class="font-medium">$8,250.00</span>
              </div>
              <div class="flex justify-between items-center p-3 border-b border-gray-100">
                <span>Retirement Fund</span>
                <span class="font-medium">$45,120.30</span>
              </div>
            </div>
          </div>

          <!-- Single Account -->
          <div class="flex justify-between items-center p-3 border border-gray-200 rounded-lg">
            <span>Credit Card</span>
            <span class="font-medium text-red-500">-$1,250.00</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
