import { defineStore } from 'pinia'
import { ref, computed, onMounted, watch } from 'vue'
import type { Conversation, Message } from '@/types'
import { isQuotaExceededError } from '@/lib/avatar'

// 序列化和反序列化 Date 对象
const serializeConversation = (conv: Conversation) => ({
  ...conv,
  createdAt: conv.createdAt.toISOString(),
  updatedAt: conv.updatedAt.toISOString(),
  messages: conv.messages.map(msg => ({
    ...msg,
    timestamp: msg.timestamp.toISOString()
  }))
})

const deserializeConversation = (data: any): Conversation => ({
  ...data,
  createdAt: new Date(data.createdAt),
  updatedAt: new Date(data.updatedAt),
  messages: data.messages.map((msg: any) => ({
    ...msg,
    timestamp: new Date(msg.timestamp)
  }))
})

export const useChatStore = defineStore('chat', () => {
  // 所有对话
  const conversations = ref<Conversation[]>([])
  const persistError = ref<string>('')
  
  // 当前选中的对话
  const currentConversationId = ref<string>('')

  // 当前对话
  const currentConversation = computed(() => 
    conversations.value.find(c => c.id === currentConversationId.value)
  )

  // 当前对话的消息
  const currentMessages = computed(() => 
    currentConversation.value?.messages || []
  )

  // 从 localStorage 加载数据
  onMounted(() => {
    const saved = localStorage.getItem('ai_companion_chats')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        conversations.value = parsed.map(deserializeConversation)
      } catch (error) {
        console.error('Failed to load chats:', error)
      }
    }
  })

  // 保存数据到 localStorage
  watch(conversations, (newVal) => {
    try {
      persistError.value = ''
      localStorage.setItem('ai_companion_chats', JSON.stringify(newVal.map(serializeConversation)))
    } catch (error) {
      if (isQuotaExceededError(error)) {
        persistError.value = '本地存储空间不足，聊天记录保存失败。请清理部分历史记录或清空缓存后重试。'
      } else {
        persistError.value = '聊天记录保存失败，请稍后重试。'
      }
      console.error('Failed to save chats:', error)
    }
  }, { deep: true })

  // 创建新对话
  const createConversation = (companionId: string, title: string = '新对话') => {
    const conversation: Conversation = {
      id: Date.now().toString(),
      companionId,
      title,
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date()
    }
    conversations.value.unshift(conversation)
    currentConversationId.value = conversation.id
    return conversation
  }

  // 选择对话 - 并且只允许选择属于当前伴侣的对话
  const selectConversation = (id: string, companionId?: string) => {
    const conversation = conversations.value.find(c => c.id === id)
    if (conversation) {
      // 如果指定了companionId，确保选择的对话属于该伴侣
      if (!companionId || conversation.companionId === companionId) {
        currentConversationId.value = id
      }
    }
  }

  // 为指定的伴侣创建或切换到一个新对话
  const createOrSwitchNewConversation = (companionId: string) => {
    // 检查当前是否已经有属于该伴侣的对话被选中
    if (!currentConversation.value || currentConversation.value.companionId !== companionId) {
      createConversation(companionId)
    } else {
      // 已经在该伴侣的对话中，创建新对话
      createConversation(companionId)
    }
  }

  // 添加消息
  const addMessage = (conversationId: string, role: 'user' | 'assistant', content: string, images?: string[]) => {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      const message: Message = {
        id: Date.now().toString(),
        conversationId,
        role,
        content,
        images: images?.length ? images : undefined,
        timestamp: new Date()
      }
      conversation.messages.push(message)
      if (conversation.messages.length > 200) {
        conversation.messages.splice(0, conversation.messages.length - 200)
      }
      conversation.updatedAt = new Date()

      // 如果是第一条消息，更新对话标题
      if (conversation.messages.length === 2 && role === 'user') {
        const titleBase = images?.length && !content.trim() ? '[图片]' : content
        conversation.title = titleBase.slice(0, 30) + (titleBase.length > 30 ? '...' : '')
      }
    }
  }

  // 重新生成最后一条消息
  const regenerateLastMessage = () => {
    if (!currentConversation.value) return
    const lastMessage = currentConversation.value.messages[currentConversation.value.messages.length - 1]
    if (lastMessage?.role === 'assistant') {
      currentConversation.value.messages.pop()
      currentConversation.value.updatedAt = new Date()
    }
  }

  // 删除对话
  const deleteConversation = (id: string) => {
    const index = conversations.value.findIndex(c => c.id === id)
    if (index !== -1) {
      const deletedConv = conversations.value[index]
      conversations.value.splice(index, 1)
      if (currentConversationId.value === id) {
        // 找到属于同一个伴侣的下一个对话，或者清空
        const nextConv = conversations.value.find(c => c.companionId === deletedConv.companionId)
        currentConversationId.value = nextConv?.id || ''

        // 如果当前伴侣没有对话了，保持当前伴侣ID但清空对话ID，避免页面关闭
        if (!nextConv && deletedConv.companionId) {
          // 重新设置伴侣对话，确保不会关闭页面
          setCompanionConversation(deletedConv.companionId)
        }
      }
    }
  }

  // 获取某个伴侣的所有对话
  const getConversationsByCompanion = (companionId: string) => {
    return conversations.value.filter(c => c.companionId === companionId)
  }

  // 为某个伴侣设置对话，确保切换伴侣时隔离会话
  const setCompanionConversation = (companionId: string) => {
    // 如果当前对话属于该伴侣，则保持不变
    if (currentConversation.value && currentConversation.value.companionId === companionId) {
      return
    }
    
    // 找到该伴侣的最近对话
    const lastConv = getConversationsByCompanion(companionId)[0]
    if (lastConv) {
      currentConversationId.value = lastConv.id
    } else {
      // 没有该伴侣的对话，创建一个新的
      currentConversationId.value = ''
    }
  }

  // Add a streaming placeholder message, return its ID
  const addStreamingPlaceholder = (conversationId: string): string => {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (!conversation) return ''
    const message: Message = {
      id: `stream-${Date.now()}`,
      conversationId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }
    conversation.messages.push(message)
    conversation.updatedAt = new Date()
    return message.id
  }

  // Update an existing message's content (used for streaming)
  const updateMessage = (messageId: string, content: string) => {
    for (const conv of conversations.value) {
      const msg = conv.messages.find(m => m.id === messageId)
      if (msg) {
        msg.content = content
        conv.updatedAt = new Date()
        return
      }
    }
  }

  return {
    conversations,
    currentConversationId,
    currentConversation,
    currentMessages,
    persistError,
    createConversation,
    createOrSwitchNewConversation,
    selectConversation,
    addMessage,
    addStreamingPlaceholder,
    updateMessage,
    regenerateLastMessage,
    deleteConversation,
    getConversationsByCompanion,
    setCompanionConversation
  }
})
