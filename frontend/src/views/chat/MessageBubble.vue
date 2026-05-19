<template>
  <div :class="wrapperClass">
    <div v-if="role === 'assistant'" class="w-full max-w-[800px]">
      <div
        class="prose prose-slate max-w-none text-[15px] leading-7"
        v-html="renderedAssistantContent"
      />
      <div
        v-if="sources && sources.length"
        class="mt-3 rounded-xl border border-slate-200 bg-white/70 p-3 text-sm"
      >
        <button class="text-indigo-600 transition-base hover:text-indigo-500" @click="expandSources = !expandSources">
          🔍 {{ sources.length }} 个参考来源
        </button>
        <div v-if="expandSources" class="mt-3 space-y-2">
          <div
            v-for="item in sources"
            :key="item.id"
            class="rounded-lg border border-slate-200 bg-slate-50 p-3"
          >
            <div class="font-medium text-slate-800">{{ item.docName }}</div>
            <p class="mt-1 text-slate-600">{{ item.snippet }}</p>
            <p class="mt-1 text-xs text-slate-500">相似度：{{ item.score.toFixed(2) }}</p>
          </div>
        </div>
      </div>
    </div>

    <div
      v-else
      class="max-w-[800px] rounded-2xl bg-[#F3F4F6] px-4 py-3 text-[15px] text-slate-800 shadow-sm"
    >
      {{ content }}
    </div>
  </div>
</template>

<script setup lang="ts">
import MarkdownIt from 'markdown-it'
import type { SourceItem } from '@/api/chat'

const props = withDefaults(
  defineProps<{
    role: 'user' | 'assistant'
    content: string
    sources?: SourceItem[]
    timestamp: string
    enableTyping?: boolean
  }>(),
  {
    sources: () => [],
    enableTyping: true
  }
)

const md = new MarkdownIt({
  html: false,
  breaks: true,
  linkify: true
})

const expandSources = ref(false)
const displayText = ref('')
const rafId = ref<number | null>(null)
const animatedOnce = ref(false)

const wrapperClass = computed(() =>
  props.role === 'user' ? 'flex justify-end py-3' : 'flex justify-start py-3'
)

const renderedAssistantContent = computed(() => {
  if (props.role === 'assistant') {
    return md.render(displayText.value || props.content || '正在思考中...')
  }
  return md.render(props.content)
})

/**
 * 使用 requestAnimationFrame 模拟 AI 逐字输出
 */
function startTypingEffect(): void {
  if (props.role !== 'assistant' || !props.enableTyping || animatedOnce.value) {
    displayText.value = props.content
    return
  }
  const text = props.content || ''
  let index = 0
  displayText.value = ''
  animatedOnce.value = true

  const step = () => {
    index += 2
    displayText.value = text.slice(0, index)
    if (index < text.length) {
      rafId.value = window.requestAnimationFrame(step)
    }
  }
  rafId.value = window.requestAnimationFrame(step)
}

watch(
  () => props.content,
  () => {
    if (props.role !== 'assistant') return
    if (!props.content) return
    startTypingEffect()
  },
  { immediate: true }
)

onBeforeUnmount(() => {
  if (rafId.value) {
    window.cancelAnimationFrame(rafId.value)
    rafId.value = null
  }
})
</script>

<style scoped>
:deep(pre) {
  background: #0f172a;
  color: #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  overflow-x: auto;
}

:deep(code) {
  font-family: Menlo, Monaco, Consolas, 'Courier New', monospace;
}
</style>
