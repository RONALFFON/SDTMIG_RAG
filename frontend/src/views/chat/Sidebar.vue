<template>
  <aside class="flex h-full w-full flex-col border-r border-slate-200 bg-white">
    <div class="p-3">
      <button
        class="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-700 transition-base hover:bg-slate-50"
        @click="$emit('create-session')"
      >
        <Plus :size="16" />
        新建对话
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-2 pb-3">
      <button
        v-for="item in sessions"
        :key="item.id"
        class="mb-1 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left transition-base"
        :class="item.id === currentSessionId ? 'bg-indigo-50 text-indigo-700' : 'text-slate-700 hover:bg-slate-50'"
        @click="$emit('switch-session', item.id)"
      >
        <span
          class="h-6 w-1 rounded"
          :class="item.id === currentSessionId ? 'bg-indigo-600' : 'bg-transparent'"
        />
        <div class="min-w-0 flex-1">
          <p class="truncate text-sm font-medium">{{ item.title }}</p>
          <p class="text-xs text-slate-500">{{ item.updatedAt }}</p>
        </div>
      </button>
    </div>

    <div class="border-t border-slate-200 p-3">
      <button
        class="mb-2 flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-700 transition-base hover:bg-slate-50"
        @click="$emit('goto-settings')"
      >
        <Settings :size="16" />
        设置
      </button>
      <div class="flex items-center gap-2 rounded-xl bg-slate-50 px-3 py-2">
        <img class="h-8 w-8 rounded-full" :src="user.avatar || defaultAvatar" alt="avatar" />
        <p class="truncate text-sm font-medium text-slate-700">{{ user.nickname || '未命名用户' }}</p>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { Plus, Settings } from '@lucide/vue-next'
import type { ChatSession } from '@/api/chat'

defineProps<{
  sessions: ChatSession[]
  currentSessionId: string
  user: {
    nickname?: string
    avatar?: string
  }
}>()

defineEmits<{
  'create-session': []
  'switch-session': [sessionId: string]
  'goto-settings': []
}>()

const defaultAvatar = 'https://api.dicebear.com/9.x/thumbs/svg?seed=default-user'
</script>

<style scoped>
</style>
