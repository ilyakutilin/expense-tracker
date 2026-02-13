import type { AccountCreate, AccountResponseFlat, AccountResponseTree } from '@/types/account'
import apiClient from './client'

export const accountsApi = {
  async list(params?: Record<string, unknown>): Promise<AccountResponseTree[]> {
    const response = await apiClient.get<AccountResponseTree[]>('/accounts/', { params })
    return response.data
  },

  async get(id: number): Promise<AccountResponseFlat> {
    const response = await apiClient.get<AccountResponseFlat>(`/accounts/${id}`)
    return response.data
  },

  async create(data: AccountCreate): Promise<AccountResponseFlat> {
    const response = await apiClient.post<AccountResponseFlat>('/accounts/', data)
    return response.data
  },

  async update(id: number, data: Partial<AccountCreate>): Promise<AccountResponseFlat> {
    const response = await apiClient.patch<AccountResponseFlat>(`/accounts/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/accounts/${id}`)
  },
}
