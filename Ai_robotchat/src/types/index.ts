
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
}

// 消息类型定义
export interface Message {
  id: string
  conversationId: string
  role: 'user' | 'assistant'
  content: string
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

// 用户资料类型定义
export interface UserProfile {
  id: string
  name: string
  avatar?: string
  customCompanions: Companion[]
}
