import { ref, computed } from 'vue'
import { useMemoryStore, MEMORY_CATEGORIES } from '@/stores/memory'
import type { Memory, MemoryCategory, MemoryType } from '@/types'

export function useMemorySystem() {
  const memoryStore = useMemoryStore()

  const memories = computed<Memory[]>(() => memoryStore.memories)
  const selectedCategory = ref<string>('all')
  const searchQuery = ref<string>('')
  const showForm = ref(false)
  const editingId = ref<string | null>(null)
  const newMemory = ref<{ type: MemoryType; content: string }>({ type: 'preference', content: '' })

  const memoryCategories: MemoryCategory[] = MEMORY_CATEGORIES

  const filteredMemories = computed(() => {
    let list = selectedCategory.value === 'all'
      ? memories.value
      : memories.value.filter(m => m.type === selectedCategory.value)
    if (searchQuery.value.trim()) {
      const q = searchQuery.value.toLowerCase()
      list = list.filter(m =>
        m.content.toLowerCase().includes(q) ||
        m.type.toLowerCase().includes(q)
      )
    }
    return list
  })

  const getMemoryCount = (categoryId: string) =>
    categoryId === 'all'
      ? memories.value.length
      : memoryStore.getCountByCategory(categoryId as MemoryType)

  const openAddForm = () => {
    editingId.value = null
    newMemory.value = { type: 'preference', content: '' }
    showForm.value = true
  }

  const openEditForm = (memory: Memory) => {
    editingId.value = memory.id
    newMemory.value = { type: memory.type, content: memory.content }
    showForm.value = true
  }

  const saveMemory = () => {
    if (!newMemory.value.content.trim()) return
    if (editingId.value) {
      memoryStore.updateMemory(editingId.value, {
        type: newMemory.value.type,
        content: newMemory.value.content.trim(),
      })
    } else {
      memoryStore.addMemory({
        type: newMemory.value.type,
        content: newMemory.value.content.trim(),
      })
    }
    showForm.value = false
    editingId.value = null
  }

  const deleteMemory = (id: string) => {
    memoryStore.deleteMemory(id)
  }

  const searchMemories = (query: string) => memoryStore.searchMemories(query)

  const getPersonalizedPrompt = (companionId?: string) =>
    memoryStore.getPersonalizedPrompt(companionId)

  return {
    memories,
    selectedCategory,
    searchQuery,
    showForm,
    editingId,
    newMemory,
    memoryCategories,
    filteredMemories,
    getMemoryCount,
    openAddForm,
    openEditForm,
    saveMemory,
    deleteMemory,
    searchMemories,
    getPersonalizedPrompt,
  }
}
