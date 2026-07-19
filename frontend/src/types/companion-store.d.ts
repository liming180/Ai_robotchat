import type { Companion } from './index'
import type { Store } from 'pinia'

interface CompanionsStore extends Store<'companion', any> {
  companions: any
  customCompanions: any
  updateCompanion: (id: string, updates: Partial<Companion>) => void
  allCompanions: any
  favoriteCompanions: any
  filterByCategory: any
  searchCompanions: any
  getCompanionById: any
  toggleFavorite: any
  addCustomCompanion: any
  increaseIntimacy: any
}