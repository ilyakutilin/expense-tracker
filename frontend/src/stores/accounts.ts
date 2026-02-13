import { accountsApi } from '@/api/accounts'
import type { AccountCreate, AccountResponseTree } from '@/types/account'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAccountsStore = defineStore('accounts', () => {
  const accounts = ref<AccountResponseTree[]>([])
  const loading = ref(false)

  async function fetchAccounts(params?: Record<string, unknown>) {
    loading.value = true
    try {
      const response = await accountsApi.list(params)
      accounts.value = response
    } finally {
      loading.value = false
    }
  }

  async function createAccount(data: AccountCreate) {
    const account = await accountsApi.create(data)
    // TODO: Instead of doing this, maybe just return Tree from API?
    const accountTree: AccountResponseTree = {
      ...account,
      children: [],
    }
    accounts.value.unshift(accountTree)
    return accountTree
  }

  async function deleteAccount(id: number) {
    await accountsApi.delete(id)
    accounts.value = accounts.value.filter(a => a.id !== id)
  }

  return {
    accounts: accounts,
    loading,
    fetchAccounts: fetchAccounts,
    createAccount: createAccount,
    deleteAccount,
  }
})
