export interface CurrencyResponse {
  id: number
  type: string
  symbol: string
}

export interface AccountCreate {
  name: string
  type: string
  parent_id?: number
  currency_id?: number
}

export interface AccountResponseBase {
  id: number
  name: string
  type: string
}

export interface AccountResponseBaseWithCurrency extends AccountResponseBase {
  currency: CurrencyResponse
}

export interface AccountResponseFlat extends AccountResponseBaseWithCurrency {
  parent: AccountResponseBase
  balance: string
  created_at: string
  updated_at: string
}

export interface AccountResponseTree extends AccountResponseFlat {
  children: AccountResponseTree[]
}
