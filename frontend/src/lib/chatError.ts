/**
 * 聊天错误文案分级（P2-5 动作 2）
 *
 * 背景：2026-11-24 的 401 故障中，前端把鉴权失败统一渲染成
 * 「请检查网络连接」，排查时被误导。这里把 HTTP 状态码、网络故障、
 * 解析失败拆成不同文案，401/403/429 直接给出可操作的方向。
 *
 * 约定：
 * - 状态码从 useStreamingChat.ts 抛出的 `... (HTTP 401)` 中提取，
 *   该文件已带状态码，本模块不改动它。
 * - 本文件零依赖（不 import Vue / api），便于用 Node 直接跑回归用例
 *   （frontend/tests/chat-error.test.mjs）。
 */

const HTTP_STATUS_PATTERN = /HTTP\s+(\d{3})/i

/** fetch 抛出的网络层错误（TypeError）在不同浏览器/Node 下措辞不同 */
const NETWORK_PATTERN = /failed to fetch|networkerror|load failed|network request failed|fetch failed/i

/** 兜底文案：无法归类的错误 */
const FALLBACK_MESSAGE = 'AI 服务暂时不可用，请稍后再试。'

/** 从错误信息里提取 HTTP 状态码，没有则返回 undefined */
export function extractHttpStatus(message: string): number | undefined {
  const matched = HTTP_STATUS_PATTERN.exec(message)
  if (!matched) return undefined
  const status = Number(matched[1])
  return Number.isFinite(status) ? status : undefined
}

/** 按状态码生成带前缀的文案（prefix 用于区分聊天服务与建议服务） */
function describeStatus(prefix: string, status: number): string {
  if (status === 401) {
    return `${prefix}鉴权失败（401）：服务间 token 不一致，请重启前端/后端或核对 SERVICE_TOKEN。`
  }
  if (status === 403) {
    return `${prefix}拒绝访问（403），请确认服务间权限配置。`
  }
  if (status === 404) {
    return `${prefix}接口不存在（404），请确认服务版本与端口。`
  }
  if (status === 429) {
    return '请求过于频繁（429），请稍等片刻再重试。'
  }
  if (status >= 500) {
    return `${prefix}内部错误（HTTP ${status}），请稍后重试。`
  }
  return `${prefix}响应异常（HTTP ${status}），请重试。`
}

/**
 * 把聊天链路上的异常翻译成用户可读文案。
 *
 * 分支顺序：状态码 → 网络层 → 解析/空内容 → 兜底。
 * 401 特意点名 SERVICE_TOKEN：三处 token 必须同值（见 CLAUDE.md）。
 */
export function describeChatError(error: unknown): string {
  if (!(error instanceof Error)) return FALLBACK_MESSAGE

  const message = error.message
  const isSuggestions = message.includes('建议服务响应异常')
  const status = extractHttpStatus(message)
  if (status !== undefined) {
    return describeStatus(isSuggestions ? '建议服务' : 'AI 服务', status)
  }

  if (error instanceof TypeError || NETWORK_PATTERN.test(message)) {
    return '连不上 AI 服务，请确认后端服务已启动。'
  }

  if (message.includes('AI 流式响应解析失败')) {
    return 'AI 响应解析失败，请重试。'
  }
  if (message.includes('AI 未生成有效内容')) {
    return 'AI 未生成有效内容，请尝试重新发送消息。'
  }
  if (message.includes('AI 未返回有效的建议数据')) {
    return 'AI 建议数据异常，请重试。'
  }

  return FALLBACK_MESSAGE
}
