export interface ApiError {
  detail: string
}

// Generic paginated response
export interface PaginatedResponse<T> {
  total: number
  page: number
  page_size: number
  total_pages: number
  items: T[]
}
