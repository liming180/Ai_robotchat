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
        <button @click="$router.push('/home')" class="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-8">
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
              @click="isLogin = true"
              :class="[
                'flex-1 py-3 rounded-xl font-medium transition-all',
                isLogin ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
              ]"
            >
              登录
            </button>
            <button
              @click="isLogin = false"
              :class="[
                'flex-1 py-3 rounded-xl font-medium transition-all',
                !isLogin ? 'bg-gradient-to-r from-pink-500 to-purple-600 text-white shadow-lg' : 'text-slate-400 hover:text-white'
              ]"
            >
              注册
            </button>
          </div>

          <!-- 表单 -->
          <form @submit.prevent="handleSubmit" class="space-y-5">
            <div v-if="!isLogin" class="space-y-2">
              <label class="text-sm font-medium text-slate-300">昵称</label>
              <input
                v-model="form.name"
                type="text"
                placeholder="请输入你的昵称"
                class="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">手机号</label>
              <input
                v-model="form.phone"
                type="tel"
                placeholder="请输入手机号"
                class="w-full px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <div class="space-y-2">
              <label class="text-sm font-medium text-slate-300">验证码</label>
              <div class="flex gap-3">
                <input
                  v-model="form.code"
                  type="text"
                  placeholder="请输入验证码"
                  class="flex-1 px-4 py-3.5 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
                />
                <button
                  type="button"
                  @click="sendCode"
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
            </div>

            <button
              type="submit"
              :disabled="isLoading"
              class="w-full py-4 bg-gradient-to-r from-pink-500 via-purple-500 to-orange-500 rounded-xl font-semibold text-white hover:from-pink-400 hover:via-purple-400 hover:to-orange-400 transition-all shadow-xl shadow-pink-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 glow-button"
            >
              <span v-if="isLoading" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              <span v-else>{{ isLogin ? '登录' : '注册并开始' }}</span>
            </button>
          </form>

          <!-- 分割线 -->
          <div class="flex items-center gap-4 my-8">
            <div class="flex-1 h-px bg-white/10"></div>
            <span class="text-slate-500 text-sm">或</span>
            <div class="flex-1 h-px bg-white/10"></div>
          </div>

          <!-- 第三方登录 -->
          <div class="grid grid-cols-2 gap-4">
            <button class="flex items-center justify-center gap-3 py-3.5 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all">
              <div class="w-6 h-6 bg-green-500 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348z"/>
                </svg>
              </div>
              <span class="text-slate-300 font-medium">微信</span>
            </button>
            <button class="flex items-center justify-center gap-3 py-3.5 bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all">
              <div class="w-6 h-6 bg-blue-500 rounded-lg flex items-center justify-center">
                <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12.003 2c-2.265 0-6.29 1.364-6.29 7.325 0 2.218 1.17 4.08 2.982 5.223a.49.49 0 0 1 .201.566l-.364 1.363c-.023.085-.045.17-.045.26 0 .198.157.358.35.358a.392.392 0 0 0 .2-.065l1.746-1.023a.798.798 0 0 1 .662-.09c1.135.343 2.35.53 3.558.53 2.266 0 6.29-1.365 6.29-7.326C21.298 3.364 17.27 2 12.003 2z"/>
                </svg>
              </div>
              <span class="text-slate-300 font-medium">QQ</span>
            </button>
          </div>
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLogin = ref(true)
const isLoading = ref(false)
const countdown = ref(0)

const form = ref({
  name: '',
  phone: '',
  code: ''
})

const sendCode = () => {
  if (!form.value.phone) return
  countdown.value = 60
  const timer = setInterval(() => {
    countdown.value--
    if (countdown.value <= 0) {
      clearInterval(timer)
    }
  }, 1000)
}

const handleSubmit = async () => {
  isLoading.value = true
  // 模拟登录/注册
  await new Promise(resolve => setTimeout(resolve, 1500))
  isLoading.value = false
  router.push('/')
}
</script>
