export interface UserResponse {
  id: number
  email: string
  role: string
  created_at: string
  updated_at: string
}

export interface UserLogin {
  username: string
  password: string
}

export interface UserRegister {
  email: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

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

export interface AccountResponseFlat extends AccountResponseBase {
  currency: CurrencyResponse
  parent: AccountResponseBase
  balance: string
  created_at: string
  updated_at: string
}

export interface AccountResponseTree extends AccountResponseFlat {
  children: AccountResponseTree[]
}

export interface ApiError {
  detail: string
}

// Generic paginated response (matches typical FastAPI pagination)
export interface PaginatedResponse<T> {
  total: number
  page: number
  page_size: number
  total_pages: number
  items: T[]
}
