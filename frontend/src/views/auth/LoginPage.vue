<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 px-4">
    <div class="card-panel w-full max-w-md p-8">
      <div class="mb-6 text-center">
        <div class="mb-2 text-3xl">🤖</div>
        <h1 class="text-xl font-semibold text-slate-900">RAG 智能助手</h1>
        <p class="mt-1 text-sm text-slate-500">欢迎回来，请先登录</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" maxlength="11" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-button
          type="primary"
          class="mt-2 w-full !bg-indigo-600 !border-indigo-600 hover:!bg-indigo-500"
          :loading="submitting"
          :disabled="submitting"
          @click="handleSubmit"
        >
          登录
        </el-button>
      </el-form>

      <div class="mt-5 text-center text-sm text-slate-500">
        还没有账号？
        <RouterLink class="text-indigo-600 hover:text-indigo-500" to="/register">立即注册</RouterLink>
      </div>

      <p
        v-if="import.meta.env.VITE_APP_ENV === 'sandbox'"
        class="mt-4 rounded-lg bg-indigo-50 p-2 text-xs text-indigo-700"
      >
        沙箱测试账号：13800138000 / Test1234
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { isValidPassword, isValidPhone } from '@/utils/validators'

type LoginForm = {
  phone: string
  password: string
}

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const form = reactive<LoginForm>({
  phone: '',
  password: ''
})

const rules: FormRules<LoginForm> = {
  phone: [
    {
      validator: (_rule, value: string, callback) => {
        if (!isValidPhone(value)) {
          callback(new Error('请输入正确的手机号'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ],
  password: [
    {
      validator: (_rule, value: string, callback) => {
        if (!isValidPassword(value)) {
          callback(new Error('密码需为 8-20 位字母+数字组合'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

/**
 * 登录提交
 */
async function handleSubmit(): Promise<void> {
  if (!formRef.value || submitting.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await authStore.login({ phone: form.phone, password: form.password })
    const redirect = (route.query.redirect as string) || '/chat'
    await router.replace(redirect)
    ElMessage.success('登录成功')
  } catch {
    ElMessage.error('账号或密码错误')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
</style>
