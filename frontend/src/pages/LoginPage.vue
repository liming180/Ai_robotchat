<template>
  <div class="login">
      <!-- ===== 左：品牌面 ===== -->
      <aside class="login-brand">
        <div class="login-brand__top">
          <button type="button" class="brand" @click="router.push('/')">
            <span class="brand-mark">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path
                  d="M20.8 5.6a5.4 5.4 0 0 0-7.6 0L12 6.8l-1.2-1.2a5.4 5.4 0 1 0-7.6 7.6L12 21l8.8-7.8a5.4 5.4 0 0 0 0-7.6Z"
                />
              </svg>
            </span>
            AI 伴侣
          </button>
        </div>

        <div class="login-brand__mid">
          <p class="eyebrow">
            <Sparkles :size="15" />
            AI COMPANION
          </p>
          <h1 class="login-title">
            它记得你上周<em>没说完</em>的那句话
          </h1>
          <p class="login-lead">
            登录之后，四位预置伴侣和你的自定义伴侣都在。聊天记录、记忆、情绪轨迹、随笔笔记，
            跨设备同步。
          </p>
        </div>

        <div class="login-brand__foot">
          <span><Lock :size="15" /> 对话仅自己可见</span>
          <span><Brain :size="15" /> 记忆可随时删除</span>
        </div>
      </aside>

      <!-- ===== 右：表单 ===== -->
      <div class="login-panel">
        <div class="login-panel__inner">
          <h2 class="panel-title">{{ isLogin ? '欢迎回来' : '创建账号' }}</h2>
          <p class="panel-sub">
            {{ isLogin ? '继续和小暖聊，或者换个人。' : '开始你的 AI 陪伴之旅。' }}
          </p>

          <!-- 切换 -->
          <SegmentedTabs
            :model-value="isLogin ? 'login' : 'register'"
            :options="modeOptions"
            variant="underline"
            aria-label="登录或注册"
            class="panel-tabs"
            @update:model-value="(v) => switchMode(v === 'login')"
          />

          <!-- 错误提示 -->
          <div v-if="errorMessage" class="form-error" role="alert">
            <AlertCircle :size="14" />
            {{ errorMessage }}
          </div>

          <!-- ===== 登录 ===== -->
          <form v-if="isLogin" class="panel-form" @submit.prevent="handleLogin">
            <label class="field" :class="{ 'field--error': !isLogin ? false : false }">
              <span>邮箱</span>
              <input
                v-model="loginForm.email"
                class="input"
                type="email"
                placeholder="请输入邮箱"
                autocomplete="username"
              />
            </label>

            <label class="field">
              <span>密码</span>
              <input
                v-model="loginForm.password"
                class="input"
                type="password"
                placeholder="请输入密码"
                autocomplete="current-password"
              />
            </label>

            <div class="form-row">
              <label class="checkbox is-on">
                <i><Check :size="10" /></i>
                记住我
              </label>
              <button type="button" class="text-link">忘记密码？</button>
            </div>

            <button type="submit" class="btn-primary btn-block" :disabled="isLoading">
              <span v-if="isLoading" class="spinner" />
              <template v-else>
                登录
                <ArrowRight :size="17" />
              </template>
            </button>
          </form>

          <!-- ===== 注册 步骤 1 ===== -->
          <form
            v-else-if="registerStep === 1"
            class="panel-form"
            @submit.prevent="verifyEmail"
          >
            <label class="field">
              <span>邮箱</span>
              <input
                v-model="registerForm.email"
                class="input"
                type="email"
                placeholder="请输入邮箱"
                autocomplete="email"
              />
            </label>

            <label class="field">
              <span>验证码</span>
              <div class="code-row">
                <input
                  v-model="registerForm.code"
                  class="input"
                  type="text"
                  placeholder="请输入验证码"
                  inputmode="numeric"
                />
                <button
                  type="button"
                  class="btn-ghost code-btn"
                  :disabled="countdown > 0 || isLoading"
                  @click="sendEmailCode"
                >
                  {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
                </button>
              </div>
              <small v-if="mockCodeHint" class="code-hint">{{ mockCodeHint }}</small>
            </label>

            <button type="submit" class="btn-primary btn-block" :disabled="isLoading">
              <span v-if="isLoading" class="spinner" />
              <template v-else>
                下一步
                <ArrowRight :size="17" />
              </template>
            </button>
          </form>

          <!-- ===== 注册 步骤 2 ===== -->
          <form v-else class="panel-form" @submit.prevent="completeRegister">
            <label class="field">
              <span>用户名</span>
              <input
                v-model="registerForm.name"
                class="input"
                type="text"
                placeholder="请输入用户名"
                autocomplete="nickname"
              />
            </label>

            <label class="field">
              <span>设置密码</span>
              <input
                v-model="registerForm.password"
                class="input"
                type="password"
                placeholder="请设置密码（至少 6 位）"
                autocomplete="new-password"
              />
            </label>

            <label class="field">
              <span>确认密码</span>
              <input
                v-model="registerForm.confirmPassword"
                class="input"
                type="password"
                placeholder="请再次输入密码"
                autocomplete="new-password"
              />
            </label>

            <div class="form-actions">
              <button type="button" class="btn-ghost" @click="registerStep = 1">上一步</button>
              <button type="submit" class="btn-primary" :disabled="isLoading">
                <span v-if="isLoading" class="spinner" />
                <template v-else>注册</template>
              </button>
            </div>
          </form>

          <p class="panel-legal">
            继续即表示同意 <button type="button" class="text-link">服务条款</button> 与
            <button type="button" class="text-link">隐私政策</button>。我们只在你的账号内保存对话内容，不用于训练。
          </p>
        </div>
      </div>
    </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { AlertCircle, ArrowRight, Brain, Check, Lock, Sparkles } from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import { ApiError } from '@/lib/api'
import SegmentedTabs, { type SegmentedOption } from '@/components/ui/SegmentedTabs.vue'

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

const modeOptions: SegmentedOption[] = [
  { label: '登录', value: 'login' },
  { label: '注册', value: 'register' },
]

const loginForm = ref({
  email: '',
  password: '',
})

const registerForm = ref({
  email: '',
  code: '',
  name: '',
  password: '',
  confirmPassword: '',
})

/** 登录成功后回到来源页（守卫写入的 redirect），无来源则去首页 */
const goAfterLogin = () => {
  const redirect = route.query.redirect
  const target =
    typeof redirect === 'string' && redirect.startsWith('/') && redirect !== '/login'
      ? redirect
      : '/'
  router.push(target)
}

// 已登录则直接跳走
watch(
  () => userStore.isAuthenticated,
  (newVal) => {
    if (newVal) goAfterLogin()
  },
  { immediate: true },
)

/** 把 ApiError 的 message 原样展示，其它异常给通用文案 */
const showError = (error: unknown, fallback: string) => {
  errorMessage.value = error instanceof ApiError ? error.message : fallback
  if (error instanceof ApiError && error.status >= 500) console.error(fallback, error)
}

const switchMode = (login: boolean) => {
  if (isLogin.value === login) return
  isLogin.value = login
  registerStep.value = 1
  errorMessage.value = ''
  mockCodeHint.value = ''
  loginForm.value = { email: '', password: '' }
  registerForm.value = {
    email: '',
    code: '',
    name: '',
    password: '',
    confirmPassword: '',
  }
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

<style scoped>
.login {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 520px);
  min-height: 100vh;
}

/* ---------- 左：品牌面 ---------- */
.login-brand {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: var(--sp-10) var(--sp-16);
  border-right: 1px solid var(--line);
  background:
    radial-gradient(circle at 20% 12%, rgba(255, 139, 114, 0.14), transparent 26rem),
    radial-gradient(circle at 84% 30%, rgba(101, 216, 197, 0.08), transparent 24rem);
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 11px;
  padding: 0;
  border: 0;
  color: var(--text-strong);
  background: transparent;
  font-size: var(--fs-16);
  font-weight: 720;
  cursor: pointer;
}

.brand-mark {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 50%;
  color: #17120f;
  background: var(--primary);
  box-shadow: 0 8px 24px rgba(255, 139, 114, 0.22);
}

.brand-mark svg {
  width: 17px;
  height: 17px;
}

.login-brand__mid {
  max-width: 30em;
}

.eyebrow {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0 0 13px;
  color: var(--accent);
  font-size: var(--fs-12);
  font-weight: 750;
}

.login-title {
  margin: 0;
  color: var(--text-strong);
  font-size: clamp(34px, 4.4vw, var(--fs-44));
  font-weight: 760;
  line-height: var(--lh-tight);
}

.login-title em {
  font-style: normal;
  color: var(--primary);
  white-space: nowrap;
}

.login-lead {
  max-width: 26em;
  margin: var(--sp-6) 0 0;
  color: var(--muted);
  font-size: var(--fs-16);
  line-height: var(--lh-body);
}

.login-brand__foot {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-6);
  color: var(--muted);
  font-size: var(--fs-13);
}

.login-brand__foot span {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.login-brand__foot svg {
  color: var(--accent);
}

/* ---------- 右：表单 ---------- */
.login-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--sp-12);
  border-left: 1px solid var(--line);
  background: var(--bg);
}

.login-panel__inner {
  width: 100%;
  max-width: 356px;
}

.panel-title {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-25);
  font-weight: 720;
}

.panel-sub {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: var(--fs-14);
}

.panel-tabs {
  margin: var(--sp-5) 0 var(--sp-5);
}

.panel-form {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.field {
  display: block;
}

.field > span {
  display: block;
  margin-bottom: var(--sp-2);
  color: var(--text);
  font-size: var(--fs-13);
  font-weight: 650;
}

.field > small {
  display: block;
  margin-top: 7px;
  font-size: var(--fs-12);
}

.input {
  width: 100%;
  min-height: 46px;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-card);
  color: var(--text);
  background: var(--bg);
  font-size: var(--fs-14);
  transition:
    border-color var(--dur) var(--ease),
    box-shadow var(--dur) var(--ease);
}

.input::placeholder {
  color: var(--muted-faint);
}

.input:focus {
  outline: none;
  border-color: var(--accent-line);
  box-shadow: var(--ring-accent);
}

.form-error {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: var(--sp-4);
  padding: 10px 12px;
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--danger-soft);
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

.code-row {
  display: flex;
  gap: var(--sp-2);
}

.code-row .input {
  flex: 1;
  min-width: 0;
}

.code-btn {
  flex-shrink: 0;
  min-width: 104px;
  font-variant-numeric: tabular-nums;
}

.code-hint {
  color: var(--accent);
}

.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
}

.checkbox {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: var(--fs-13);
  cursor: pointer;
}

.checkbox i {
  display: grid;
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 4px;
  color: #17120f;
  background: var(--primary);
}

.text-link {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  padding: 0;
  border: 0;
  color: var(--accent);
  background: transparent;
  font-size: var(--fs-13);
  cursor: pointer;
}

.text-link:hover {
  text-decoration: underline;
}

.btn-primary,
.btn-ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 46px;
  padding: 0 20px;
  border: 0;
  border-radius: var(--radius);
  font-size: var(--fs-14);
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--dur) var(--ease),
    border-color var(--dur) var(--ease),
    opacity var(--dur) var(--ease);
}

.btn-primary {
  color: var(--on-primary);
  background: var(--primary);
  box-shadow: var(--shadow-primary);
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: var(--text);
  background: transparent;
}

.btn-ghost:hover:not(:disabled) {
  border-color: var(--line-strong);
}

.btn-primary:disabled,
.btn-ghost:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.btn-block {
  width: 100%;
  margin-top: var(--sp-1);
}

.form-actions {
  display: flex;
  gap: var(--sp-3);
  margin-top: var(--sp-1);
}

.form-actions > * {
  flex: 1;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(32, 22, 18, 0.28);
  border-top-color: var(--on-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.panel-legal {
  margin: var(--sp-6) 0 0;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  line-height: 1.7;
}

.panel-legal .text-link {
  font-size: inherit;
  color: var(--muted);
}

/* ---------- 响应式 ---------- */
@media (max-width: 1024px) {
  .login {
    grid-template-columns: 1fr;
  }

  .login-brand {
    display: none;
  }

  .login-panel {
    border-left: 0;
    padding: var(--sp-10) var(--sp-6);
  }
}

@media (max-width: 480px) {
  .login-panel {
    padding: var(--sp-8) var(--sp-5);
  }

  .login-panel__inner {
    max-width: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .spinner {
    animation: none;
  }
}
</style>
