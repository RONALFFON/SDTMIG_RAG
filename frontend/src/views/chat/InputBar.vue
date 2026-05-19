<template>
  <div class="border-t border-slate-200 bg-white/90 px-4 py-3 backdrop-blur">
    <div class="mx-auto max-w-[800px]">
      <div v-if="files.length > 0" class="mb-2 flex flex-wrap gap-2">
        <div
          v-for="item in files"
          :key="item.name"
          class="flex items-center gap-2 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-700"
        >
          <span class="max-w-[200px] truncate">{{ item.name }}</span>
          <button class="text-slate-500 hover:text-red-500" @click="removeFile(item)">×</button>
        </div>
      </div>

      <div class="flex items-end gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
        <button
          class="flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition-base hover:bg-slate-100"
          @click="triggerFileSelect"
        >
          <Paperclip :size="18" />
        </button>
        <input
          ref="fileInputRef"
          class="hidden"
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md"
          @change="handleFileChange"
        />

        <textarea
          ref="textareaRef"
          v-model="inputValue"
          class="max-h-[200px] min-h-[48px] flex-1 resize-none border-none bg-transparent px-2 py-2 text-sm outline-none"
          placeholder="输入你的问题，Shift+Enter 换行"
          @keydown="handleKeydown"
          @input="autoResize"
        />

        <button
          class="flex h-9 w-9 items-center justify-center rounded-full text-white transition-base"
          :class="canSend ? 'bg-indigo-600 hover:bg-indigo-500' : 'bg-slate-300 cursor-not-allowed'"
          :disabled="!canSend || sending"
          @click="submit"
        >
          <SendHorizontal :size="16" />
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { Paperclip, SendHorizontal } from '@lucide/vue-next'

const props = defineProps<{
  enterToSend: boolean
  sending: boolean
}>()

const emit = defineEmits<{
  send: [question: string, files: File[]]
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const inputValue = ref('')
const files = ref<File[]>([])

const canSend = computed(() => inputValue.value.trim().length > 0)

/**
 * 自适应文本域高度
 */
function autoResize(): void {
  if (!textareaRef.value) return
  textareaRef.value.style.height = '48px'
  textareaRef.value.style.height = `${Math.min(textareaRef.value.scrollHeight, 200)}px`
}

function triggerFileSelect(): void {
  fileInputRef.value?.click()
}

function handleFileChange(event: Event): void {
  const target = event.target as HTMLInputElement
  const selected = Array.from(target.files || [])
  if (selected.length === 0) return
  files.value = [...files.value, ...selected]
  target.value = ''
}

function removeFile(file: File): void {
  files.value = files.value.filter((item) => item !== file)
}

async function submit(): Promise<void> {
  const question = inputValue.value.trim()
  if (!question || props.sending) return
  emit('send', question, files.value)
  inputValue.value = ''
  files.value = []
  await nextTick()
  autoResize()
}

function handleKeydown(event: KeyboardEvent): void {
  if (!props.enterToSend) return
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    submit().catch(() => ElMessage.error('发送失败，请稍后重试'))
  }
}
</script>

<style scoped>
</style>
