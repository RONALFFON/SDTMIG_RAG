<template>
  <div ref="containerRef" class="h-full overflow-y-auto px-4 py-4">
    <div v-if="messages.length === 0" class="flex h-full items-center justify-center">
      <div class="text-center">
        <div class="mb-3 text-4xl">💬</div>
        <h2 class="text-2xl font-semibold text-slate-900">有什么我可以帮助你的？</h2>
        <p class="mt-2 text-sm text-slate-500">支持文档问答、知识检索与总结生成</p>
      </div>
    </div>

    <TransitionGroup v-else name="message" tag="div" class="mx-auto max-w-[800px]">
      <MessageBubble
        v-for="item in messages"
        :key="item.id"
        :role="item.role"
        :content="item.content"
        :sources="item.sources"
        :timestamp="item.timestamp"
      />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import type { ChatMessage } from '@/api/chat'
import MessageBubble from '@/views/chat/MessageBubble.vue'

const props = defineProps<{
  messages: ChatMessage[]
}>()

const containerRef = ref<HTMLElement | null>(null)

/**
 * 新消息到达后自动滚动到底部
 */
async function scrollToBottom(): Promise<void> {
  await nextTick()
  if (!containerRef.value) return
  containerRef.value.scrollTop = containerRef.value.scrollHeight
}

watch(
  () => props.messages.length,
  () => {
    scrollToBottom()
  },
  { immediate: true }
)
</script>

<style scoped>
.message-enter-active,
.message-leave-active {
  transition: all 240ms ease-in-out;
}

.message-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.message-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
