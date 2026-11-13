import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Conversation, Message } from '@/types'
import { javaFetch } from '@/lib/api'

/**
 * 会话与消息数据源 = Java（MySQL）。
 * localStorage 只在拉取失败时作为只读缓存兜底。
 */

const CACHE_KEY = 'ai_companion_chats'

/** Java `ConversationResponse`（列表不含消息） */
interface ConversationDto {
  id: string
  companionId: string
  title?: string | null
  updatedAt?: string | null
}

/** Java `ConversationDetailResponse.MessageResponse` */
interface MessageDto {
  id: string
  role: 'user' | 'assistant' | string
  content?: string | null
  /** 图片 URL 的 JSON 数组字符串，Java 不反序列化，前端自行 parse */
  images?: string | null
  createdAt?: string | null
}

interface ConversationDetailDto {
  id: string
  title?: string | null
  companion?: { id: string } | null
  messages?: MessageDto[]
}

const parseImages = (images?: string | null): string[] | undefined => {
  if (!images) return undefined
  try {
    const list = JSON.parse(images)
    return Array.isArray(list) && list.length ? list : undefined
  } catch {
    return undefined
  }
}

const toMessage = (dto: MessageDto, conversationId: string): Message => ({
  id: dto.id,
  conversationId,
  role: dto.role === 'assistant' ? 'assistant' : 'user',
  content: dto.content || '',
  images: parseImages(dto.images),
  timestamp: dto.createdAt ? new Date(dto.createdAt) : new Date(),
})

const toConversation = (dto: ConversationDto): Conversation => ({
  id: dto.id,
  companionId: dto.companionId,
  title: dto.title || '新对话',
  messages: [],
  createdAt: dto.updatedAt ? new Date(dto.updatedAt) : new Date(),
  updatedAt: dto.updatedAt ? new Date(dto.updatedAt) : new Date(),
})

/** 首条消息生成会话标题：纯图片记 [图片]，否则取前 30 字 */
const deriveTitle = (content: string, images?: string[]) => {
  const base = !content.trim() && images?.length ? '[图片]' : content.trim()
  return base.slice(0, 30) + (base.length > 30 ? '...' : '')
}

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<string>('')
  const loading = ref(false)
  const error = ref('')
  const fromCache = ref(false)

  const currentConversation = computed(() =>
    conversations.value.find(c => c.id === currentConversationId.value)
  )

  const currentMessages = computed(() => currentConversation.value?.messages || [])

  const readCache = (): Conversation[] => {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return []
    try {
      const list = JSON.parse(raw)
      if (!Array.isArray(list)) return []
      return list.map((c: any): Conversation => ({
        id: String(c.id),
        companionId: String(c.companionId ?? ''),
        title: c.title || '新对话',
        createdAt: new Date(c.createdAt ?? Date.now()),
        updatedAt: new Date(c.updatedAt ?? Date.now()),
        messages: Array.isArray(c.messages)
          ? c.messages.map((m: any): Message => ({
              id: String(m.id),
              conversationId: String(m.conversationId ?? c.id),
              role: m.role === 'assistant' ? 'assistant' : 'user',
              content: m.content || '',
              images: Array.isArray(m.images) && m.images.length ? m.images : undefined,
              timestamp: new Date(m.timestamp ?? Date.now()),
            }))
          : [],
      }))
    } catch {
      localStorage.removeItem(CACHE_KEY)
      return []
    }
  }

  const writeCache = () => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(conversations.value.map(c => ({
        ...c,
        createdAt: c.createdAt.toISOString(),
        updatedAt: c.updatedAt.toISOString(),
        messages: c.messages.map(m => ({ ...m, timestamp: m.timestamp.toISOString() })),
      }))))
    } catch {
      // 缓存写失败不影响主流程
    }
  }

  /**
   * 拉取会话列表。
   * @param companionId 只拉某个伴侣的会话；不传则拉全部（历史页用）
   * @param withMessages 是否同时拉每条会话的消息（历史页做预览/搜索需要）
   */
  async function loadConversations(companionId?: string, withMessages = false): Promise<void> {
    loading.value = true
    try {
      const suffix = companionId ? `?companionId=${encodeURIComponent(companionId)}&page=1&pageSize=50` : '?page=1&pageSize=50'
      const list = await javaFetch<ConversationDto[]>(`/api/v1/chat/conversations${suffix}`)
      const mapped = (list || []).map(toConversation)

      // 保留已加载的消息，避免列表刷新把当前会话内容清空
      for (const conv of mapped) {
        const existing = conversations.value.find(c => c.id === conv.id)
        if (existing?.messages.length) conv.messages = existing.messages
      }

      conversations.value = mapped
      error.value = ''
      fromCache.value = false

      if (withMessages) {
        await Promise.all(mapped.map(conv =>
          conv.messages.length ? Promise.resolve() : loadMessages(conv.id).catch(() => undefined)
        ))
      }
      writeCache()
    } catch (e) {
      const cached = readCache()
      if (cached.length) {
        conversations.value = cached
        fromCache.value = true
        error.value = `会话列表加载失败，正在显示离线缓存：${(e as Error).message}`
      } else {
        error.value = `会话列表加载失败：${(e as Error).message}`
      }
    } finally {
      loading.value = false
    }
  }

  /** 拉取单个会话的消息（覆盖该会话的 messages） */
  async function loadMessages(conversationId: string): Promise<void> {
    if (!conversationId) return
    const detail = await javaFetch<ConversationDetailDto>(`/api/v1/chat/conversations/${conversationId}`)
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (!conversation) return

    conversation.messages = (detail.messages || []).map(m => toMessage(m, conversationId))
    if (detail.title) conversation.title = detail.title
    if (detail.companion?.id) conversation.companionId = detail.companion.id
    writeCache()
  }

  /**
   * 首次发送消息时才真正建会话（懒创建），避免侧栏堆一堆空「新对话」。
   * 当前已选中该伴侣的会话时直接复用。
   */
  async function ensureConversation(companionId: string, title?: string): Promise<Conversation> {
    const current = currentConversation.value
    if (current && current.companionId === companionId) return current

    const dto = await javaFetch<ConversationDto>('/api/v1/chat/conversations', {
      method: 'POST',
      body: { companionId, title: title || '新对话' },
    })
    const conversation = toConversation(dto)
    conversation.companionId = companionId
    conversations.value.unshift(conversation)
    currentConversationId.value = conversation.id
    writeCache()
    return conversation
  }

  /** 清空当前选择，进入「待创建」状态：不发请求，首次发送时才由 ensureConversation 建库 */
  function startDraft() {
    currentConversationId.value = ''
  }

  function selectConversation(id: string, companionId?: string) {
    const conversation = conversations.value.find(c => c.id === id)
    if (!conversation) return
    if (companionId && conversation.companionId !== companionId) return
    currentConversationId.value = id
  }

  /** 本地乐观追加一条消息（流式期间展示用），不落库 */
  function addMessage(
    conversationId: string,
    role: 'user' | 'assistant',
    content: string,
    images?: string[],
  ): Message | null {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (!conversation) return null

    const message: Message = {
      id: `local-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`,
      conversationId,
      role,
      content,
      images: images?.length ? images : undefined,
      timestamp: new Date(),
    }
    conversation.messages.push(message)
    if (conversation.messages.length > 200) {
      conversation.messages.splice(0, conversation.messages.length - 200)
    }
    conversation.updatedAt = new Date()
    writeCache()
    return message
  }

  /** 流式回复结束后把一条消息落库（generate=false，只落库不调 AI） */
  async function saveMessage(
    conversationId: string,
    role: 'user' | 'assistant',
    content: string,
    images?: string[],
  ): Promise<void> {
    await javaFetch(`/api/v1/chat/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: {
        role,
        content,
        images: images?.length ? JSON.stringify(images) : null,
        generate: false,
      },
    })
  }

  /** 一次提交 user + assistant 两条；assistant 为空则跳过（如流式失败只保留用户消息） */
  async function saveMessages(
    conversationId: string,
    userMsg: { content: string; images?: string[] },
    aiMsg?: { content: string; images?: string[] },
  ): Promise<void> {
    await saveMessage(conversationId, 'user', userMsg.content, userMsg.images)
    if (aiMsg && (aiMsg.content.trim() || aiMsg.images?.length)) {
      await saveMessage(conversationId, 'assistant', aiMsg.content, aiMsg.images)
    }
  }

  async function deleteConversation(id: string): Promise<void> {
    const index = conversations.value.findIndex(c => c.id === id)
    const target = index !== -1 ? conversations.value[index] : undefined

    await javaFetch(`/api/v1/chat/conversations/${id}`, { method: 'DELETE' })

    if (index !== -1) conversations.value.splice(index, 1)
    if (currentConversationId.value === id) {
      currentConversationId.value = ''
      if (target) setCompanionConversation(target.companionId)
    }
    writeCache()
  }

  const getConversationsByCompanion = (companionId: string) =>
    conversations.value.filter(c => c.companionId === companionId)

  /** 切到某伴侣最近的一条会话；没有则进入待创建状态 */
  function setCompanionConversation(companionId: string) {
    const current = currentConversation.value
    if (current && current.companionId === companionId) return

    const last = getConversationsByCompanion(companionId)[0]
    currentConversationId.value = last?.id || ''
  }

  const totalMessages = computed(() =>
    conversations.value.reduce((acc, conv) => acc + conv.messages.length, 0)
  )

  return {
    conversations,
    currentConversationId,
    currentConversation,
    currentMessages,
    loading,
    error,
    fromCache,
    totalMessages,
    loadConversations,
    loadMessages,
    ensureConversation,
    startDraft,
    selectConversation,
    addMessage,
    saveMessage,
    saveMessages,
    deleteConversation,
    getConversationsByCompanion,
    setCompanionConversation,
    deriveTitle,
  }
})
