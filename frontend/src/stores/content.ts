import { defineStore } from 'pinia'
import { ref, onMounted, watch } from 'vue'
import type { SavedContent, SavedContentKind } from '@/types'
import { isQuotaExceededError } from '@/lib/avatar'

const STORAGE_KEY = 'ai-saved-content'

const todayStr = () => new Date().toISOString().slice(0, 10)

const serialize = (c: SavedContent) => ({ ...c, createdAt: c.createdAt.toISOString() })
const deserialize = (d: any): SavedContent => ({ ...d, createdAt: new Date(d.createdAt) })

export const useContentStore = defineStore('content', () => {
  const items = ref<SavedContent[]>([])
  const persistError = ref<string>('')

  onMounted(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        items.value = JSON.parse(saved).map(deserialize)
      } catch (error) {
        console.error('Failed to load saved content:', error)
      }
    }
  })

  watch(items, (newVal) => {
    try {
      persistError.value = ''
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newVal.map(serialize)))
    } catch (error) {
      if (isQuotaExceededError(error)) {
        persistError.value = '本地存储空间不足，内容保存失败。请清理部分数据后重试。'
      } else {
        persistError.value = '内容保存失败，请稍后重试。'
      }
      console.error('Failed to save content:', error)
    }
  }, { deep: true })

  const listByKind = (kind: SavedContentKind) =>
    items.value.filter(c => c.kind === kind)

  const getByDate = (kind: SavedContentKind, date: string) =>
    items.value.find(c => c.kind === kind && c.date === date)

  const save = (kind: SavedContentKind, title: string, content: string, date: string = todayStr()) => {
    const item: SavedContent = {
      id: `${kind}-${Date.now()}`,
      kind,
      date,
      title,
      content,
      createdAt: new Date(),
    }
    items.value.unshift(item)
    return item
  }

  const remove = (id: string) => {
    items.value = items.value.filter(c => c.id !== id)
  }

  return {
    items,
    persistError,
    listByKind,
    getByDate,
    save,
    remove,
  }
})
