import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Note } from '@/types'

export const useNoteStore = defineStore('note', () => {
  const notes = ref<Note[]>([])

  const allTags = computed(() => {
    const tags = new Set<string>()
    notes.value.forEach(note => {
      note.tags.forEach(tag => tags.add(tag))
    })
    return [...tags]
  })

  const addNote = (companionId: string, content: string, tags: string[] = []) => {
    const note: Note = {
      id: Date.now().toString(),
      companionId,
      content,
      tags,
      createdAt: new Date()
    }
    notes.value.push(note)
    saveToLocalStorage()
  }

  const deleteNote = (noteId: string) => {
    notes.value = notes.value.filter(n => n.id !== noteId)
    saveToLocalStorage()
  }

  const updateNote = (noteId: string, content: string, tags: string[]) => {
    const note = notes.value.find(n => n.id === noteId)
    if (note) {
      note.content = content
      note.tags = tags
      saveToLocalStorage()
    }
  }

  const filterByTag = (tag: string) => {
    if (tag === '全部') return notes.value
    return notes.value.filter(n => n.tags.includes(tag))
  }

  const searchNotes = (query: string) => {
    const lowerQuery = query.toLowerCase()
    return notes.value.filter(n => 
      n.content.toLowerCase().includes(lowerQuery) || 
      n.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    )
  }

  const saveToLocalStorage = () => {
    localStorage.setItem('ai-notes', JSON.stringify(notes.value))
  }

  const loadFromLocalStorage = () => {
    const saved = localStorage.getItem('ai-notes')
    if (saved) {
      const parsed = JSON.parse(saved)
      notes.value = parsed.map((n: any) => ({
        ...n,
        createdAt: new Date(n.createdAt)
      }))
    }
  }

  loadFromLocalStorage()

  return {
    notes,
    allTags,
    addNote,
    deleteNote,
    updateNote,
    filterByTag,
    searchNotes
  }
})
