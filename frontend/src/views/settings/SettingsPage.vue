<template>
  <div class="min-h-screen bg-slate-50 p-4 md:p-6">
    <div class="mx-auto max-w-4xl">
      <button class="mb-4 flex items-center gap-1 text-sm text-slate-600 hover:text-slate-900" @click="router.push('/chat')">
        <ArrowLeft :size="16" />
        返回聊天
      </button>

      <div class="space-y-4">
        <section class="card-panel p-5">
          <h2 class="text-base font-semibold text-slate-900">账号信息</h2>
          <div class="mt-4 flex items-center gap-3">
            <img :src="authStore.user?.avatar || defaultAvatar" class="h-12 w-12 rounded-full" alt="avatar" />
            <div class="flex-1">
              <el-input v-model="nickname" placeholder="请输入昵称" />
            </div>
            <el-button @click="saveProfile">保存</el-button>
          </div>
          <p class="mt-3 text-sm text-slate-600">手机号：{{ maskedPhone }}</p>
        </section>

        <section class="card-panel p-5">
          <h2 class="text-base font-semibold text-slate-900">安全设置</h2>
          <el-button class="mt-3" @click="showPasswordForm = !showPasswordForm">
            {{ showPasswordForm ? '收起修改密码' : '修改密码' }}
          </el-button>
          <el-form v-if="showPasswordForm" class="mt-3 grid grid-cols-1 gap-3 md:grid-cols-3">
            <el-input v-model="passwordForm.oldPassword" type="password" show-password placeholder="旧密码" />
            <el-input v-model="passwordForm.newPassword" type="password" show-password placeholder="新密码" />
            <el-input v-model="passwordForm.confirmPassword" type="password" show-password placeholder="确认新密码" />
            <div class="md:col-span-3">
              <el-button type="primary" @click="handleUpdatePassword">确认修改</el-button>
            </div>
          </el-form>
          <el-button class="mt-4 !text-red-600" link @click="handleLogout">退出登录</el-button>
        </section>

        <section class="card-panel p-5">
          <h2 class="text-base font-semibold text-slate-900">偏好设置</h2>
          <div class="mt-3 flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
            <span class="text-sm text-slate-700">主题模式（预留）</span>
            <el-switch v-model="darkMode" />
          </div>
          <div class="mt-2 flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
            <span class="text-sm text-slate-700">回车发送</span>
            <el-switch v-model="enterToSend" @change="chatStore.setEnterToSend" />
          </div>
          <div class="mt-2 flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2">
            <span class="text-sm text-slate-700">回答渲染偏好</span>
            <el-select v-model="renderMode" style="width: 160px" @change="chatStore.setRenderMode">
              <el-option label="Markdown" value="markdown" />
              <el-option label="纯文本" value="text" />
            </el-select>
          </div>
        </section>

        <section class="card-panel p-5">
          <h2 class="text-base font-semibold text-slate-900">关于</h2>
          <div class="mt-3 space-y-1 text-sm text-slate-600">
            <p>前端版本：{{ appVersion }}</p>
            <p>
              环境标识：
              <span class="rounded bg-indigo-100 px-2 py-0.5 text-xs text-indigo-700">
                {{ envLabel }}
              </span>
            </p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft } from '@lucide/vue-next'
import { useRouter } from 'vue-router'
import { updatePasswordApi, updateProfileApi } from '@/api/user'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import { maskPhone } from '@/utils/format'
import { isValidPassword } from '@/utils/validators'
import packageJson from '../../../package.json'

const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const defaultAvatar = 'https://api.dicebear.com/9.x/thumbs/svg?seed=default-user'
const nickname = ref(authStore.user?.nickname || '')
const showPasswordForm = ref(false)
const darkMode = ref(false)
const enterToSend = ref(chatStore.enterToSend)
const renderMode = ref(chatStore.renderMode)

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const appVersion = packageJson.version
const envLabel = computed(() => (import.meta.env.VITE_APP_ENV === 'sandbox' ? 'Sandbox' : 'Production'))
const maskedPhone = computed(() => maskPhone(authStore.user?.phone || ''))

/**
 * 保存昵称
 */
async function saveProfile(): Promise<void> {
  if (!nickname.value.trim()) {
    ElMessage.warning('昵称不能为空')
    return
  }
  const user = await updateProfileApi({ nickname: nickname.value.trim() })
  authStore.user = user
  ElMessage.success('保存成功')
}

/**
 * 修改密码
 */
async function handleUpdatePassword(): Promise<void> {
  if (!isValidPassword(passwordForm.newPassword)) {
    ElMessage.error('密码需为 8-20 位字母+数字组合')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }
  await updatePasswordApi({
    oldPassword: passwordForm.oldPassword,
    newPassword: passwordForm.newPassword
  })
  ElMessage.success('密码修改成功')
  passwordForm.oldPassword = ''
  passwordForm.newPassword = ''
  passwordForm.confirmPassword = ''
}

/**
 * 退出登录并返回登录页
 */
async function handleLogout(): Promise<void> {
  await ElMessageBox.confirm('确认退出当前账号吗？', '提示', {
    type: 'warning'
  })
  await authStore.logout()
  await router.replace('/login')
}
</script>

<style scoped>
</style>
