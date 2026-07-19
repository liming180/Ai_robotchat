import type { Companion } from '@/types'

declare module '@/stores/companion' {
  interface CompanionsStore {
    updateCompanion: (id: string, updates: Partial<Companion>) => void
  }
}