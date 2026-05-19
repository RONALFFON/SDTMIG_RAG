import { defineStore } from 'pinia'
import { loginApi, logoutApi, refreshTokenApi, registerApi, sendCodeApi, type AuthUser } from '@/api/auth'
import { getProfileApi } from '@/api/user'

const TOKEN_KEY = 'rag_access_token'
const REFRESH_TOKEN_KEY = 'rag_refresh_token'
const USER_KEY = 'rag_user'

type RegisterParams = {
  phone: string
  code: string
  password: string
}

type LoginParams = {
  phone: string
  password: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY) || '',
    user: (JSON.parse(localStorage.getItem(USER_KEY) || 'null') as AuthUser | null) || null,
    isLoggedIn: Boolean(localStorage.getItem(TOKEN_KEY))
  }),
  actions: {
    /**
     * 写入 token 与用户信息
     */
    applyAuth(payload: { token: string; refreshToken: string; user: AuthUser }): void {
      this.token = payload.token
      this.refreshToken = payload.refreshToken
      this.user = payload.user
      this.isLoggedIn = true

      localStorage.setItem(TOKEN_KEY, payload.token)
      localStorage.setItem(REFRESH_TOKEN_KEY, payload.refreshToken)
      localStorage.setItem(USER_KEY, JSON.stringify(payload.user))
    },

    /**
     * 登录动作
     */
    async login(params: LoginParams): Promise<void> {
      const result = await loginApi(params)
      this.applyAuth({
        token: result.access_token,
        refreshToken: result.refresh_token,
        user: result.user
      })
    },

    /**
     * 注册动作
     */
    async register(params: RegisterParams): Promise<void> {
      const result = await registerApi(params)
      this.applyAuth({
        token: result.access_token,
        refreshToken: result.refresh_token,
        user: result.user
      })
    },

    /**
     * 发送验证码
     */
    async sendCode(phone: string): Promise<void> {
      await sendCodeApi(phone)
    },

    /**
     * 刷新 token
     */
    async refreshAccessToken(): Promise<string> {
      if (!this.refreshToken) {
        throw new Error('无可用 refresh_token')
      }
      const result = await refreshTokenApi(this.refreshToken)
      this.token = result.access_token
      this.refreshToken = result.refresh_token
      this.isLoggedIn = true

      localStorage.setItem(TOKEN_KEY, result.access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, result.refresh_token)
      return result.access_token
    },

    /**
     * 退出登录
     */
    async logout(silent = false): Promise<void> {
      if (!silent && this.token) {
        try {
          await logoutApi()
        } catch {
          // 忽略退出接口失败，前端仍需清理态
        }
      }
      this.token = ''
      this.refreshToken = ''
      this.user = null
      this.isLoggedIn = false
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },

    /**
     * 拉取最新用户资料
     */
    async loadProfile(): Promise<void> {
      if (!this.token) return
      const profile = await getProfileApi()
      this.user = profile
      localStorage.setItem(USER_KEY, JSON.stringify(profile))
    }
  }
})
