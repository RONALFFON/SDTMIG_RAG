<template>
  <div class="flex h-screen bg-slate-50">
    <div class="hidden w-[260px] md:block">
      <Sidebar
        :sessions="chatStore.sessions"
        :current-session-id="chatStore.currentSessionId"
        :user="authStore.user || {}"
        @create-session="handleCreateSession"
        @switch-session="handleSwitchSession"
        @goto-settings="gotoSettings"
      />
    </div>

    <el-drawer v-model="drawerVisible" size="260px" :with-header="false" direction="ltr" class="md:!hidden">
      <Sidebar
        :sessions="chatStore.sessions"
        :current-session-id="chatStore.currentSessionId"
        :user="authStore.user || {}"
        @create-session="handleCreateSession"
        @switch-session="handleSwitchSession"
        @goto-settings="gotoSettings"
      />
    </el-drawer>

    <section class="flex min-w-0 flex-1 flex-col">
      <header class="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4">
        <div class="flex items-center gap-2">
          <button class="rounded-lg p-2 transition-base hover:bg-slate-100 md:hidden" @click="drawerVisible = true">
            <Menu :size="18" />
          </button>
          <h1 class="max-w-[380px] truncate text-sm font-semibold text-slate-800">
            {{ currentTitle }}
          </h1>
        </div>
        <div class="rounded-full bg-emerald-50 px-2 py-1 text-xs text-emerald-600">模型在线</div>
      </header>

      <div class="min-h-0 flex-1">
        <MessageArea :messages="chatStore.messages" />
      </div>

      <InputBar
        :enter-to-send="chatStore.enterToSend"
        :sending="sending"
        @send="handleSend"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { Menu } from '@lucide/vue-next'
import { useRouter } from 'vue-router'
import Sidebar from '@/views/chat/Sidebar.vue'
import MessageArea from '@/views/chat/MessageArea.vue'
import InputBar from '@/views/chat/InputBar.vue'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const drawerVisible = ref(false)
const sending = ref(false)

const currentTitle = computed(() => {
  const session = chatStore.sessions.find((item) => item.id === chatStore.currentSessionId)
  return session?.title || '新对话'
})

async function handleCreateSession(): Promise<void> {
  await chatStore.createSession()
  drawerVisible.value = false
}

async function handleSwitchSession(sessionId: string): Promise<void> {
  await chatStore.switchSession(sessionId)
  drawerVisible.value = false
}

function gotoSettings(): void {
  drawerVisible.value = false
  router.push('/settings')
}

/**
 * 发送消息：先上传附件，再请求问答
 */
async function handleSend(question: string, files: File[]): Promise<void> {
  if (sending.value) return
  sending.value = true
  try {
    for (const file of files) {
      // TODO: 二期可补充上传进度轮询
      await chatStore.uploadFile(file)
    }
    await chatStore.sendMessage(question)
  } catch {
    ElMessage.error('发送失败，请稍后重试')
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  try {
    await Promise.all([chatStore.fetchSessions(), authStore.loadProfile()])
  } catch {
    ElMessage.warning('会话加载异常，请刷新重试')
  }
})
</script>

<style scoped>
</style>
