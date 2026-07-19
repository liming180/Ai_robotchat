import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Conversation, Message } from '@/types'

export const useChatStore = defineStore('chat', () => {
  // 所有对话
  const conversations = ref<Conversation[]>([])
  
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

  // 选择对话
  const selectConversation = (id: string) => {
    currentConversationId.value = id
  }

  // 添加消息
  const addMessage = (conversationId: string, role: 'user' | 'assistant', content: string) => {
    const conversation = conversations.value.find(c => c.id === conversationId)
    if (conversation) {
      const message: Message = {
        id: Date.now().toString(),
        conversationId,
        role,
        content,
        timestamp: new Date()
      }
      conversation.messages.push(message)
      conversation.updatedAt = new Date()
      
      // 如果是第一条消息，更新对话标题
      if (conversation.messages.length === 2 && role === 'user') {
        conversation.title = content.slice(0, 30) + (content.length > 30 ? '...' : '')
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
      conversations.value.splice(index, 1)
      if (currentConversationId.value === id) {
        currentConversationId.value = conversations.value[0]?.id || ''
      }
    }
  }

  // 获取某个伴侣的所有对话
  const getConversationsByCompanion = (companionId: string) => {
    return conversations.value.filter(c => c.companionId === companionId)
  }

  return {
    conversations,
    currentConversationId,
    currentConversation,
    currentMessages,
    createConversation,
    selectConversation,
    addMessage,
    regenerateLastMessage,
    deleteConversation,
    getConversationsByCompanion
  }
})
