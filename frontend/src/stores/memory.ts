import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Memory, MemoryCategory, MemoryType } from '@/types'
import { aiFetch } from '@/lib/api'
import { useUserStore } from '@/stores/user'

/**
 * 记忆数据归属 = Python AI 服务（SQLite `user_memories`，P0-6 决策）。
 * 本轮只做「列表 + 新增」：Python 端没有 update / delete 端点，编辑删除为二期。
 */

const CACHE_KEY = 'ai-memories'

export const MEMORY_CATEGORIES: MemoryCategory[] = [
  { id: 'preference', name: '偏好', icon: '❤️' },
  { id: 'habit', name: '习惯', icon: '📝' },
  { id: 'important_date', name: '重要日期', icon: '📅' },
  { id: 'milestone', name: '里程碑', icon: '🏆' },
]

/** Python `GET /api/v1/memory/{userId}` 的单条结构 */
interface MemoryDto {
  id: string | number
  userId: string
  type?: string | null
  keyword?: string | null
  content?: string | null
  createdAt?: string | null
}

const MEMORY_TYPES: MemoryType[] = ['preference', 'habit', 'important_date', 'milestone']

/** Python 的 memoryType 是自由字符串（LangChain 工具会写 fact 等），统一映射到前端的 4 个分类 */
const normalizeType = (type?: string | null): MemoryType => {
  const value = (type || '').trim()
  if (MEMORY_TYPES.includes(value as MemoryType)) return value as MemoryType
  if (value === 'fact' || value === 'factual' || !value) return 'preference'
  return 'preference'
}

const toMemory = (dto: MemoryDto): Memory => ({
  id: String(dto.id),
  type: normalizeType(dto.type),
  content: dto.content || '',
  createdAt: dto.createdAt ? new Date(dto.createdAt) : new Date(),
})

export const useMemoryStore = defineStore('memory', () => {
  const memories = ref<Memory[]>([])
  const loading = ref(false)
  const error = ref('')
  const fromCache = ref(false)

  const readCache = (): Memory[] => {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return []
    try {
      const list = JSON.parse(raw)
      return Array.isArray(list)
        ? list.map((m: any) => ({
            id: String(m.id),
            type: normalizeType(m.type),
            content: m.content || '',
            createdAt: new Date(m.createdAt ?? Date.now()),
          }))
        : []
    } catch {
      localStorage.removeItem(CACHE_KEY)
      return []
    }
  }

  const writeCache = () => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(memories.value.map(m => ({
        ...m,
        createdAt: m.createdAt.toISOString(),
      }))))
    } catch {
      // 缓存失败不影响主流程
    }
  }

  /** 当前登录用户（Java UUID）；未登录时为空，接口会被守卫拦在前面 */
  const currentUserId = () => useUserStore().userId

  async function loadMemories(keyword?: string): Promise<void> {
    const userId = currentUserId()
    if (!userId) {
      memories.value = []
      return
    }

    loading.value = true
    try {
      const suffix = keyword ? `?keyword=${encodeURIComponent(keyword)}` : ''
      const data = await aiFetch<{ memories?: MemoryDto[] }>(`/api/v1/memory/${userId}${suffix}`)
      memories.value = (data?.memories || []).map(toMemory)
      error.value = ''
      fromCache.value = false
      writeCache()
    } catch (e) {
      const cached = readCache()
      if (cached.length) {
        memories.value = cached
        fromCache.value = true
        error.value = `记忆加载失败，正在显示本地缓存：${(e as Error).message}`
      } else {
        error.value = `记忆加载失败：${(e as Error).message}`
      }
    } finally {
      loading.value = false
    }
  }

  /** 新增记忆：先写 Python，成功后插入本地列表；失败抛给调用方提示 */
  async function addMemory(data: Omit<Memory, 'id' | 'createdAt'>): Promise<Memory> {
    const userId = currentUserId()
    if (!userId) throw new Error('未登录，无法保存记忆')

    const content = data.content.trim()
    const keyword = content.length <= 20 ? content : `${content.slice(0, 20)}...`
    const dto = await aiFetch<MemoryDto>('/api/v1/memory', {
      method: 'POST',
      body: { userId, memoryType: data.type, keyword, content },
    })

    const memory = toMemory(dto)
    // Python 返回的 memoryType 可能被标准化，保留用户选择的分类更符合预期
    memory.type = data.type
    memories.value.unshift(memory)
    writeCache()
    return memory
  }

  /** 二期能力：Python 端无 update / delete 端点 */
  function updateMemory(): never {
    throw new Error('记忆编辑暂未开放（后端未提供更新接口）')
  }

  function deleteMemory(): never {
    throw new Error('记忆删除暂未开放（后端未提供删除接口）')
  }

  const getCountByCategory = (type: MemoryType) =>
    memories.value.filter(m => m.type === type).length

  const filterByCategory = (category: string) => {
    if (category === 'all') return memories.value
    return memories.value.filter(m => m.type === category)
  }

  const searchMemories = (query: string) => {
    const lower = query.toLowerCase()
    return memories.value.filter(m => m.content.toLowerCase().includes(lower))
  }

  // 将记忆拼成提示词片段；ChatPage 当前由 Python LangChain 工具注入记忆，本函数保留给后续使用
  const getPersonalizedPrompt = () => {
    if (!memories.value.length) return ''
    const grouped: Record<string, string[]> = {}
    for (const m of memories.value) {
      ;(grouped[m.type] = grouped[m.type] || []).push(m.content)
    }
    const parts: string[] = []
    for (const [type, items] of Object.entries(grouped)) {
      const cat = MEMORY_CATEGORIES.find(c => c.id === type)
      parts.push(`${cat?.name ?? type}：${items.join('、')}`)
    }
    return `你了解关于用户的这些信息——${parts.join('；')}。请在对话中自然地体现这份了解。`
  }

  const totalCount = computed(() => memories.value.length)

  return {
    memories,
    categories: MEMORY_CATEGORIES,
    loading,
    error,
    fromCache,
    totalCount,
    loadMemories,
    getCountByCategory,
    filterByCategory,
    searchMemories,
    addMemory,
    updateMemory,
    deleteMemory,
    getPersonalizedPrompt,
  }
})
