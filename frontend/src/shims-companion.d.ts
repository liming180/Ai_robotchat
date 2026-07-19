import type { Companion } from '@/types'

declare module '@stores/companion' {
  export interface PiniaCustomStateProperties<Id extends string, S> {
    companionStore: {
      updateCompanion: (id: string, updates: Partial<Companion>) => void
    }
  }
}