import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Note } from '@/types'
import { javaFetch } from '@/lib/api'

/**
 * 笔记数据归属 = Java 业务后端（MySQL `note` 表，任务十一）。
 *
 * 历史版本纯 localStorage，且**从未有新增入口**（`addNote` 零调用），
 * 页面永远空状态。本次完整接后端，旧 `ai-notes` 本地数据**不做迁移、直接废弃**
 * （该 key 里极可能一条数据都没有），详见 `docs/任务十一-笔记后端实施方案.md`。
 */

/** Java `GET/POST/PUT /api/v1/notes` 的单条结构。tags 是逗号分隔字符串（P1-4 契约）。 */
interface NoteDto {
  id: string
  companionId: string
  content?: string | null
  tags?: string | null
  createdAt?: string | null
  updatedAt?: string | null
}

interface NoteListDto {
  items: NoteDto[]
  total: number
  page: number
  pageSize: number
}

/** 逗号分隔字符串 → 数组，过滤空项（用户可能写 "温柔, ,治愈"） */
const parseTags = (raw?: string | null): string[] =>
  (raw || '')
    .split(',')
    .map(t => t.trim())
    .filter(t => t.length > 0)

/** 数组 → 逗号分隔字符串，后端只收字符串 */
const joinTags = (tags: string[]): string => tags.join(',')

const toNote = (dto: NoteDto): Note => ({
  id: dto.id,
  companionId: dto.companionId,
  content: dto.content || '',
  tags: parseTags(dto.tags),
  createdAt: dto.createdAt ? new Date(dto.createdAt) : new Date(),
  updatedAt: dto.updatedAt ? new Date(dto.updatedAt) : new Date(),
})

export const useNoteStore = defineStore('note', () => {
  const notes = ref<Note[]>([])
  const loading = ref(false)
  /** 加载失败原因；页面据此提示。不再有本地缓存兜底。 */
  const error = ref('')

  /** 所有笔记的标签去重集合，供筛选 tab 使用 */
  const allTags = computed(() => {
    const tags = new Set<string>()
    notes.value.forEach(note => note.tags.forEach(tag => tags.add(tag)))
    return [...tags]
  })

  /** 拉取笔记列表。companionId 传空表示全部伴侣。 */
  async function loadNotes(companionId = ''): Promise<void> {
    loading.value = true
    try {
      const query = new URLSearchParams({ page: '1', pageSize: '50' })
      if (companionId) query.set('companionId', companionId)
      const data = await javaFetch<NoteListDto>(`/api/v1/notes?${query.toString()}`)
      notes.value = (data?.items || []).map(toNote)
      error.value = ''
    } catch (e) {
      error.value = `笔记加载失败：${(e as Error).message}`
    } finally {
      loading.value = false
    }
  }

  /** 新增笔记。companionId 必选（后端会校验伴侣存在）。 */
  async function addNote(companionId: string, content: string, tags: string[] = []): Promise<Note> {
    const dto = await javaFetch<NoteDto>('/api/v1/notes', {
      method: 'POST',
      body: { companionId, content: content.trim(), tags: joinTags(tags) },
    })
    const note = toNote(dto)
    // 后端按 updatedAt 倒序返回，本地也插到最前保持一致
    notes.value.unshift(note)
    return note
  }

  /** 更新笔记。只传需要改的字段，null 表示不改。 */
  async function updateNote(
    noteId: string,
    patch: { content?: string; tags?: string[]; companionId?: string },
  ): Promise<Note> {
    const body: Record<string, unknown> = {}
    if (patch.content !== undefined) body.content = patch.content.trim()
    if (patch.tags !== undefined) body.tags = joinTags(patch.tags)
    if (patch.companionId !== undefined) body.companionId = patch.companionId

    const dto = await javaFetch<NoteDto>(`/api/v1/notes/${noteId}`, { method: 'PUT', body })
    const updated = toNote(dto)
    const index = notes.value.findIndex(n => n.id === noteId)
    if (index !== -1) notes.value[index] = updated
    return updated
  }

  /** 删除笔记（后端逻辑删除）。 */
  async function deleteNote(noteId: string): Promise<void> {
    await javaFetch<null>(`/api/v1/notes/${noteId}`, { method: 'DELETE' })
    notes.value = notes.value.filter(n => n.id !== noteId)
  }

  const filterByTag = (tag: string) => {
    if (tag === '全部') return notes.value
    return notes.value.filter(n => n.tags.includes(tag))
  }

  const searchNotes = (query: string) => {
    const lowerQuery = query.toLowerCase()
    return notes.value.filter(n =>
      n.content.toLowerCase().includes(lowerQuery) ||
      n.tags.some(tag => tag.toLowerCase().includes(lowerQuery)),
    )
  }

  return {
    notes,
    loading,
    error,
    allTags,
    loadNotes,
    addNote,
    updateNote,
    deleteNote,
    filterByTag,
    searchNotes,
  }
})
