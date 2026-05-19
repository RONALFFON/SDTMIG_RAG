import MockAdapter from 'axios-mock-adapter'
import http, { rawHttp } from '@/utils/request'
import { setupAuthMock } from '@/mock/auth.mock'
import { setupChatMock } from '@/mock/chat.mock'

let hasSetup = false

/**
 * 根据环境变量注册沙箱 Mock
 */
export async function setupMock(): Promise<void> {
  if (hasSetup || import.meta.env.VITE_USE_MOCK !== 'true') return

  const httpMock = new MockAdapter(http, { delayResponse: 800 })
  const rawMock = new MockAdapter(rawHttp, { delayResponse: 500 })

  setupAuthMock(httpMock)
  setupAuthMock(rawMock)
  setupChatMock(httpMock)

  hasSetup = true
}
