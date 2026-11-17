import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { javaFetch, setTokens, clearTokens, accessToken, clearBusinessCache, ApiError } from '@/lib/api'

/** 与 Java `AuthResponse.UserInfo` 一一对应 */
export interface User {
  id: string
  email: string
  name: string
  avatar?: string | null
}

/** 登录/注册/刷新的响应体 */
interface AuthResponse {
  accessToken: string
  refreshToken: string
  tokenType: string
  user: User
}

interface SendCodeResult {
  sent: boolean
  expiresIn: number
  /** 仅 mock 模式返回固定验证码，真实模式无此字段 */
  code?: string
}

export interface RegisterParams {
  email: string
  code: string
  name: string
  password: string
}

const USER_CACHE_KEY = 'ai_companion_user'

/** 从 localStorage 恢复用户缓存；解析失败则清掉脏数据 */
function loadCachedUser(): User | null {
  const raw = localStorage.getItem(USER_CACHE_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    localStorage.removeItem(USER_CACHE_KEY)
    return null
  }
}

function saveUser(value: User): void {
  localStorage.setItem(USER_CACHE_KEY, JSON.stringify(value))
}

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(loadCachedUser())

  /**
   * 登录态以 accessToken 为准（P0-2 口径），而不是 user 对象。
   * 只有 user 缓存没有 token 时视为未登录（例如被 api.ts 的 forceLogout 清过 token）。
   */
  const isAuthenticated = computed(() => accessToken.value !== null)

  /** Java 的 UUID 字符串，供聊天/记忆/情绪请求透传（P0-3） */
  const userId = computed(() => user.value?.id ?? null)

  function applyAuth(data: AuthResponse): void {
    setTokens(data.accessToken, data.refreshToken)
    user.value = data.user
    saveUser(data.user)
  }

  /** 发送邮箱验证码；mock 模式下返回值里带 code，页面可直接提示/回填 */
  async function sendEmailCode(email: string): Promise<SendCodeResult> {
    return javaFetch<SendCodeResult>('/api/v1/auth/send-email-code', {
      method: 'POST',
      body: { email },
      auth: false,
    })
  }

  async function login(email: string, password: string): Promise<User> {
    const data = await javaFetch<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: { email, password },
      auth: false,
    })
    applyAuth(data)
    return data.user
  }

  async function register(params: RegisterParams): Promise<User> {
    const data = await javaFetch<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: params,
      auth: false,
    })
    applyAuth(data)
    return data.user
  }

  /**
   * 有 token 但无用户缓存（如清缓存后刷新）时补齐用户信息。
   * 失败不抛给调用方：token 失效会由 javaFetch 自行登出。
   */
  async function fetchMe(): Promise<User | null> {
    if (!accessToken.value) return null
    try {
      const me = await javaFetch<User>('/api/v1/users/me')
      user.value = me
      saveUser(me)
      return me
    } catch (error) {
      if (error instanceof ApiError && error.status >= 500) console.warn('获取用户信息失败:', error.message)
      return null
    }
  }

  /**
   * 更新个人信息（昵称 / 头像）。
   *
   * 后端 `PUT /api/v1/users/me` 接收 `Map<String,String>`，只取 `name` 与 `avatar`，
   * 返回更新后的 UserInfo。这里成功后立刻写回 user 与 localStorage，
   * 让顶栏、侧栏的头像不用刷新就跟着变。
   */
  async function updateProfile(payload: { name?: string; avatar?: string }): Promise<User> {
    const body: Record<string, string> = {}
    if (typeof payload.name === 'string') body.name = payload.name
    if (typeof payload.avatar === 'string') body.avatar = payload.avatar

    const updated = await javaFetch<User>('/api/v1/users/me', {
      method: 'PUT',
      body,
    })

    user.value = updated
    saveUser(updated)
    return updated
  }

  function logout(): void {
    user.value = null
    localStorage.removeItem(USER_CACHE_KEY)
    clearTokens()
    // 业务缓存必须一起清：否则换账号登录后，后端请求失败走离线兜底时
    // 会把上一个账号的会话/情绪/记忆展示给新用户
    clearBusinessCache()
  }

  return {
    user,
    userId,
    isAuthenticated,
    sendEmailCode,
    login,
    register,
    fetchMe,
    updateProfile,
    logout,
  }
})
