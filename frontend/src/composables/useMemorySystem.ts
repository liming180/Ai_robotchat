import { ref, computed } from 'vue'
import { useMemoryStore, MEMORY_CATEGORIES } from '@/stores/memory'
import type { Memory, MemoryCategory, MemoryType } from '@/types'

export function useMemorySystem() {
  const memoryStore = useMemoryStore()

  const memories = computed<Memory[]>(() => memoryStore.memories)
  const selectedCategory = ref<string>('all')
  const searchQuery = ref<string>('')
  const showForm = ref(false)
  /** 记忆编辑/删除已开放（T-5，任务十） */
  const canEdit = true
  const saving = ref(false)
  const saveError = ref('')

  const newMemory = ref<{ type: MemoryType; content: string }>({ type: 'preference', content: '' })
  /** 正在编辑的记录 id；为空表示新增模式 */
  const editingId = ref('')
  /** 待删除的记录；非 null 时删除确认框可见 */
  const deleteTarget = ref<Memory | null>(null)
  const deleting = ref(false)
  const deleteError = ref('')

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
    editingId.value = ''
    newMemory.value = { type: 'preference', content: '' }
    saveError.value = ''
    showForm.value = true
  }

  /** 打开编辑表单，回填当前记录 */
  const openEditForm = (memory: Memory) => {
    editingId.value = memory.id
    newMemory.value = { type: memory.type, content: memory.content }
    saveError.value = ''
    showForm.value = true
  }

  const cancelForm = () => {
    showForm.value = false
    editingId.value = ''
    saveError.value = ''
    newMemory.value = { type: 'preference', content: '' }
  }

  /** 保存记忆：新增与编辑共用同一表单，按 editingId 分支 */
  const saveMemory = async () => {
    if (!newMemory.value.content.trim() || saving.value) return
    saving.value = true
    saveError.value = ''
    const payload = {
      type: newMemory.value.type,
      content: newMemory.value.content.trim(),
    }
    try {
      if (editingId.value) {
        await memoryStore.updateMemory(editingId.value, payload)
      } else {
        await memoryStore.addMemory(payload)
      }
      cancelForm()
    } catch (e) {
      saveError.value = `${editingId.value ? '保存' : '新增'}失败：${(e as Error).message}`
    } finally {
      saving.value = false
    }
  }

  // ---------- 删除 ----------
  const openDeleteDialog = (memory: Memory) => {
    deleteTarget.value = memory
    deleteError.value = ''
  }

  const closeDeleteDialog = () => {
    if (deleting.value) return
    deleteTarget.value = null
    deleteError.value = ''
  }

  const confirmDelete = async () => {
    if (!deleteTarget.value || deleting.value) return
    deleting.value = true
    deleteError.value = ''
    try {
      await memoryStore.deleteMemory(deleteTarget.value.id)
      // 删的正好是编辑中的那条，顺手关表单，避免保存到已删除的记录
      if (editingId.value && editingId.value === deleteTarget.value.id) cancelForm()
      deleteTarget.value = null
    } catch (e) {
      deleteError.value = `删除失败：${(e as Error).message}`
    } finally {
      deleting.value = false
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
    editingId,
    deleteTarget,
    deleting,
    deleteError,
    memoryCategories,
    loading: computed(() => memoryStore.loading),
    error: computed(() => memoryStore.error),
    fromCache: computed(() => memoryStore.fromCache),
    filteredMemories,
    getMemoryCount,
    load,
    openAddForm,
    openEditForm,
    cancelForm,
    saveMemory,
    openDeleteDialog,
    closeDeleteDialog,
    confirmDelete,
    searchMemories,
    getPersonalizedPrompt,
  }
}
