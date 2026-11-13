import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Companion } from '@/types'
import { javaFetch } from '@/lib/api'

/**
 * 伴侣数据源 = Java（MySQL）。
 * localStorage 只做「拉取失败时的只读缓存」，不再是事实源。
 */

const CACHE_KEY = 'ai_companion_catalog'

/** Java `CompanionResponse`：tags 是逗号分隔字符串，createdAt 是 ISO 串 */
interface CompanionDto {
  id: string
  name: string
  avatar?: string | null
  description?: string | null
  category?: string | null
  personality?: string | null
  systemPrompt?: string | null
  isFavorite?: boolean | null
  intimacy?: number | null
  tags?: string | null
  createdAt?: string | null
}

export interface CreateCompanionPayload {
  name: string
  avatar?: string
  description?: string
  category?: string
  personality?: string
  systemPrompt?: string
  tags?: string[]
}

const dtoToCompanion = (dto: CompanionDto): Companion => ({
  id: dto.id,
  name: dto.name,
  avatar: dto.avatar || '',
  description: dto.description || '',
  category: dto.category || '',
  personality: dto.personality || '',
  systemPrompt: dto.systemPrompt || '',
  isFavorite: Boolean(dto.isFavorite),
  intimacy: dto.intimacy ?? 0,
  createdAt: dto.createdAt ? new Date(dto.createdAt) : new Date(),
  tags: (dto.tags || '')
    .split(',')
    .map(t => t.trim())
    .filter(Boolean),
})

const companionToPayload = (c: Companion | CreateCompanionPayload) => ({
  name: c.name,
  avatar: c.avatar,
  description: c.description,
  category: c.category,
  personality: c.personality,
  systemPrompt: c.systemPrompt,
  tags: c.tags.join(','),
})

/** 生成参数：拉取时带筛选条件，收藏/分类过滤交给后端（CompanionServiceImpl 已支持） */
interface ListParams {
  category?: string
  search?: string
  favorite?: boolean
}

export const useCompanionStore = defineStore('companion', () => {
  const companions = ref<Companion[]>([])
  const loading = ref(false)
  /** 最近一次拉取失败的原因，页面据此提示；成功时清空 */
  const error = ref('')
  /** true 表示当前展示的是 localStorage 缓存（离线兜底） */
  const fromCache = ref(false)

  const allCompanions = computed(() => companions.value)
  const favoriteCompanions = computed(() => companions.value.filter(c => c.isFavorite))

  const filterByCategory = (category: string) => {
    if (category === '全部') return companions.value
    return companions.value.filter(c => c.category === category)
  }

  const searchCompanions = (query: string) => {
    const lower = query.toLowerCase()
    return companions.value.filter(c =>
      c.name.toLowerCase().includes(lower)
      || c.description.toLowerCase().includes(lower)
      || c.tags.some(tag => tag.toLowerCase().includes(lower))
    )
  }

  const getCompanionById = (id: string) => companions.value.find(c => c.id === id)

  /** 分类标签：由后端返回的数据去重生成，避免硬编码与真实数据（Java preset-1~4）对不上 */
  const categories = computed(() => {
    const seen: string[] = []
    for (const c of companions.value) {
      if (c.category && !seen.includes(c.category)) seen.push(c.category)
    }
    return ['全部', ...seen]
  })

  const readCache = (): Companion[] => {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return []
    try {
      const list = JSON.parse(raw) as CompanionDto[]
      return Array.isArray(list) ? list.map(dtoToCompanion) : []
    } catch {
      localStorage.removeItem(CACHE_KEY)
      return []
    }
  }

  const writeCache = (list: Companion[]) => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(list.map(c => ({
        ...c,
        createdAt: c.createdAt.toISOString(),
        tags: c.tags.join(','),
      }))))
    } catch {
      // 缓存失败不影响主流程（图片 URL 很短，正常不会超限）
    }
  }

  const applyList = (list: Companion[]) => {
    companions.value = list
    writeCache(list)
  }

  /** 拉取伴侣列表；失败时回落到只读缓存并设置 error 文案 */
  async function loadCompanions(params: ListParams = {}): Promise<void> {
    loading.value = true
    try {
      const query = new URLSearchParams()
      if (params.category) query.set('category', params.category)
      if (params.search) query.set('search', params.search)
      if (params.favorite !== undefined) query.set('favorite', String(params.favorite))
      const suffix = query.toString() ? `?${query.toString()}` : ''

      const list = await javaFetch<CompanionDto[]>(`/api/v1/companions${suffix}`)
      applyList((list || []).map(dtoToCompanion))
      error.value = ''
      fromCache.value = false
    } catch (e) {
      const cached = readCache()
      if (cached.length) {
        companions.value = cached
        fromCache.value = true
        error.value = `伴侣列表加载失败，正在显示离线缓存：${(e as Error).message}`
      } else {
        error.value = `伴侣列表加载失败：${(e as Error).message}`
      }
    } finally {
      loading.value = false
    }
  }

  /** 直连 /chat/:id 或 /settings/:id 时，列表可能尚未加载，单独补一次详情 */
  async function loadCompanion(id: string): Promise<Companion | undefined> {
    try {
      const dto = await javaFetch<CompanionDto>(`/api/v1/companions/${id}`)
      const companion = dtoToCompanion(dto)
      const index = companions.value.findIndex(c => c.id === id)
      if (index !== -1) companions.value[index] = companion
      else companions.value.push(companion)
      return companion
    } catch (e) {
      error.value = `伴侣详情加载失败：${(e as Error).message}`
      return getCompanionById(id) ?? readCache().find(c => c.id === id)
    }
  }

  async function toggleFavorite(id: string): Promise<void> {
    const companion = getCompanionById(id)
    if (!companion) return
    const data = await javaFetch<{ isFavorite: boolean }>(`/api/v1/companions/${id}/favorite`, {
      method: 'PATCH',
    })
    companion.isFavorite = Boolean(data?.isFavorite)
    writeCache(companions.value)
  }

  async function increaseIntimacy(id: string, amount = 2): Promise<void> {
    const companion = getCompanionById(id)
    if (!companion) return
    const data = await javaFetch<{ intimacy: number }>(`/api/v1/companions/${id}/intimacy`, {
      method: 'PATCH',
      body: { amount },
    })
    companion.intimacy = data?.intimacy ?? companion.intimacy + amount
    writeCache(companions.value)
  }

  async function createCompanion(payload: CreateCompanionPayload): Promise<Companion> {
    const dto = await javaFetch<CompanionDto>('/api/v1/companions', {
      method: 'POST',
      body: companionToPayload({ ...payload, tags: payload.tags ?? [] }),
    })
    const companion = dtoToCompanion(dto)
    companions.value.unshift(companion)
    writeCache(companions.value)
    return companion
  }

  async function updateCompanion(id: string, updates: Partial<Companion>): Promise<Companion> {
    const current = getCompanionById(id)
    const merged = { ...(current ?? ({} as Companion)), ...updates } as Companion
    const dto = await javaFetch<CompanionDto>(`/api/v1/companions/${id}`, {
      method: 'PUT',
      body: companionToPayload(merged),
    })
    const companion = dtoToCompanion(dto)
    const index = companions.value.findIndex(c => c.id === id)
    if (index !== -1) companions.value[index] = companion
    writeCache(companions.value)
    return companion
  }

  return {
    companions,
    allCompanions,
    favoriteCompanions,
    categories,
    loading,
    error,
    fromCache,
    filterByCategory,
    searchCompanions,
    getCompanionById,
    loadCompanions,
    loadCompanion,
    toggleFavorite,
    increaseIntimacy,
    createCompanion,
    updateCompanion,
  }
})
