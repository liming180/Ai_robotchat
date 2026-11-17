
// 伴侣类型定义
export interface Companion {
  id: string
  name: string
  avatar: string
  description: string
  category: string
  personality: string
  systemPrompt: string
  isFavorite: boolean
  intimacy: number
  createdAt: Date
  tags: string[]
  /** 预置伴侣（preset-1~4）不可编辑/删除，前端据此隐藏入口 */
  isPreset?: boolean
  /** 创建者 userId；'system' 表示系统预置 */
  createdBy?: string
}

// 消息类型定义
export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant'
  content: string
  images?: string[]  // base64 data URLs of attached images
  timestamp: Date
  isEditing?: boolean
}

// 对话类型定义
export interface Conversation {
  id: string
  companionId: string
  title: string
  messages: Message[]
  createdAt: Date
  updatedAt: Date
}

export interface Note {
  id: string
  /** 可为空：手动写的笔记允许「不关联」任何伴侣 */
  companionId?: string
  /** 来源会话：非空 = 从对话「存为笔记」，为空 = 手动写的（以此区分来源，无 origin 字段） */
  conversationId?: string
  content: string
  tags: string[]
  createdAt: Date
  /** 后端在每次更新时刷新；列表按此倒序 */
  updatedAt: Date
}

// 用户资料类型定义
export interface UserProfile {
  id: string
  name: string
  avatar?: string
  customCompanions: Companion[]
}

// ===== 情感感知模块 =====
export type EmotionType = 'happy' | 'sad' | 'angry' | 'anxious' | 'neutral'

export interface EmotionRecord {
  id: string
  emotion: EmotionType
  intensity: number  // 0-100
  content: string
  timestamp: Date
}

export interface EmotionStats {
  total: number
  dominant: EmotionType
  distribution: Record<EmotionType, number>
}

// ===== 个性化记忆模块 =====
export type MemoryType = 'preference' | 'habit' | 'important_date' | 'milestone'

export interface Memory {
  id: string
  type: MemoryType
  content: string
  createdAt: Date
  companionId?: string
}

export interface MemoryCategory {
  id: MemoryType
  name: string
  icon: string
}

// ===== 场景化陪伴模块 =====
export type SceneType = 'bedtime_story' | 'morning_greeting' | 'pomodoro' | 'weather'

export interface SceneSetting {
  enabled: boolean
  time?: string  // HH:mm 触发时间
}

export type SceneSettings = Partial<Record<SceneType, SceneSetting>>

// ===== 多模态互动模块 =====
export type GameType = 'truth_dare' | 'shared_todo' | 'would_you_rather'

export interface SharedTodo {
  id: string
  content: string
  done: boolean
}

export interface TruthDareCard {
  id: string
  type: 'truth' | 'dare' | 'would_you_rather'
  content: string
}

// 已保存的 AI 生成内容（随笔/睡前故事/晨间问候）
export type SavedContentKind = 'essay' | 'bedtime' | 'morning'

export interface SavedContent {
  id: string
  kind: SavedContentKind
  date: string  // YYYY-MM-DD
  title: string
  content: string
  createdAt: Date
}
