import type { AccountResponseBaseWithCurrency } from './account'
import type { TagResponseBase } from './tag'

type TransactionType = 'income' | 'expense' | 'transfer' | 'exchange' | 'correction' | 'refund'

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
