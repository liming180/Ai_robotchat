import type { Companion } from './index'
import type { Store } from 'pinia'

declare module '@/stores/companion' {
  interface CompanionsStore extends Store<'companion', any> {
    updateCompanion: (id: string, updates: Partial<Companion>) => void
  }
}

declare module '@/stores/note' {
  interface NoteStore extends Store<'note', any> {
    notes: any
    loading: boolean
    error: string
    allTags: string[]
    /** 拉取列表；companionId 传空表示全部伴侣 */
    loadNotes: (companionId?: string) => Promise<void>
    /** 新增笔记；companionId 可空（不关联），conversationId 非空表示从对话存下来 */
    addNote: (input: {
      content: string
      tags?: string[]
      companionId?: string
      conversationId?: string
    }) => Promise<any>
    deleteNote: (noteId: string) => Promise<void>
    updateNote: (
      noteId: string,
      patch: { content?: string; tags?: string[]; companionId?: string },
    ) => Promise<any>
  }
}