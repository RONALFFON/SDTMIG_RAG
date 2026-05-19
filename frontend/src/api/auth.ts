import http, { rawHttp } from '@/utils/request'

export interface AuthUser {
  id: string
  phone: string
  nickname: string
  avatar?: string
}

export interface AuthPayload {
  access_token: string
  refresh_token: string
  user: AuthUser
}

/**
 * 发送短信验证码
 */
export async function sendCodeApi(phone: string): Promise<{ success: boolean }> {
  const { data } = await http.post('/api/auth/send-code', { phone })
  return data
}

/**
 * 手机号注册
 */
export async function registerApi(payload: {
  phone: string
  code: string
  password: string
}): Promise<AuthPayload> {
  const { data } = await http.post('/api/auth/register', payload)
  return data
}

/**
 * 账号登录
 */
export async function loginApi(payload: {
  phone: string
  password: string
}): Promise<AuthPayload> {
  const { data } = await http.post('/api/auth/login', payload)
  return data
}

/**
 * 刷新 access token（使用原始请求实例，避免拦截器递归）
 */
export async function refreshTokenApi(refreshToken: string): Promise<{
  access_token: string
  refresh_token: string
}> {
  const { data } = await rawHttp.post('/api/auth/refresh', { refresh_token: refreshToken })
  return data
}

/**
 * 退出登录
 */
export async function logoutApi(): Promise<{ success: boolean }> {
  const { data } = await http.post('/api/auth/logout')
  return data
}
