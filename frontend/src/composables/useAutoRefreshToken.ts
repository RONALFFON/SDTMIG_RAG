import { onBeforeUnmount, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const REFRESH_INTERVAL = 4 * 60 * 1000

function parseJwtExp(token: string): number {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return (payload?.exp || 0) * 1000
  } catch {
    return 0
  }
}

/**
 * 自动续期 token：当 access_token 将在 5 分钟内过期时主动刷新
 */
export function useAutoRefreshToken(): void {
  const authStore = useAuthStore()
  let timer: number | null = null

  const checkAndRefresh = async (): Promise<void> => {
    if (!authStore.token || !authStore.refreshToken) return
    const expAt = parseJwtExp(authStore.token)
    if (!expAt) return
    const remain = expAt - Date.now()
    if (remain < 5 * 60 * 1000) {
      try {
        await authStore.refreshAccessToken()
      } catch {
        await authStore.logout(true)
      }
    }
  }

  onMounted(() => {
    checkAndRefresh()
    timer = window.setInterval(checkAndRefresh, REFRESH_INTERVAL)
  })

  onBeforeUnmount(() => {
    if (timer) {
      window.clearInterval(timer)
      timer = null
    }
  })
}
