/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Java 业务后端地址（端口 8080，见 .env.development） */
  readonly VITE_API_BASE_URL: string
  /** Python AI 服务地址（端口 5000，见 .env.development） */
  readonly VITE_AI_BASE_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
