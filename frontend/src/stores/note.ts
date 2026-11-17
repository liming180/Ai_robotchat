import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Note } from '@/types'
import { javaFetch } from '@/lib/api'

/**
 * 笔记数据归属 = Java 业务后端（MySQL `note` 表，任务十一）。
 *
 * 2026-11-17 任务十二对齐设计稿：
 * - 新增 `conversationId`（来源会话，非空 = 从对话「存为笔记」），以此区分来源，**不设 origin 列**
 * - `companionId` 改为可空（手动笔记允许「不关联」）
 * - 标题不落库，展示层由 `useNoteTitle`（`lib/note.ts`）从正文首行派生
 */

/** Java `GET/POST/PUT /api/v1/notes` 的单条结构。tags 是逗号分隔字符串（P1-4 契约）。 */
interface NoteDto {
  id: string
  companionId?: string | null
  conversationId?: string | null
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

/** 新增笔记的入参。companionId 传空表示「不关联」 */
export interface AddNoteInput {
  content: string
  tags?: string[]
  companionId?: string
  /** 从对话存笔记时传当前会话 id，后端会校验归属当前用户 */
  conversationId?: string
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
  // 空串归一成 undefined，避免模板里出现「记在 名下」
  companionId: dto.companionId || undefined,
  conversationId: dto.conversationId || undefined,
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

  /** 新增笔记。companionId 可空（不关联）；conversationId 非空表示从对话存下来。 */
  async function addNote(input: AddNoteInput): Promise<Note> {
    const body: Record<string, unknown> = { content: input.content.trim() }
    // 空串不传，后端按 null 处理；传空串也能被 hasText 挡掉，但少传更干净
    if (input.companionId) body.companionId = input.companionId
    if (input.conversationId) body.conversationId = input.conversationId
    body.tags = joinTags(input.tags || [])

    const dto = await javaFetch<NoteDto>('/api/v1/notes', { method: 'POST', body })
    const note = toNote(dto)
    // 后端按 updatedAt 倒序返回，本地也插到最前保持一致
    notes.value.unshift(note)
    return note
  }

  /**
   * 更新笔记。只传需要改的字段，null 表示不改。
   *
   * companionId 的语义：`undefined` = 不修改，空串 = 解除关联（后端把列置 NULL）。
   */
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
