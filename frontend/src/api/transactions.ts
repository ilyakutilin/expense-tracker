import type { PaginatedResponse } from '@/types'
import type {
  TransactionCreate,
  TransactionFilters,
  TransactionResponse,
} from '@/types/transaction'
import apiClient from './client'

export const transactionApi = {
  async list(params?: TransactionFilters): Promise<PaginatedResponse<TransactionResponse>> {
    const response = await apiClient.get<PaginatedResponse<TransactionResponse>>('/transactions/', {
      params,
    })
    return response.data
  },

  async get(id: number): Promise<TransactionResponse> {
    const response = await apiClient.get<TransactionResponse>(`/transactions/${id}`)
    return response.data
  },

  async create(data: TransactionCreate): Promise<TransactionResponse> {
    const response = await apiClient.post<TransactionResponse>('/transactions/', data)
    return response.data
  },

  async update(id: number, data: Partial<TransactionCreate>): Promise<TransactionResponse> {
    const response = await apiClient.patch<TransactionResponse>(`/transactions/${id}`, data)
    return response.data
  },

  async delete(id: number): Promise<void> {
    await apiClient.delete(`/transactions/${id}`)
  },
}
