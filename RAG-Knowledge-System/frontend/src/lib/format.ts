/**
 * 展示层格式化与状态口径。
 *
 * 状态取值来自后端 kb_document.status / kb_collection.status：
 * pending / parsing / chunking / embedding / completed / failed / active / disabled。
 */

export interface StatusMeta {
  label: string
  className: string
  pulse?: boolean
}

const STATUS_MAP: Record<string, StatusMeta> = {
  pending: {
    label: '排队中',
    className: 'border-neutral-600/40 bg-neutral-600/10 text-neutral-300',
  },
  parsing: {
    label: '解析中',
    className: 'border-sky-500/30 bg-sky-500/10 text-sky-300',
    pulse: true,
  },
  chunking: {
    label: '切片中',
    className: 'border-sky-500/30 bg-sky-500/10 text-sky-300',
    pulse: true,
  },
  embedding: {
    label: '向量化中',
    className: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
    pulse: true,
  },
  processing: {
    label: '处理中',
    className: 'border-amber-500/30 bg-amber-500/10 text-amber-300',
    pulse: true,
  },
  completed: {
    label: '已完成',
    className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  },
  active: {
    label: '启用中',
    className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300',
  },
  failed: {
    label: '失败',
    className: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
  },
  error: {
    label: '失败',
    className: 'border-rose-500/30 bg-rose-500/10 text-rose-300',
  },
  disabled: {
    label: '已停用',
    className: 'border-neutral-600/40 bg-neutral-700/30 text-neutral-400',
  },
}

export function statusMeta(status?: string | null): StatusMeta {
  return (
    STATUS_MAP[(status || '').toLowerCase()] || {
      label: status || '未知',
      className: 'border-neutral-600/40 bg-neutral-600/10 text-neutral-400',
    }
  )
}

export const TERMINAL_STATUSES = ['completed', 'failed', 'error'] as const

export function isTerminal(status?: string | null): boolean {
  return TERMINAL_STATUSES.includes((status || '') as (typeof TERMINAL_STATUSES)[number])
}

export function isFailed(status?: string | null): boolean {
  const s = (status || '').toLowerCase()
  return s === 'failed' || s === 'error'
}

/** 文档来源的中文标签。 */
export function sourceLabel(source?: string | null): string {
  if (source === 'manual') return '手动录入'
  if (source === 'file') return '文件上传'
  return source || '未知'
}

/** 检索分数尺度的可读说明（cosine / tei 是相似度，rrf 是名次融合分）。 */
export function scoreScaleMeta(scale?: string | null): { label: string; hint: string } {
  if (scale === 'rrf') {
    return {
      label: 'RRF 名次分',
      hint: 'hybrid 模式下为名次融合值（约 0.015–0.033），越大只代表排名越靠前，不能当相似度读，阈值参数同时被服务端忽略。',
    }
  }
  if (scale === 'tei') {
    return { label: 'TEI 精排分', hint: 'rerank 精排后的相关度分数，0–1 之间。' }
  }
  return { label: '余弦相似度', hint: 'Milvus COSINE 相似度，0–1 之间，越大越相关。' }
}

export function formatBytes(size?: number | null): string {
  if (size == null) return '—'
  if (size < 1024) return `${size} B`
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / 1024 / 1024).toFixed(2)} MB`
}

const pad = (n: number) => String(n).padStart(2, '0')

/** 2026-11-24T21:39:53 → 2026-11-24 21:39 */
export function formatDateTime(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export function formatDate(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${d.getMonth() + 1}-${pad(d.getDate())}`
}

/** 相对时间：刚刚 / 3 分钟前 / 2 小时前 / 5 天前 */
export function formatRelative(iso?: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const diff = Date.now() - d.getTime()
  if (diff < 60_000) return '刚刚'
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)} 分钟前`
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)} 小时前`
  if (diff < 30 * 86_400_000) return `${Math.floor(diff / 86_400_000)} 天前`
  return formatDateTime(iso)
}

export function truncate(text: string, max: number): string {
  if (text.length <= max) return text
  return `${text.slice(0, max)}…`
}

/** 数字千分位。 */
export function formatNumber(n?: number | null): string {
  if (n == null) return '0'
  return n.toLocaleString('zh-CN')
}