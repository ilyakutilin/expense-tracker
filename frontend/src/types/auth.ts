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
