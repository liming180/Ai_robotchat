import { defineStore } from 'pinia'

import { api, apiErrorMessage } from '@/lib/api'
import { isTerminal } from '@/lib/format'
import type { TaskStatus } from '@/lib/api'

interface TaskRecord extends TaskStatus {
  updatedAt: number
  /** 轮询本身失败（网络/鉴权），与任务 failed 区分 */
  pollError?: string
}

/**
 * 全局任务轮询表。
 *
 * 旧实现只把 taskId 存在详情页的局部变量里：一次刷新页面，进度条就永久停住，
 * 文档会一直显示上传时的旧状态。改成全局表后：
 * - 进详情页时按 document.taskId + 非终态 status 自动恢复轮询（修复刷新丢失）；
 * - 同一任务在任意页面都能读到最新进度；
 * - 所有非终态任务共用一条 2s 定时器，不随页面数量线性膨胀。
 */
export const useTaskStore = defineStore('tasks', {
  state: () => ({
    records: {} as Record<string, TaskRecord>,
    timer: 0 as number,
    /** 最近一次有任务进入终态的时间，供页面 watch 后刷新列表 */
    lastSettledAt: 0 as number,
  }),

  getters: {
    recordOf: (state) => (taskId?: string | null): TaskRecord | null => {
      if (!taskId) return null
      return state.records[taskId] || null
    },
    activeTaskIds(state): string[] {
      return Object.entries(state.records)
        .filter(([, r]) => !isTerminal(r.status))
        .map(([id]) => id)
    },
  },

  actions: {
    /** 登记任务并启动轮询（重复登记同一 id 无副作用）。 */
    watch(taskIds: (string | null | undefined)[]) {
      const ids = taskIds.filter((id): id is string => !!id)
      if (!ids.length) return
      for (const id of ids) {
        if (!this.records[id]) {
          this.records[id] = {
            taskId: id,
            documentId: '',
            status: 'pending',
            progress: 0,
            chunkCount: 0,
            errorMsg: null,
            updatedAt: Date.now(),
          }
        }
      }
      this.ensureTimer()
    },

    /** 详情页/文档列表恢复：文档非终态且带 taskId 时继续轮询。 */
    restoreFromDocuments(docs: { taskId?: string | null; status?: string; documentId?: string; id?: string; progress?: number; chunkCount?: number }[]) {
      const ids: string[] = []
      for (const d of docs) {
        if (!d.taskId || isTerminal(d.status)) continue
        const existed = this.records[d.taskId]
        if (!existed) {
          this.records[d.taskId] = {
            taskId: d.taskId,
            documentId: d.id || d.documentId || '',
            status: d.status || 'pending',
            progress: d.progress ?? 0,
            chunkCount: d.chunkCount ?? 0,
            errorMsg: null,
            updatedAt: Date.now(),
          }
        }
        ids.push(d.taskId)
      }
      this.ensureTimer()
      return ids
    },

    ensureTimer() {
      if (this.timer) return
      this.timer = window.setInterval(() => this.tick(), 2000)
      void this.tick()
    },

    stopTimer() {
      if (this.timer) {
        window.clearInterval(this.timer)
        this.timer = 0
      }
    },

    async tick() {
      const ids = this.activeTaskIds
      if (!ids.length) {
        this.stopTimer()
        return
      }
      await Promise.all(
        ids.map(async (id) => {
          const prev = this.records[id]
          if (!prev) return
          try {
            const data = await api.getTask(id)
            const settled = isTerminal(prev.status) === false && isTerminal(data.status)
            this.records[id] = { ...prev, ...data, updatedAt: Date.now(), pollError: '' }
            if (settled) this.lastSettledAt = Date.now()
          } catch (e) {
            // 403（归属校验/任务已删）与断网都停止轮询该任务，避免死循环刷 401
            this.records[id] = {
              ...prev,
              updatedAt: Date.now(),
              pollError: apiErrorMessage(e, '任务进度查询失败'),
            }
            this.stopTimer()
            this.startOrphanTimer()
          }
        }),
      )
      if (!this.activeTaskIds.length) this.stopTimer()
    },

    /** 单个任务出错后其余任务仍需继续，重建定时器时跳过出错的。 */
    startOrphanTimer() {
      if (this.timer) return
      const alive = Object.entries(this.records).filter(([, r]) => !isTerminal(r.status) && !r.pollError)
      if (!alive.length) return
      this.timer = window.setInterval(() => this.tick(), 2000)
    },
  },
})