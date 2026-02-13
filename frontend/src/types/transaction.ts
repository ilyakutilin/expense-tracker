import type { AccountResponseBaseWithCurrency } from './account'
import type { TagResponseBase } from './tag'

type TransactionType = 'income' | 'expense' | 'transfer' | 'exchange' | 'correction' | 'refund'

const orderByFields = ['id', 'type', 'date', 'is_template'] as const
type OrderByField = (typeof orderByFields)[number]
type WithPrefix<T extends string> = T | `-${T}`

export interface TransactionFilters {
  page?: number
  page_size?: number
  type?: TransactionType
  date_lt?: string
  date_lte?: string
  date_gt?: string
  date_gte?: string
  comment?: string
  is_template?: boolean
  account_id?: number
  account_id_in?: string
  amount_lt?: number
  amount_lte?: number
  amount_gt?: number
  amount_gte?: number
  tag_ids_in?: string
  tag_ids_all?: string
  order_by?: WithPrefix<OrderByField>
  search?: string
}

export interface TransactionLineBase {
  id: number
  transaction_id: number
  account_id: number
  amount: number
}
export interface TransactionLineCreate {
  transaction_id?: number
  account_id: number
  amount: number
}

export interface TransactionCreate {
  type: TransactionType
  date: string
  comment: string
  is_template: boolean
  lines: TransactionLineCreate[]
  tag_ids: number[]
}

export interface TransactionLineResponse {
  id: number
  account: AccountResponseBaseWithCurrency
  amount: string
  created_at: string
  updated_at: string
}

export interface TransactionResponse {
  id: number
  type: TransactionType
  lines: TransactionLineResponse[]
  date: string | null
  comment: string | null
  is_template: boolean
  tags: TagResponseBase[]
  created_at: string
  updated_at: string
}
