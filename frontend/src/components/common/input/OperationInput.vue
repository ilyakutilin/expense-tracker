<script setup lang="ts">
import ExchangeForm from '@/components/exchanges/ExchangeForm.vue'
import ExpenseForm from '@/components/expenses/ExpenseForm.vue'
import IncomeForm from '@/components/income/IncomeForm.vue'
import TransferForm from '@/components/transfers/TransferForm.vue'
import { computed, ref } from 'vue'

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
</script>

<template>
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
</template>
