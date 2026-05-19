import axios, { AxiosError, AxiosHeaders, type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

type QueuedRequest = {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

interface RetryRequestConfig extends AxiosRequestConfig {
  _retry?: boolean
}

const baseURL = import.meta.env.VITE_API_BASE_URL || ''

export const rawHttp = axios.create({
  baseURL,
  timeout: 15000
})

const http: AxiosInstance = axios.create({
  baseURL,
  timeout: 15000
})

let isRefreshing = false
let requestQueue: QueuedRequest[] = []

function flushQueue(error: unknown, token?: string): void {
  requestQueue.forEach((task) => {
    if (error) {
      task.reject(error)
    } else {
      task.resolve(token || '')
    }
  })
  requestQueue = []
}

function appendAuthHeader(config: AxiosRequestConfig, token: string): AxiosRequestConfig {
  const headers = AxiosHeaders.from(config.headers || {})
  headers.set('Authorization', `Bearer ${token}`)
  return {
    ...config,
    headers
  }
}

http.interceptors.request.use((config) => {
  const authStore = useAuthStore()
  if (authStore.token) {
    return appendAuthHeader(config, authStore.token)
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const status = error.response?.status
    const originalConfig = (error.config || {}) as RetryRequestConfig
    const authStore = useAuthStore()

    if (status !== 401 || originalConfig._retry) {
      return Promise.reject(error)
    }

    if (!authStore.refreshToken) {
      await authStore.logout(true)
      await router.replace(`/login?redirect=${encodeURIComponent(router.currentRoute.value.fullPath)}`)
      return Promise.reject(error)
    }

    originalConfig._retry = true

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        requestQueue.push({
          resolve: (token: string) => resolve(http(appendAuthHeader(originalConfig, token))),
          reject
        })
      })
    }

    isRefreshing = true
    try {
      const newToken = await authStore.refreshAccessToken()
      flushQueue(null, newToken)
      return http(appendAuthHeader(originalConfig, newToken))
    } catch (refreshError) {
      flushQueue(refreshError)
      ElMessage.error('登录状态已失效，请重新登录')
      await authStore.logout(true)
      await router.replace(`/login?redirect=${encodeURIComponent(router.currentRoute.value.fullPath)}`)
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export default http
