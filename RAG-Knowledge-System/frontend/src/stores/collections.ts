import { defineStore } from 'pinia'

import { api } from '@/lib/api'
import type { CompanionItem, HealthProbe } from '@/lib/api'

/**
 * 知识库 / 角色 / 后端健康状态的共享数据。
 *
 * 为什么集中管理：
 * - 角色下拉在列表页、详情页、检索页都要用，逐页拉一次等于三次请求；
 * - 知识库全量下拉必须分页遍历（后端 pageSize 上限 100），逐页写会重复实现；
 * - 列表页写入、详情页读取，返回列表时不会看到过期计数。
 */
export const useCollectionStore = defineStore('collections', {
  state: () => ({
    companions: [] as CompanionItem[],
    companionsLoaded: false,
    /** 最近一次 /health 结果（含 503 场景，见 api.HealthProbe） */
    health: null as HealthProbe | null,
    healthError: '' as string,
    healthChecking: false,
    /** 全量知识库（下拉 / 概览用），分页遍历后缓存 */
    all: [] as { id: string; name: string }[],
    allLoaded: false,
    /** 最近一次详情页读到的元信息，供面包屑与头部摘要复用 */
    currentMeta: null as Record<string, unknown> | null,
  }),

  getters: {
    companionName: (state) => (id?: string | null) => {
      if (!id) return '未绑定角色'
      return state.companions.find((c) => c.id === id)?.name || id
    },
    /** 8002 进程活着（503 也算活着） */
    backendOnline: (state) => !!state.health?.reachable,
    /** 向量库可用：chroma 回退时为 disabled，同样算可用 */
    vectorReady: (state) => {
      const m = state.health?.data?.milvus
      return m === 'connected' || m === 'disabled'
    },
    milvusDown: (state) => state.health?.data?.milvus === 'unavailable',
  },

  actions: {
    async loadCompanions(force = false) {
      if (this.companionsLoaded && !force) return this.companions
      try {
        const data = await api.listCompanions()
        this.companions = data.items || []
        this.companionsLoaded = true
      } catch {
        // 主库不可用时角色下拉留空，不阻塞页面
        this.companionsLoaded = true
      }
      return this.companions
    },

    async loadAllCollections(force = false) {
      if (this.allLoaded && !force) return this.all
      try {
        const items = await api.listAllCollections()
        this.all = items.map((c) => ({ id: c.id, name: c.name }))
        this.allLoaded = true
      } catch {
        this.allLoaded = true
      }
      return this.all
    },

    async ping() {
      this.healthChecking = true
      try {
        this.health = await api.health()
        // 503 时后端仍然给了 message（向量库不可用…），保留下来做提示
        this.healthError = this.health.httpStatus === 200 ? '' : this.health.message
      } catch (e) {
        this.health = null
        this.healthError = e instanceof Error ? e.message : '8002 无响应'
      } finally {
        this.healthChecking = false
      }
      return this.health
    },

    invalidate() {
      this.allLoaded = false
      this.all = []
    },
  },
})