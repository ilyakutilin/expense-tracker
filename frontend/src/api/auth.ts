import type { Token, UserLogin, UserResponse } from '@/types'
import apiClient from './client'

export const authApi = {
  async login(credentials: UserLogin): Promise<Token> {
    // FastAPI's OAuth2 expects form data, not JSON
    const formData = new URLSearchParams()
    formData.append('username', credentials.username)
    formData.append('password', credentials.password)

    const response = await apiClient.post<Token>('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  async me(): Promise<UserResponse> {
    const response = await apiClient.get<UserResponse>('/auth/me')
    return response.data
  },
}
