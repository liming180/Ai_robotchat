/**
 * RAG 后端（8002）统一 API 层。
 * 响应包装 {success, message, data, error, timestamp}，按 success 判断成败（不要按 code）。
 * 登录转发返回 Java 的 AuthResponse：{accessToken, refreshToken, tokenType, user}。
 */
import axios from 'axios'
import type { AxiosInstance } from 'axios'

const BASE_URL = import.meta.env.VITE_RAG_API_BASE_URL || 'http://localhost:8002'
const PREFIX = '/api/v1/kb'
const TOKEN_KEY = 'rag_access_token'

export interface RagResponse<T = any> {
  success: boolean
  message?: string | null
  data: T
  error?: { code?: string; message?: string; details?: unknown } | null
  timestamp?: string
}

export interface AuthData {
  accessToken: string
  refreshToken: string
  tokenType: string
  user: { id: string; email: string; name: string; avatar?: string | null }
}

export interface CollectionItem {
  id: string
  name: string
  description?: string | null
  companionId?: string | null
  parserConfig?: Record<string, unknown> | null
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

export interface RetrieveResult {
  chunks: RetrievedChunk[]
  elapsedMs: number
  searchedCollections: string[]
}

export function getToken(): string {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    // 401：token 过期/无效 → 清凭证并回登录页
    if (error?.response?.status === 401) {
      clearToken()
      if (!location.pathname.startsWith('/login')) location.href = '/login'
    }
    return Promise.reject(error)
  },
)

async function unwrap<T>(promise: Promise<{ data: RagResponse<T> }>): Promise<T> {
  const resp = await promise
  const body = resp.data
  if (!body.success) {
    throw new Error(body.error?.message || body.message || '请求失败')
  }
  return body.data
}

export const api = {
  // ---- 登录（转发 Java 8081）----
  login: (email: string, password: string) =>
    unwrap<AuthData>(http.post('/api/v1/auth/login', { email, password })),

  // ---- 知识库 ----
  getCollection: (id: string) => unwrap<CollectionItem>(http.get(`${PREFIX}/collections/${id}`)),
  listCollections: (params: {
    keyword?: string
    companionId?: string
    page?: number
    pageSize?: number
  }) =>
    unwrap<{ items: CollectionItem[]; total: number }>(
      http.get(`${PREFIX}/collections`, { params }),
    ),
  createCollection: (payload: { name: string; description?: string; companionId?: string }) =>
    unwrap<CollectionItem>(http.post(`${PREFIX}/collections`, payload)),
  updateCollection: (id: string, payload: { name?: string; description?: string; companionId?: string }) =>
    unwrap(http.put(`${PREFIX}/collections/${id}`, payload)),
  deleteCollection: (id: string) => unwrap(http.delete(`${PREFIX}/collections/${id}`)),

  // ---- 文档 ----
  listDocuments: (collectionId: string, params?: { status?: string }) =>
    unwrap<{ items: DocumentItem[]; total?: number }>(
      http.get(`${PREFIX}/collections/${collectionId}/documents`, { params }),
    ),
  uploadDocuments: (collectionId: string, files: File[]) => {
    const formData = new FormData()
    for (const file of files) formData.append('files', file)
    return unwrap(http.post(`${PREFIX}/collections/${collectionId}/documents/upload`, formData))
  },
  createManualDocument: (collectionId: string, payload: { title: string; content: string }) =>
    unwrap(http.post(`${PREFIX}/collections/${collectionId}/documents/manual`, payload)),
  reindexDocument: (docId: string) => unwrap(http.post(`${PREFIX}/documents/${docId}/reindex`)),
  deleteDocument: (docId: string) => unwrap(http.delete(`${PREFIX}/documents/${docId}`)),

  // ---- 异步任务 ----
  getTask: (taskId: string) => unwrap<TaskStatus>(http.get(`${PREFIX}/tasks/${taskId}`)),

  // ---- 角色（只读主库）----
  listCompanions: () => unwrap<{ items: CompanionItem[] }>(http.get(`${PREFIX}/companions`)),

  // ---- 检索 ----
  retrieve: (payload: {
    query: string
    companionId?: string
    collectionIds?: string[]
    topK?: number
    scoreThreshold?: number
  }) => unwrap<RetrieveResult>(http.post(`${PREFIX}/retrieve`, payload)),
}
