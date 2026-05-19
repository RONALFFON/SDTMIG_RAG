<script setup lang="ts">
import { useAutoRefreshToken } from '@/composables/useAutoRefreshToken'

useAutoRefreshToken()
</script>

<template>
  <RouterView />
  <div
    v-if="import.meta.env.VITE_APP_ENV === 'sandbox'"
    class="fixed right-4 top-4 z-50 rounded-full bg-indigo-600/85 px-3 py-1 text-xs text-white shadow"
  >
    🔧 Sandbox
  </div>
</template>
