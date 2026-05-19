import type MockAdapter from 'axios-mock-adapter'

type MockUser = {
  id: string
  phone: string
  nickname: string
  avatar: string
}

const mockUsers = new Map<string, { password: string; user: MockUser }>([
  [
    '13800138000',
    {
      password: 'Test1234',
      user: {
        id: 'u-1001',
        phone: '13800138000',
        nickname: '沙箱用户',
        avatar: 'https://api.dicebear.com/9.x/thumbs/svg?seed=sandbox'
      }
    }
  ]
])

function createMockJwt(expiredInSeconds = 60 * 60): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(JSON.stringify({ exp: Math.floor(Date.now() / 1000) + expiredInSeconds }))
  return `${header}.${payload}.mock-signature`
}

/**
 * 注册认证相关 Mock
 */
export function setupAuthMock(mock: MockAdapter): void {
  mock.onPost('/api/auth/send-code').reply(200, { success: true })

  mock.onPost('/api/auth/register').reply((config) => {
    const body = JSON.parse(config.data || '{}')
    if (body.code !== '888888') {
      return [400, { message: '验证码错误' }]
    }
    const phone = String(body.phone || '')
    const user: MockUser = {
      id: `u-${Date.now()}`,
      phone,
      nickname: `用户${phone.slice(-4)}`,
      avatar: 'https://api.dicebear.com/9.x/thumbs/svg?seed=register'
    }
    mockUsers.set(phone, { password: String(body.password || ''), user })
    return [
      200,
      {
        access_token: createMockJwt(),
        refresh_token: createMockJwt(7 * 24 * 60 * 60),
        user
      }
    ]
  })

  mock.onPost('/api/auth/login').reply((config) => {
    const body = JSON.parse(config.data || '{}')
    const record = mockUsers.get(String(body.phone || ''))
    if (!record || record.password !== body.password) {
      return [401, { message: '账号或密码错误' }]
    }
    return [
      200,
      {
        access_token: createMockJwt(),
        refresh_token: createMockJwt(7 * 24 * 60 * 60),
        user: record.user
      }
    ]
  })

  mock.onPost('/api/auth/refresh').reply(200, {
    access_token: createMockJwt(),
    refresh_token: createMockJwt(7 * 24 * 60 * 60)
  })

  mock.onPost('/api/auth/logout').reply(200, { success: true })

  mock.onGet('/api/user/profile').reply((config) => {
    const authHeader = config.headers?.Authorization || config.headers?.authorization
    if (!authHeader) {
      return [401, { message: '未登录' }]
    }
    const fallback = mockUsers.get('13800138000')?.user
    return [200, fallback]
  })

  mock.onPut('/api/user/profile').reply((config) => {
    const body = JSON.parse(config.data || '{}')
    const record = mockUsers.get('13800138000')
    if (!record) return [404, { message: '用户不存在' }]
    record.user.nickname = body.nickname || record.user.nickname
    return [200, record.user]
  })

  mock.onPut('/api/user/password').reply(200, { success: true })
}
