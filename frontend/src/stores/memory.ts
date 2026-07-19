import { defineStore } from 'pinia'
import { ref, computed, onMounted, watch } from 'vue'
import type { Memory, MemoryCategory, MemoryType } from '@/types'
import { isQuotaExceededError } from '@/lib/avatar'

const STORAGE_KEY = 'ai-memories'

export const MEMORY_CATEGORIES: MemoryCategory[] = [
  { id: 'preference', name: '偏好', icon: '❤️' },
  { id: 'habit', name: '习惯', icon: '📝' },
  { id: 'important_date', name: '重要日期', icon: '📅' },
  { id: 'milestone', name: '里程碑', icon: '🏆' },
]

const serialize = (m: Memory) => ({ ...m, createdAt: m.createdAt.toISOString() })
const deserialize = (d: any): Memory => ({ ...d, createdAt: new Date(d.createdAt) })

export const useMemoryStore = defineStore('memory', () => {
  const memories = ref<Memory[]>([])
  const persistError = ref<string>('')

  onMounted(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        memories.value = JSON.parse(saved).map(deserialize)
      } catch (error) {
        console.error('Failed to load memories:', error)
      }
    }
  })

  watch(memories, (newVal) => {
    try {
      persistError.value = ''
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newVal.map(serialize)))
    } catch (error) {
      if (isQuotaExceededError(error)) {
        persistError.value = '本地存储空间不足，记忆保存失败。请清理部分数据后重试。'
      } else {
        persistError.value = '记忆保存失败，请稍后重试。'
      }
      console.error('Failed to save memories:', error)
    }
  }, { deep: true })

  const getCountByCategory = (type: MemoryType) =>
    memories.value.filter(m => m.type === type).length

  const filterByCategory = (category: string) => {
    if (category === 'all') return memories.value
    return memories.value.filter(m => m.type === category)
  }

  const getByCompanion = (companionId: string) =>
    memories.value.filter(m => m.companionId === companionId)

  const searchMemories = (query: string) => {
    const lower = query.toLowerCase()
    return memories.value.filter(m =>
      m.content.toLowerCase().includes(lower) ||
      m.type.toLowerCase().includes(lower)
    )
  }

  const addMemory = (data: Omit<Memory, 'id' | 'createdAt'>) => {
    const memory: Memory = {
      ...data,
      id: Date.now().toString(),
      createdAt: new Date(),
    }
    memories.value.unshift(memory)
    return memory
  }

  const updateMemory = (id: string, updates: Partial<Memory>) => {
    const index = memories.value.findIndex(m => m.id === id)
    if (index !== -1) {
      memories.value[index] = { ...memories.value[index], ...updates }
    }
  }

  const deleteMemory = (id: string) => {
    memories.value = memories.value.filter(m => m.id !== id)
  }

  // 将记忆拼成提示词片段，供后续注入 systemPrompt
  const getPersonalizedPrompt = (companionId?: string) => {
    const list = companionId ? getByCompanion(companionId) : memories.value
    if (!list.length) return ''
    const grouped: Record<string, string[]> = {}
    for (const m of list) {
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
    persistError,
    totalCount,
    getCountByCategory,
    filterByCategory,
    getByCompanion,
    searchMemories,
    addMemory,
    updateMemory,
    deleteMemory,
    getPersonalizedPrompt,
  }
})
