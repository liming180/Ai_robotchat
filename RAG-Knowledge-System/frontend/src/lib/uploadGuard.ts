/**
 * 上传前置校验。
 *
 * 为什么必须在前端拦：后端 upload_documents 在循环里逐个文件 create + 提交任务，
 * 遇到非法文件直接 raise 400 —— 但因前面的文件已经落盘并提交入库任务，
 * 前端只看到「上传失败」，库里却多出几个文档（半成功脏数据）。
 * 所以要在提交前排掉非法文件，只把合法文件交给后端。
 */

export const ALLOWED_EXTENSIONS = ['json', 'md', 'txt'] as const
export const MAX_FILE_SIZE_MB = 20
const MAX_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

export interface RejectedFile {
  name: string
  size: number
  reason: string
}

export interface GuardResult {
  accepted: File[]
  rejected: RejectedFile[]
}

export function extensionOf(fileName: string): string {
  const idx = fileName.lastIndexOf('.')
  if (idx < 0) return ''
  return fileName.slice(idx + 1).toLowerCase()
}

export function guardFiles(files: File[]): GuardResult {
  const accepted: File[] = []
  const rejected: RejectedFile[] = []

  for (const file of files) {
    const ext = extensionOf(file.name)
    if (!ext) {
      rejected.push({ name: file.name, size: file.size, reason: '没有扩展名，无法判断格式' })
      continue
    }
    if (!ALLOWED_EXTENSIONS.includes(ext as (typeof ALLOWED_EXTENSIONS)[number])) {
      rejected.push({
        name: file.name,
        size: file.size,
        reason: `格式不支持（.${ext}），仅支持 ${ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(' / ')}`,
      })
      continue
    }
    if (file.size === 0) {
      rejected.push({ name: file.name, size: 0, reason: '文件为空' })
      continue
    }
    if (file.size > MAX_BYTES) {
      rejected.push({
        name: file.name,
        size: file.size,
        reason: `超过单文件上限 ${MAX_FILE_SIZE_MB}MB`,
      })
      continue
    }
    accepted.push(file)
  }

  return { accepted, rejected }
}

export const ACCEPT_ATTR = ALLOWED_EXTENSIONS.map((e) => `.${e}`).join(',')