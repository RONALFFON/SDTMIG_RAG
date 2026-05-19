import http from '@/utils/request'

export interface UserProfile {
  id: string
  phone: string
  nickname: string
  avatar?: string
}

/**
 * 获取用户资料
 */
export async function getProfileApi(): Promise<UserProfile> {
  const { data } = await http.get('/api/user/profile')
  return data
}

/**
 * 更新用户资料
 */
export async function updateProfileApi(payload: {
  nickname: string
}): Promise<UserProfile> {
  const { data } = await http.put('/api/user/profile', payload)
  return data
}

/**
 * 修改密码
 */
export async function updatePasswordApi(payload: {
  oldPassword: string
  newPassword: string
}): Promise<{ success: boolean }> {
  const { data } = await http.put('/api/user/password', payload)
  return data
}
