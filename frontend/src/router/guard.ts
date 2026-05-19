import type { Router } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const whiteList = ['/login', '/register']

/**
 * 注册全局前置守卫，处理登录态鉴权
 */
export function setupRouterGuard(router: Router): void {
  router.beforeEach((to, _from, next) => {
    const authStore = useAuthStore()
    const hasToken = Boolean(authStore.token)

    if (hasToken && whiteList.includes(to.path)) {
      next('/chat')
      return
    }

    if (!hasToken && !whiteList.includes(to.path)) {
      next(`/login?redirect=${encodeURIComponent(to.fullPath)}`)
      return
    }

    next()
  })
}
