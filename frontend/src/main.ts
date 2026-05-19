import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from '@/App.vue'
import router from '@/router'
import { setupRouterGuard } from '@/router/guard'
import { setupMock } from '@/mock/setup'
import '@/styles/global.css'

async function bootstrap(): Promise<void> {
  await setupMock()

  const app = createApp(App)
  const pinia = createPinia()

  app.use(pinia)
  app.use(router)
  app.use(ElementPlus)

  setupRouterGuard(router)

  app.mount('#app')
}

bootstrap()
