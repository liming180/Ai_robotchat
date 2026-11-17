/**
 * useToast —— 轻提示队列
 *
 * 设计要点：
 * - 队列是模块级单例：任何组件 import 这个文件都能推提示，不依赖 provide/inject。
 * - ToastStack.vue 只负责渲染，从这个模块读 items、调 remove。
 * - 定时器统一在模块内管理，组件卸载不会导致提示卡死。
 *
 * 用法：
 *   import { useToast } from '@/composables/useToast'
 *   const toast = useToast()
 *   toast.success('已保存')
 *   toast.error('保存失败，请重试')
 */
import { reactive } from 'vue'

export type ToastKind = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  kind: ToastKind
  message: string
  /** 毫秒；0 表示不自动关闭 */
  duration: number
}

/** 全局共享队列（模块级单例） */
export const toastItems = reactive<ToastItem[]>([])

let seed = 0
const timers = new Map<number, ReturnType<typeof setTimeout>>()

/** 同时最多显示 4 条，超出丢弃最旧的 */
const MAX_VISIBLE = 4

export const dismissToast = (id: number) => {
  const index = toastItems.findIndex((t) => t.id === id)
  if (index >= 0) toastItems.splice(index, 1)

  const timer = timers.get(id)
  if (timer) {
    clearTimeout(timer)
    timers.delete(id)
  }
}

const push = (kind: ToastKind, message: string, duration = 3200) => {
  const id = ++seed
  toastItems.push({ id, kind, message, duration })

  while (toastItems.length > MAX_VISIBLE) {
    const oldest = toastItems[0]
    if (!oldest) break
    dismissToast(oldest.id)
  }

  if (duration > 0) {
    timers.set(
      id,
      setTimeout(() => dismissToast(id), duration),
    )
  }

  return id
}

export function useToast() {
  return {
    success: (message: string, duration?: number) => push('success', message, duration),
    error: (message: string, duration?: number) => push('error', message, duration),
    info: (message: string, duration?: number) => push('info', message, duration),
    dismiss: dismissToast,
  }
}
