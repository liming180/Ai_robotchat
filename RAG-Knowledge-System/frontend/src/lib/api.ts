/**
 * RAG 后端（8002）统一 API 层。
 *
 * 关键口径：
 * - 响应包装 {success, message, data, error, timestamp}，按 success 判断成败（不要按 code）。
 * - 管理接口（collections / documents / tasks / companions）走 Authorization: Bearer <JWT>。
 * - /retrieve 挂的是 verify_service_token，必须带 X-Service-Token，与 JWT 是两套鉴权；
 *   缺 token 时后端返回 401，但**不能**当作「登录过期」清凭证踢回登录页。
 * - 登录转发返回 Java 的 AuthResponse：{accessToken, refreshToken, tokenType, user}。
 */
import axios from 'axios'
import type { AxiosError, AxiosInstance } from 'axios'

// 默认写 127.0.0.1 而不是 localhost：uvicorn 只监听 IPv4，
// 浏览器访问 localhost 会先走 ::1 再回落，部分内核下直接报 Network Error。
const BASE_URL = (import.meta.env.VITE_RAG_API_BASE_URL || 'http://127.0.0.1:8002').replace(/\/+$/, '')
const SERVICE_TOKEN = (import.meta.env.VITE_RAG_SERVICE_TOKEN || '').trim()
const PREFIX = '/api/v1/kb'
const TOKEN_KEY = 'rag_access_token'
const USER_KEY = 'rag_user'

export interface RagResponse<T = unknown> {
  success: boolean
  message?: string | null
  data: T
  error?: { code?: string; message?: string; details?: unknown } | null
  timestamp?: string
}

export interface AuthUser {
  id: string
  email: string
  name?: string
  avatar?: string | null
}

export interface AuthData {
  accessToken: string
  refreshToken: string
  tokenType: string
  user: AuthUser
}

/** JSON 文件的解析规则（后端 app/schemas/collection.py::ParserConfig）。 */
export interface ParserConfig {
  itemsPath?: string | null
  contentField?: string
  titleField?: string | null
  metaFields?: string[]
}

export interface CollectionItem {
  id: string
  name: string
  description?: string | null
  companionId?: string | null
  parserConfig?: ParserConfig | null
  embeddingModel: string
  embeddingDim: number
  embeddingBackend: string
  chunkSize: number
  chunkOverlap: number
  documentCount: number
  chunkCount: number
  status: string
  createdBy?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}

export interface CollectionPayload {
  name: string
  description?: string
  companionId?: string
  chunkSize?: number
  chunkOverlap?: number
  parserConfig?: ParserConfig | null
  status?: string
}

export interface DocumentItem {
  id: string
  collectionId: string
  sourceType: string
  title: string
  fileName?: string | null
  fileExt?: string | null
  fileSize?: number | null
  status: string
  progress: number
  errorMsg?: string | null
  taskId?: string | null
  chunkCount: number
  createdAt?: string | null
  updatedAt?: string | null
}

export interface ChunkItem {
  id: string
  documentId: string
  collectionId: string
  chunkIndex: number
  content: string
  charCount: number
  vectorId: string
  meta?: Record<string, unknown> | null
}

export interface DocumentDetail extends DocumentItem {
  rawContent?: string | null
  filePath?: string | null
  chunks?: ChunkItem[]
}

export interface UploadResultItem {
  documentId: string
  taskId: string
  title: string
  fileName?: string | null
}

export interface CompanionItem {
  id: string
  name: string
  avatar?: string | null
  description?: string | null
  category?: string | null
  personality?: string | null
}

export interface TaskStatus {
  taskId: string
  documentId: string
  status: string
  progress: number
  errorMsg?: string | null
  chunkCount: number
}

export interface RetrievedChunk {
  content: string
  score: number
  documentId?: string | null
  documentTitle?: string | null
  collectionId?: string | null
  collectionName?: string | null
  chunkIndex?: number | null
}

/** 分数尺度：cosine / tei 是 0~1 相似度；rrf 是名次融合分（0.015~0.033 量级）。 */
export type ScoreScale = 'cosine' | 'tei' | 'rrf' | string

export interface RetrieveResult {
  chunks: RetrievedChunk[]
  elapsedMs: number
  searchedCollections: string[]
  scoreScale: ScoreScale
}

export interface RetrievePayload {
  query: string
  companionId?: string
  collectionIds?: string[]
  topK?: number
  scoreThreshold?: number
}

export interface HealthInfo {
  service: string
  version: string
  env: string
  database: string
  mainDatabase: string
  embeddingConfigured: boolean
  vectorStore?: string
  /** 2026-11-25 起 /health 真实探活 Milvus：connected / unavailable / disabled */
  milvus?: string
  milvusLatencyMs?: number
  milvusVersion?: string
}

/**
 * 健康检查结果。
 *
 * 后端 2026-11-25 起在 Milvus 不可用时返回 **HTTP 503**（进程活着但干不了活），
 * 所以不能只按「请求成功/失败」二分：要能区分「8002 没起来」和
 * 「8002 在跑但向量库挂了」——后者检索一定失败，提示要指向 Milvus 容器。
 */
export interface HealthProbe {
  /** 进程是否响应（任何 HTTP 状态码都算活着） */
  reachable: boolean
  httpStatus: number
  data: HealthInfo | null
  message: string
}

export interface PageResult<T> {
  items: T[]
  total: number
  page?: number
  pageSize?: number
}

/* ------------------------------------------------------------------ */
/* 本地凭证                                                            */
/* ------------------------------------------------------------------ */

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function getUser(): AuthUser | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    return null
  }
}

export function setUser(user: AuthUser | null): void {
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user))
  else localStorage.removeItem(USER_KEY)
}

/**
 * 本地联调种子凭证（仅开发环境生效）。
 *
 * 用途：本机没有可用的账号口令时，也能进管理台逐页联调 / 走查。
 * - 只在 `import.meta.env.DEV` 下执行，生产构建里这段被静态剔除；
 * - token 由 `VITE_DEV_TOKEN` 注入（写 .env.development.local，不进仓库）；
 * - 用户信息从 JWT 载荷解析，不在前端硬编码任何身份。
 */
export function seedDevCredentials(): void {
  if (!import.meta.env.DEV || getToken()) return
  const devToken = (import.meta.env.VITE_DEV_TOKEN || '').trim()
  if (!devToken) return
  try {
    const payload = JSON.parse(
      atob(devToken.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')),
    ) as { userId?: string; email?: string }
    setToken(devToken)
    setUser({ id: payload.userId || '', email: payload.email || '' })
    // eslint-disable-next-line no-console
    console.info('[dev] 已注入联调凭证：', payload.email || payload.userId)
  } catch {
    // eslint-disable-next-line no-console
    console.warn('[dev] VITE_DEV_TOKEN 解析失败，已忽略')
  }
}

/* ------------------------------------------------------------------ */
/* axios 实例                                                          */
/* ------------------------------------------------------------------ */

const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
})

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

/** 后端 401 有两种来源，必须区分：登录过期 vs 服务间密钥不匹配。 */
function isServiceTokenFailure(message: string): boolean {
  return /x-service-token/i.test(message)
}

http.interceptors.response.use(
  (resp) => resp,
  (error: AxiosError<RagResponse>) => {
    const status = error.response?.status
    const body = error.response?.data
    const message = body?.error?.message || body?.message || ''
    if (message) error.message = message

    if (status === 401 && !isServiceTokenFailure(message)) {
      // 登录过期/令牌无效：清凭证并回登录页（登录接口自身的 401 不触发跳转）
      clearToken()
      setUser(null)
      if (!location.pathname.startsWith('/login')) location.href = '/login'
    }
    return Promise.reject(error)
  },
)

async function unwrap<T>(promise: Promise<{ data: RagResponse<T> }>): Promise<T> {
  const resp = await promise
  const body = resp.data
  if (!body?.success) {
    throw new Error(body?.error?.message || body?.message || '请求失败')
  }
  return body.data
}

/** 统一把任意异常转成可读文案（含后端 message / HTTP 状态）。 */
export function apiErrorMessage(e: unknown, fallback = '请求失败'): string {
  if (axios.isAxiosError(e)) {
    // 顺序很关键：axios 的超时/网络错误 message 是英文（"timeout of 90000ms exceeded"、
    // "Network Error"），先翻成中文口径，别把英文原文直接甩给用户。
    if (e.code === 'ECONNABORTED') {
      return '请求超时：首次检索要等 Milvus 加载集合，冷启动可达 30–60s；持续超时请确认 milvus-standalone 容器在运行'
    }
    if (!e.response) return '无法连接 8002：请确认 RAG 后端已启动（端口 8002），并且前端代理 /rag-api 可用'
    const status = e.response.status
    const body = e.response.data as RagResponse | undefined
    const backendMsg = body?.error?.message || body?.message || ''
    if (backendMsg) return backendMsg
    if (status === 502 || status === 503) return `${fallback}：服务暂不可用（HTTP ${status}），稍后重试`
    return `${fallback}（HTTP ${status}）`
  }
  if (e instanceof Error && e.message) return e.message
  return fallback
}

/** 检索接口专用的请求配置：服务间密钥缺失时后端会 401，页面据此给出明确提示。 */
const retrieveConfig = {
  headers: SERVICE_TOKEN ? { 'X-Service-Token': SERVICE_TOKEN } : undefined,
  timeout: 90000, // rerank 模式下单次检索可达 20~40s
}

export const hasServiceToken = Boolean(SERVICE_TOKEN)

/* ------------------------------------------------------------------ */
/* API                                                                 */
/* ------------------------------------------------------------------ */

export const api = {
  // ---- 登录（8002 转发 Java 8081）----
  login: (email: string, password: string) =>
    unwrap<AuthData>(http.post('/api/v1/auth/login', { email, password })),

  /**
   * 探活：503 也是有效结果（Milvus 挂了但 8002 还活着），所以不走 unwrap，
   * 直接把状态码和 body 一起交给调用方判断。
   */
  health: async (): Promise<HealthProbe> => {
    const resp = await http.get<RagResponse<HealthInfo>>('/health', {
      timeout: 8000,
      validateStatus: () => true,
    })
    const body = resp.data
    return {
      reachable: true,
      httpStatus: resp.status,
      data: (body?.data as HealthInfo | undefined) ?? null,
      message: body?.message || body?.error?.message || '',
    }
  },

  // ---- 知识库 ----
  getCollection: (id: string) => unwrap<CollectionItem>(http.get(`${PREFIX}/collections/${id}`)),

  listCollections: (params: {
    keyword?: string
    companionId?: string
    page?: number
    pageSize?: number
  }) => unwrap<PageResult<CollectionItem>>(http.get(`${PREFIX}/collections`, { params })),

  /** 分页遍历取全量（后端 pageSize 上限 100，下拉框不能只拉一页）。 */
  async listAllCollections(): Promise<CollectionItem[]> {
    const pageSize = 100
    const first = await api.listCollections({ page: 1, pageSize })
    const items = [...first.items]
    const total = first.total ?? items.length
    let page = 1
    while (items.length < total && page < 50) {
      page += 1
      const next = await api.listCollections({ page, pageSize })
      if (!next.items.length) break
      items.push(...next.items)
    }
    return items
  },

  createCollection: (payload: CollectionPayload) =>
    unwrap<CollectionItem>(http.post(`${PREFIX}/collections`, payload)),

  updateCollection: (id: string, payload: Partial<CollectionPayload>) =>
    unwrap<CollectionItem>(http.put(`${PREFIX}/collections/${id}`, payload)),

  deleteCollection: (id: string) => unwrap<{ id: string }>(http.delete(`${PREFIX}/collections/${id}`)),

  // ---- 文档 ----
  listDocuments: (collectionId: string, params?: { status?: string }) =>
    unwrap<PageResult<DocumentItem>>(
      http.get(`${PREFIX}/collections/${collectionId}/documents`, { params }),
    ),

  /** 文档详情；withChunks=true 时附带切片列表与原始正文。 */
  getDocument: (docId: string, withChunks = false) =>
    unwrap<DocumentDetail>(
      http.get(`${PREFIX}/documents/${docId}`, { params: { withChunks } }),
    ),

  uploadDocuments: (collectionId: string, files: File[], onProgress?: (percent: number) => void) => {
    const formData = new FormData()
    for (const file of files) formData.append('files', file)
    return unwrap<UploadResultItem[]>(
      http.post(`${PREFIX}/collections/${collectionId}/documents/upload`, formData, {
        timeout: 180000,
        onUploadProgress: (event) => {
          if (!onProgress) return
          const total = event.total || 0
          if (total > 0) onProgress(Math.round((event.loaded / total) * 100))
        },
      }),
    )
  },

  createManualDocument: (
    collectionId: string,
    payload: { title: string; content: string; companionId?: string },
  ) =>
    unwrap<{ documentId: string; taskId: string; title: string }>(
      http.post(`${PREFIX}/collections/${collectionId}/documents/manual`, payload),
    ),

  /** 仅 sourceType=manual 可编辑，保存后后端会重建切片与向量。 */
  updateDocument: (docId: string, payload: { title?: string; content?: string }) =>
    unwrap<{ documentId: string; taskId: string }>(http.put(`${PREFIX}/documents/${docId}`, payload)),

  reindexDocument: (docId: string) =>
    unwrap<{ documentId: string; taskId: string }>(http.post(`${PREFIX}/documents/${docId}/reindex`)),

  deleteDocument: (docId: string) => unwrap<{ id: string }>(http.delete(`${PREFIX}/documents/${docId}`)),

  // ---- 异步任务 ----
  getTask: (taskId: string) => unwrap<TaskStatus>(http.get(`${PREFIX}/tasks/${taskId}`)),

  // ---- 角色（只读主库）----
  listCompanions: () => unwrap<{ items: CompanionItem[] }>(http.get(`${PREFIX}/companions`)),

  // ---- 检索（服务间鉴权，不是 JWT）----
  retrieve: (payload: RetrievePayload) =>
    unwrap<RetrieveResult>(http.post(`${PREFIX}/retrieve`, payload, retrieveConfig)),
}