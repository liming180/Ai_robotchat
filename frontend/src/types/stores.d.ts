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
    addNote: (companionId: string, content: string, tags: string[]) => void
    deleteNote: (noteId: string) => void
    updateNote: (noteId: string, content: string, tags: string[]) => void
  }
}