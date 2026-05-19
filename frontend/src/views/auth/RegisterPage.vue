<template>
  <div class="flex min-h-screen items-center justify-center bg-slate-50 px-4">
    <div class="card-panel w-full max-w-md p-8">
      <div class="mb-6 text-center">
        <div class="mb-2 text-3xl">✨</div>
        <h1 class="text-xl font-semibold text-slate-900">创建账号</h1>
        <p class="mt-1 text-sm text-slate-500">注册后即可体验智能问答</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="form.phone" maxlength="11" placeholder="请输入手机号" />
        </el-form-item>

        <el-form-item label="验证码" prop="code">
          <div class="flex w-full gap-2">
            <el-input v-model="form.code" maxlength="6" placeholder="请输入 6 位验证码" />
            <el-button :disabled="countdown > 0" @click="handleSendCode">
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" show-password placeholder="请再次输入密码" />
        </el-form-item>

        <el-button
          type="primary"
          class="mt-2 w-full !bg-indigo-600 !border-indigo-600 hover:!bg-indigo-500"
          :loading="submitting"
          :disabled="submitting"
          @click="handleSubmit"
        >
          注册并登录
        </el-button>
      </el-form>

      <div class="mt-5 text-center text-sm text-slate-500">
        已有账号？
        <RouterLink class="text-indigo-600 hover:text-indigo-500" to="/login">去登录</RouterLink>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { isValidCode, isValidPassword, isValidPhone } from '@/utils/validators'

type RegisterForm = {
  phone: string
  code: string
  password: string
  confirmPassword: string
}

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const countdown = ref(0)
const form = reactive<RegisterForm>({
  phone: '',
  code: '',
  password: '',
  confirmPassword: ''
})

let timer: number | null = null

const rules: FormRules<RegisterForm> = {
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
  code: [
    {
      validator: (_rule, value: string, callback) => {
        if (!isValidCode(value)) {
          callback(new Error('请输入正确的 6 位验证码'))
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
  ],
  confirmPassword: [
    {
      validator: (_rule, value: string, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur'
    }
  ]
}

/**
 * 发送验证码并启动倒计时
 */
async function handleSendCode(): Promise<void> {
  if (!isValidPhone(form.phone)) {
    ElMessage.error('请输入正确的手机号')
    return
  }
  try {
    await authStore.sendCode(form.phone)
    ElMessage.success('验证码已发送')
    countdown.value = 60
    timer = window.setInterval(() => {
      countdown.value -= 1
      if (countdown.value <= 0 && timer) {
        window.clearInterval(timer)
        timer = null
      }
    }, 1000)
  } catch {
    ElMessage.error('验证码发送失败，请稍后重试')
  }
}

/**
 * 提交注册并自动登录
 */
async function handleSubmit(): Promise<void> {
  if (!formRef.value || submitting.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    await authStore.register({
      phone: form.phone,
      code: form.code,
      password: form.password
    })
    ElMessage.success('注册成功')
    await router.replace('/chat')
  } catch {
    ElMessage.error('注册失败，请检查信息后重试')
  } finally {
    submitting.value = false
  }
}

onBeforeUnmount(() => {
  if (timer) {
    window.clearInterval(timer)
    timer = null
  }
})
</script>

<style scoped>
</style>
