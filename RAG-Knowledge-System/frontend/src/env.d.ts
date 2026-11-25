/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** RAG 后端（8002）地址 */
  readonly VITE_RAG_API_BASE_URL: string
  /** 服务间检索密钥：与 backend/.env 的 SERVICE_TOKEN 同值，仅 /retrieve 使用 */
  readonly VITE_RAG_SERVICE_TOKEN: string
  /** 仅开发环境：无可用账号口令时注入的联调 JWT（生产构建不读取） */
  readonly VITE_DEV_TOKEN?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

// 不需要 `declare module '*.vue'` 兜底：类型检查走 vue-tsc（`npm run check`），
// 它会自己解析单文件组件的类型；加 shim 反而退化成 DefineComponent<{}, {}, any>，
// 让 props/emit 的检查全部失效。