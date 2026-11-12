<template>
  <div class="min-h-screen relative overflow-hidden flex">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 -z-10">
      <div class="absolute top-0 left-0 w-1/2 h-full bg-gradient-to-br from-pink-600/20 via-purple-600/20 to-transparent"></div>
      <div class="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-bl from-orange-500/20 via-pink-500/20 to-transparent"></div>
      <div class="absolute top-1/4 left-1/4 w-96 h-96 bg-pink-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 1.5s"></div>
    </div>

    <!-- 左侧装饰区域 -->
    <div class="hidden lg:flex lg:w-1/2 items-center justify-center p-12">
      <div class="max-w-lg">
        <div class="flex items-center gap-4 mb-8">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center shadow-xl shadow-pink-500/30">
            <svg class="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
          <span class="text-3xl font-bold bg-gradient-to-r from-pink-400 via-purple-400 to-orange-400 bg-clip-text text-transparent">AI 情侣</span>
        </div>
        <h1 class="text-4xl font-bold text-white mb-6">找到属于你的<br>AI 灵魂伴侣</h1>
        <p class="text-slate-400 text-lg leading-relaxed mb-8">
          开始一段温暖的 AI 陪伴之旅，让每一天都充满爱与关怀。我们为你准备了最贴心的互动体验。
        </p>
        <div class="space-y-4">
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-xl bg-green-500/20 flex items-center justify-center">
              <svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <span class="text-slate-300">24小时全天候陪伴</span>
          </div>
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center">
              <svg class="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <span class="text-slate-300">个性化定制专属伴侣</span>
          </div>
          <div class="flex items-center gap-4">
            <div class="w-10 h-10 rounded-xl bg-pink-500/20 flex items-center justify-center">
              <svg class="w-5 h-5 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
              </svg>
            </div>
            <span class="text-slate-300">安全私密的对话环境</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧登录表单 -->
    <div class="flex-1 flex items-center justify-center p-6 lg:p-12">
      <div class="w-full max-w-md">
        <!-- 返回按钮 -->
        <button @click="$router.push('/')" class="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-8">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
          </svg>
          返回首页
        </button>

        <!-- 表单卡片 -->
        <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-8 shadow-2xl">
          <div class="text-center mb-8">
            <h2 class="text-3xl font-bold text-white mb-2">{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
            <p class="text-slate-400">{{ isLogin ? '登录以继续我们的故事' : '开始你的 AI 陪伴之旅' }}</p>
          </div>

          <!-- 切换标签 -->
          <div class="flex bg-white/5 rounded-2xl p-1.5 mb-8">
            <button
              @click="switchMode(true)"
              :class="[
                'flex-1 py-3 rounded-xl font-medium transition-all',
                isLogin ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
              ]"
            >
              登录
            </button>
            <button
              @click="switchMode(false)"
              :class="[
                'flex-1 py-3 rounded-xl font-medium transition-all',
                !isLogin ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
              ]"
            >
              注册
            </button>
          </div>

          <!-- 错误提示 -->
          <div v-if="errorMessage" class="mb-5 px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
            {{ errorMessage }}
          </div>

          <!-- 登录表单 -->
          <form v-if="isLogin" @submit.prevent="handleLogin" class="space-y-5">
            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">邮箱</label>
              <input
                v-model="loginForm.email"
                type="email"
                placeholder="请输入邮箱"
                class="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">密码</label>
              <input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                class="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <button
              type="submit"
              :disabled="isLoading"
              class="w-full py-4 bg-gradient-to-r from-pink-500 via-purple-500 to-orange-500 rounded-xl font-semibold text-white hover:from-pink-400 hover:via-purple-400 hover:to-orange-400 transition-all shadow-xl shadow-pink-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span v-if="isLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span v-else>登录</span>
            </button>
          </form>

          <!-- 注册表单 - 步骤1: 邮箱验证 -->
          <form v-else-if="registerStep === 1" @submit.prevent="verifyEmail" class="space-y-5">
            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">邮箱</label>
              <input
                v-model="registerForm.email"
                type="email"
                placeholder="请输入邮箱"
                class="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">验证码</label>
              <div class="flex gap-3">
                <input
                  v-model="registerForm.code"
                  type="text"
                  placeholder="请输入验证码"
                  class="flex-1 px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
                />
                <button
                  type="button"
                  @click="sendEmailCode"
                  :disabled="countdown > 0"
                  :class="[
                    'px-5 py-3.5 rounded-xl font-medium whitespace-nowrap transition-all',
                    countdown > 0
                      ? 'bg-white/5 text-slate-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-pink-500/20 to-purple-500/20 text-pink-400 hover:from-pink-500/30 hover:to-purple-500/30'
                  ]"
                >
                  {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
                </button>
              </div>
              <p v-if="mockCodeHint" class="text-xs text-pink-400">{{ mockCodeHint }}</p>
            </div>

            <button
              type="submit"
              :disabled="isLoading"
              class="w-full py-4 bg-gradient-to-r from-pink-500 via-purple-500 to-orange-500 rounded-xl font-semibold text-white hover:from-pink-400 hover:via-purple-400 hover:to-orange-400 transition-all shadow-xl shadow-pink-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span v-if="isLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span v-else>下一步</span>
            </button>
          </form>

          <!-- 注册表单 - 步骤2: 设置密码 -->
          <form v-else @submit.prevent="completeRegister" class="space-y-5">
            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">用户名</label>
              <input
                v-model="registerForm.name"
                type="text"
                placeholder="请输入用户名"
                class="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">设置密码</label>
              <input
                v-model="registerForm.password"
                type="password"
                placeholder="请设置密码（至少6位）"
                class="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">确认密码</label>
              <input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                class="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <div class="flex gap-3">
              <button
                type="button"
                @click="registerStep = 1"
                class="flex-1 py-4 bg-white/5 border border-white/10 rounded-xl font-semibold text-slate-300 hover:bg-white/10 transition-all"
              >
                上一步
              </button>
              <button
                type="submit"
                :disabled="isLoading"
                class="flex-1 py-4 bg-gradient-to-r from-pink-500 via-purple-500 to-orange-500 rounded-xl font-semibold text-white hover:from-pink-400 hover:via-purple-400 hover:to-orange-400 transition-all shadow-xl shadow-pink-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <span v-if="isLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                <span v-else>注册</span>
              </button>
            </div>
          </form>
        </div>

        <!-- 底部协议 -->
        <p class="text-center text-slate-500 text-sm mt-8">
          {{ isLogin ? '登录即表示' : '注册即表示' }}同意
          <a href="#" class="text-pink-400 hover:text-pink-300">用户协议</a>
          和
          <a href="#" class="text-pink-400 hover:text-pink-300">隐私政策</a>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ApiError } from '@/lib/api'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const isLogin = ref(true)
const isLoading = ref(false)
const countdown = ref(0)
const registerStep = ref(1)
/** 后端返回的错误文案，内联展示（不再用 alert） */
const errorMessage = ref('')
/** mock 模式下后端回传的固定验证码提示 */
const mockCodeHint = ref('')

const loginForm = ref({
  email: '',
  password: ''
})

const registerForm = ref({
  email: '',
  code: '',
  name: '',
  password: '',
  confirmPassword: ''
})

// 登录成功后回到来源页（守卫写入的 redirect），无来源则去首页
const goAfterLogin = () => {
  const redirect = route.query.redirect
  const target = typeof redirect === 'string' && redirect.startsWith('/') && redirect !== '/login'
    ? redirect
    : '/'
  router.push(target)
}

// 如果已经登录，直接跳转到首页
watch(() => userStore.isAuthenticated, (newVal) => {
  if (newVal) goAfterLogin()
}, { immediate: true })

/** 把 ApiError 的 message 原样展示，其它异常给通用文案 */
const showError = (error: unknown, fallback: string) => {
  errorMessage.value = error instanceof ApiError ? error.message : fallback
  if (error instanceof ApiError && error.status >= 500) console.error(fallback, error)
}

const switchMode = (login: boolean) => {
  isLogin.value = login
  registerStep.value = 1
  errorMessage.value = ''
  mockCodeHint.value = ''
  loginForm.value = { email: '', password: '' }
  registerForm.value = { email: '', code: '', name: '', password: '', confirmPassword: '' }
}

const sendEmailCode = async () => {
  errorMessage.value = ''
  mockCodeHint.value = ''
  const email = registerForm.value.email.trim()
  if (!email) {
    errorMessage.value = '请先填写邮箱'
    return
  }

  try {
    const data = await userStore.sendEmailCode(email)
    // 本地 mock 模式（app.email.mock=true）会直接回传验证码，方便联调
    if (data.code) {
      registerForm.value.code = data.code
      mockCodeHint.value = `本地 mock 验证码：${data.code}（已自动填入）`
    } else {
      mockCodeHint.value = `验证码已发送，${Math.round((data.expiresIn || 300) / 60)} 分钟内有效`
    }

    countdown.value = 60
    const timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (error) {
    showError(error, '验证码发送失败，请重试')
  }
}

const verifyEmail = () => {
  errorMessage.value = ''
  if (!registerForm.value.email.trim()) {
    errorMessage.value = '请填写邮箱'
    return
  }
  if (!registerForm.value.code.trim()) {
    errorMessage.value = '请填写验证码'
    return
  }
  registerStep.value = 2
}

const completeRegister = async () => {
  errorMessage.value = ''
  if (!registerForm.value.name.trim()) {
    errorMessage.value = '请填写用户名'
    return
  }
  if (registerForm.value.password.length < 6) {
    errorMessage.value = '密码至少 6 位'
    return
  }
  if (registerForm.value.password !== registerForm.value.confirmPassword) {
    errorMessage.value = '两次输入的密码不一致'
    return
  }

  isLoading.value = true
  try {
    await userStore.register({
      email: registerForm.value.email.trim(),
      code: registerForm.value.code.trim(),
      name: registerForm.value.name.trim(),
      password: registerForm.value.password,
    })
    goAfterLogin()
  } catch (error) {
    showError(error, '注册失败，请重试')
  } finally {
    isLoading.value = false
  }
}

const handleLogin = async () => {
  errorMessage.value = ''
  if (!loginForm.value.email.trim() || !loginForm.value.password) {
    errorMessage.value = '请填写邮箱和密码'
    return
  }

  isLoading.value = true
  try {
    await userStore.login(loginForm.value.email.trim(), loginForm.value.password)
    goAfterLogin()
  } catch (error) {
    showError(error, '登录失败，请重试')
  } finally {
    isLoading.value = false
  }
}
</script>
