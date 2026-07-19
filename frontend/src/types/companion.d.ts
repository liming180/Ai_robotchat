import type { Companion } from './index'

declare module '@/stores/companion' {
  interface CompanionsStore {
    updateCompanion: (id: string, updates: Partial<Companion>) => void
  }
}