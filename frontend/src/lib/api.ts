/**
 * 前端统一 API 层
 *
 * 设计要点：
 * 1. 绝对地址 + 环境变量（不用 Vite proxy，避免 SSE 流式被代理缓冲）
 * 2. 两套响应格式各自解包：Java `{code,message,data}` / Python `{success,message,data}`
 * 3. 业务代码只调 javaFetch / aiFetch，不直接摸 res.data，也不出现 localhost 字面量
 *
 * 该文件不 import 任何 store / router（静态），避免
 * api → router → pages → stores → api 的循环依赖；跳转登录用动态 import。
 */

// ── Token 存储（任务三的 user store 复用同一组键）──
export const TOKEN_KEYS = {
  access: 'ai_companion_access_token',
  refresh: 'ai_companion_refresh_token',
} as const
/** user store 现有的用户信息缓存键，强制登出时一并清理，避免残留旧身份 */
const USER_CACHE_KEY = 'ai_companion_user'

export class ApiError extends Error {
  code: number
  status: number

  constructor(code: number, message: string, status = 0) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

// ── 环境变量（懒解析：缺失时在调用处抛出可读错误，而不是静默回落 localhost）──
function readEnv(name: string, value: string | undefined): string {
  if (!value) {
    throw new ApiError(-1, `缺少环境变量 ${name}，请在 frontend/.env.development 中配置`)
  }
  return value.replace(/\/+$/, '')
}

let apiBaseCache: string | null = null
let aiBaseCache: string | null = null

/** Java 业务后端地址（8080） */
export function getApiBase(): string {
  if (!apiBaseCache) apiBaseCache = readEnv('VITE_API_BASE_URL', import.meta.env.VITE_API_BASE_URL)
  return apiBaseCache
}

/** Python AI 服务地址（5000）；SSE 场景用它自行拼地址 */
export function getAiBase(): string {
  if (!aiBaseCache) aiBaseCache = readEnv('VITE_AI_BASE_URL', import.meta.env.VITE_AI_BASE_URL)
  return aiBaseCache
}

// ── Token 读写 ──
export function getAccessToken(): string | null {
  return localStorage.getItem(TOKEN_KEYS.access)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(TOKEN_KEYS.refresh)
}

export function setTokens(accessToken: string, refreshToken?: string): void {
  localStorage.setItem(TOKEN_KEYS.access, accessToken)
  if (refreshToken) localStorage.setItem(TOKEN_KEYS.refresh, refreshToken)
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEYS.access)
  localStorage.removeItem(TOKEN_KEYS.refresh)
}

// ── 请求参数 ──
export interface FetchOptions extends Omit<RequestInit, 'body'> {
  /** 对象会自动 JSON 序列化；字符串/FormData 原样发送 */
  body?: unknown
  /** 是否注入 Authorization，默认 true */
  auth?: boolean
}

function buildInit(options: FetchOptions, withAuth: boolean, forceToken?: string): RequestInit {
  const headers = new Headers(options.headers)
  let body: BodyInit | undefined

  if (options.body !== undefined && options.body !== null) {
    if (typeof options.body === 'string' || options.body instanceof FormData) {
      body = options.body
    } else {
      body = JSON.stringify(options.body)
      if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
    }
  }

  if (withAuth) {
    const token = forceToken ?? getAccessToken()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  return { ...options, headers, body }
}

async function readJson(res: Response): Promise<unknown> {
  const text = await res.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

/**
 * 网络层失败（服务未启动 / DNS / CORS）时给出可定位的提示，
 * 而不是让调用方看到笼统的 "Failed to fetch"。
 */
async function rawFetch(base: string, path: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(`${base}${path}`, init)
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error)
    throw new ApiError(-1, `无法连接服务 ${base}（${reason}），请确认服务已启动`, 0)
  }
}

// ── 401/403 刷新令牌（单飞：并发请求只触发一次刷新）──
let refreshPromise: Promise<boolean> | null = null

async function refreshAccessToken(): Promise<boolean> {
  if (refreshPromise) return refreshPromise

  const task = (async (): Promise<boolean> => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) return false

    try {
      // 刷新接口本身不走 javaFetch，防止 401 递归
      const res = await rawFetch(getApiBase(), '/api/v1/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refreshToken }),
      })
      if (!res.ok) return false

      const payload = (await readJson(res)) as
        | { code?: number; data?: { accessToken?: string; refreshToken?: string } }
        | null
      if (payload?.code !== 200 || !payload.data?.accessToken) return false

      setTokens(payload.data.accessToken, payload.data.refreshToken ?? refreshToken)
      return true
    } catch {
      return false
    }
  })()

  refreshPromise = task
  try {
    return await task
  } finally {
    if (refreshPromise === task) refreshPromise = null
  }
}

async function forceLogout(): Promise<void> {
  clearTokens()
  // 清掉旧身份缓存，避免守卫读到"有用户但无 token"的中间态
  localStorage.removeItem(USER_CACHE_KEY)

  try {
    const { default: router } = await import('@/router')
    if (router.currentRoute.value.path !== '/login') await router.replace('/login')
  } catch {
    if (window.location.pathname !== '/login') window.location.assign('/login')
  }
}

// ── 响应解包 ──
/** Java `Result`：code === 200 视为成功，返回 data */
export function unwrapJava<T>(payload: unknown, status = 0): T {
  if (!payload || typeof payload !== 'object') {
    throw new ApiError(-1, `响应格式异常（HTTP ${status}）`, status)
  }
  const result = payload as { code?: number; message?: string; data?: T }
  if (result.code !== 200) {
    throw new ApiError(result.code ?? -1, result.message || `请求失败（HTTP ${status}）`, status)
  }
  return result.data as T
}

/** Python `APIResponse`：success === true 视为成功，返回 data */
export function unwrapPython<T>(payload: unknown, status = 0): T {
  if (!payload || typeof payload !== 'object') {
    throw new ApiError(-1, `响应格式异常（HTTP ${status}）`, status)
  }
  const result = payload as { success?: boolean; message?: string; data?: T }
  if (result.success !== true) {
    throw new ApiError(-1, result.message || `请求失败（HTTP ${status}）`, status)
  }
  return result.data as T
}

// ── Java 请求 ──
/**
 * 调 Java 业务后端，返回解包后的 data。
 * 401/403 时尝试用 refreshToken 换新 token 并重试一次；刷新失败则清 token 跳 /login。
 */
export async function javaFetch<T = unknown>(path: string, options: FetchOptions = {}): Promise<T> {
  const withAuth = options.auth !== false
  const base = getApiBase()

  let res = await rawFetch(base, path, buildInit(options, withAuth))

  if (withAuth && (res.status === 401 || res.status === 403)) {
    // 说明：Java 未配 AuthenticationEntryPoint 时未登录返回 403，这里两种码统一按鉴权失败处理
    const refreshed = await refreshAccessToken()
    if (!refreshed) {
      await forceLogout()
      throw new ApiError(res.status, '登录已过期，请重新登录', res.status)
    }
    res = await rawFetch(base, path, buildInit(options, true))
  }

  const payload = await readJson(res)
  if (!res.ok && payload === null) {
    throw new ApiError(res.status, `请求失败（HTTP ${res.status}）`, res.status)
  }
  return unwrapJava<T>(payload, res.status)
}

// ── Python AI 请求 ──
/** 调 Python AI 服务（非流式），返回解包后的 data */
export async function aiFetch<T = unknown>(path: string, options: FetchOptions = {}): Promise<T> {
  const res = await rawFetch(getAiBase(), path, buildInit(options, options.auth === true))
  const payload = await readJson(res)
  if (!res.ok && payload === null) {
    throw new ApiError(res.status, `请求失败（HTTP ${res.status}）`, res.status)
  }
  return unwrapPython<T>(payload, res.status)
}

/** 上传 base64 data URL 到 Java，返回可访问的图片 URL（依赖任务零之一的上传端点） */
export async function uploadImage(dataUrl: string): Promise<string> {
  const data = await javaFetch<{ url?: string }>('/api/v1/uploads', {
    method: 'POST',
    body: { dataUrl },
  })
  if (!data?.url) throw new ApiError(-1, '上传接口未返回图片地址')
  return data.url
}
