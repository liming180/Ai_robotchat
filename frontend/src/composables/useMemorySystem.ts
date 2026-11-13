import { ref, computed } from 'vue'
import { useMemoryStore, MEMORY_CATEGORIES } from '@/stores/memory'
import type { Memory, MemoryCategory, MemoryType } from '@/types'

export function useMemorySystem() {
  const memoryStore = useMemoryStore()

  const memories = computed<Memory[]>(() => memoryStore.memories)
  const selectedCategory = ref<string>('all')
  const searchQuery = ref<string>('')
  const showForm = ref(false)
  /** 本轮只支持新增：Python 端没有 update 端点，编辑入口不展示 */
  const canEdit = false
  const saving = ref(false)
  const saveError = ref('')

  const newMemory = ref<{ type: MemoryType; content: string }>({ type: 'preference', content: '' })

  const memoryCategories: MemoryCategory[] = MEMORY_CATEGORIES

  const filteredMemories = computed(() => {
    let list = selectedCategory.value === 'all'
      ? memories.value
      : memories.value.filter(m => m.type === selectedCategory.value)
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase()
      list = list.filter(m => m.content.toLowerCase().includes(q))
    }
    return list
  })

  const getMemoryCount = (categoryId: string) =>
    categoryId === 'all'
      ? memories.value.length
      : memoryStore.getCountByCategory(categoryId as MemoryType)

  const load = () => memoryStore.loadMemories()

  const openAddForm = () => {
    newMemory.value = { type: 'preference', content: '' }
    saveError.value = ''
    showForm.value = true
  }

  /** 新增记忆：写 Python 后端，失败时在表单内提示，不关闭表单 */
  const saveMemory = async () => {
    if (!newMemory.value.content.trim() || saving.value) return
    saving.value = true
    saveError.value = ''
    try {
      await memoryStore.addMemory({
        type: newMemory.value.type,
        content: newMemory.value.content.trim(),
      })
      showForm.value = false
      newMemory.value = { type: 'preference', content: '' }
    } catch (e) {
      saveError.value = `保存失败：${(e as Error).message}`
    } finally {
      saving.value = false
    }
  }

  const searchMemories = (query: string) => memoryStore.searchMemories(query)

  const getPersonalizedPrompt = () => memoryStore.getPersonalizedPrompt()

  return {
    memories,
    selectedCategory,
    searchQuery,
    showForm,
    canEdit,
    saving,
    saveError,
    newMemory,
    memoryCategories,
    loading: computed(() => memoryStore.loading),
    error: computed(() => memoryStore.error),
    fromCache: computed(() => memoryStore.fromCache),
    filteredMemories,
    getMemoryCount,
    load,
    openAddForm,
    saveMemory,
    searchMemories,
    getPersonalizedPrompt,
  }
}
