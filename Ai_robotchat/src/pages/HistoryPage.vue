<template>
  <div class="min-h-screen relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 -z-10">
      <div class="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-purple-600/10 to-transparent"></div>
    </div>

    <!-- 顶部导航 -->
    <nav class="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/80 border-b border-white/10">
      <div class="max-w-4xl mx-auto px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <button @click="$router.back()" class="p-2 rounded-xl hover:bg-white/5 transition-colors">
              <svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
              </svg>
            </button>
            <h1 class="text-2xl font-bold text-white">聊天历史</h1>
          </div>
          <button @click="showClearConfirm = true" class="p-2 rounded-xl hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-colors">
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>
    </nav>

    <!-- 筛选器 -->
    <div class="sticky top-[73px] z-40 backdrop-blur-xl bg-slate-900/80 border-b border-white/10">
      <div class="max-w-4xl mx-auto px-6 py-4">
        <div class="flex flex-col sm:flex-row gap-4">
          <div class="relative flex-1">
            <svg class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索聊天记录..."
              class="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
            />
          </div>
          <select
            v-model="selectedTime"
            class="px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
          >
            <option value="all">全部时间</option>
            <option value="today">今天</option>
            <option value="week">本周</option>
            <option value="month">本月</option>
          </select>
        </div>
      </div>
    </div>

    <div class="max-w-4xl mx-auto px-6 py-8">
      <div v-if="groupedConversations.length > 0" class="space-y-8">
        <div v-for="group in groupedConversations" :key="group.date" class="space-y-4">
          <h3 class="text-sm font-semibold text-slate-500 uppercase tracking-wider">{{ group.date }}</h3>
          <div class="space-y-3">
            <div
              v-for="conversation in group.conversations"
              :key="conversation.id"
              @click="openConversation(conversation)"
              class="group bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-5 hover:bg-white/10 hover:border-pink-500/30 transition-all cursor-pointer"
            >
              <div class="flex items-start gap-4">
                <img
                  :src="getCompanionAvatar(conversation.companionId)"
                  class="w-14 h-14 rounded-2xl object-cover flex-shrink-0"
                />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between mb-2">
                    <h4 class="font-semibold text-white truncate">{{ conversation.title }}</h4>
                    <span class="text-xs text-slate-500 flex-shrink-0 ml-2">{{ formatTime(conversation.updatedAt) }}</span>
                  </div>
                  <p class="text-slate-400 text-sm truncate mb-3">{{ getPreviewText(conversation) }}</p>
                  <div class="flex items-center justify-between">
                    <span class="text-xs text-slate-500">{{ getCompanionName(conversation.companionId) }}</span>
                    <button
                      @click.stop="deleteConversation(conversation.id)"
                      class="opacity-0 group-hover:opacity-100 p-2 rounded-lg hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-all"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-else class="text-center py-20">
        <div class="w-24 h-24 rounded-full bg-white/5 mx-auto mb-6 flex items-center justify-center">
          <svg class="w-12 h-12 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
        </div>
        <h3 class="text-xl font-semibold text-white mb-2">暂无聊天记录</h3>
        <p class="text-slate-400 mb-6">开始一段新的对话吧</p>
        <button @click="$router.push('/')" class="px-6 py-3 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl font-semibold text-white hover:from-pink-400 hover:to-purple-500 transition-all">
          选择伴侣
        </button>
      </div>
    </div>

    <!-- 清空确认弹窗 -->
    <div v-if="showClearConfirm" class="fixed inset-0 z-50 flex items-center justify-center p-6">
      <div class="absolute inset-0 bg-black/60" @click="showClearConfirm = false"></div>
      <div class="relative bg-slate-900 border border-white/10 rounded-3xl p-8 max-w-md w-full shadow-2xl">
        <h3 class="text-xl font-bold text-white mb-3">清空所有历史</h3>
        <p class="text-slate-400 mb-8">确定要删除所有聊天记录吗？此操作无法撤销。</p>
        <div class="flex gap-4">
          <button
            @click="showClearConfirm = false"
            class="flex-1 py-3 bg-white/5 border border-white/10 rounded-xl font-semibold text-slate-300 hover:bg-white/10 transition-all"
          >
            取消
          </button>
          <button
            @click="clearAllHistory"
            class="flex-1 py-3 bg-red-500/20 border border-red-500/30 rounded-xl font-semibold text-red-400 hover:bg-red-500/30 transition-all"
          >
            清空
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useCompanionStore } from '@/stores/companion'

const router = useRouter()
const chatStore = useChatStore()
const companionStore = useCompanionStore()

const searchQuery = ref('')
const selectedTime = ref('all')
const showClearConfirm = ref(false)

const filteredConversations = computed(() => {
  let conversations = [...chatStore.conversations].sort((a, b) => 
    new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
  )

  // 搜索筛选
  if (searchQuery.value) {
    conversations = conversations.filter(conv => {
      const titleMatch = conv.title.toLowerCase().includes(searchQuery.value.toLowerCase())
      const messageMatch = conv.messages.some(msg => 
        msg.content.toLowerCase().includes(searchQuery.value.toLowerCase())
      )
      return titleMatch || messageMatch
    })
  }

  // 时间筛选
  const now = new Date()
  if (selectedTime.value === 'today') {
    conversations = conversations.filter(conv => {
      const convDate = new Date(conv.updatedAt)
      return convDate.toDateString() === now.toDateString()
    })
  } else if (selectedTime.value === 'week') {
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    conversations = conversations.filter(conv => new Date(conv.updatedAt) >= weekAgo)
  } else if (selectedTime.value === 'month') {
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
    conversations = conversations.filter(conv => new Date(conv.updatedAt) >= monthAgo)
  }

  return conversations
})

const groupedConversations = computed(() => {
  const groups: { date: string; conversations: typeof chatStore.conversations }[] = []
  const today = new Date().toDateString()
  const yesterday = new Date(Date.now() - 86400000).toDateString()

  filteredConversations.value.forEach(conv => {
    const convDate = new Date(conv.updatedAt).toDateString()
    let dateLabel = formatDateLabel(new Date(conv.updatedAt))
    
    if (convDate === today) dateLabel = '今天'
    else if (convDate === yesterday) dateLabel = '昨天'

    const existingGroup = groups.find(g => g.date === dateLabel)
    if (existingGroup) {
      existingGroup.conversations.push(conv)
    } else {
      groups.push({ date: dateLabel, conversations: [conv] })
    }
  })

  return groups
})

const getCompanionAvatar = (companionId: string) => {
  return companionStore.getCompanionById(companionId)?.avatar || ''
}

const getCompanionName = (companionId: string) => {
  return companionStore.getCompanionById(companionId)?.name || '未知'
}

const getPreviewText = (conversation: typeof chatStore.conversations[0]) => {
  const lastMessage = conversation.messages[conversation.messages.length - 1]
  if (!lastMessage) return '暂无消息'
  return lastMessage.content.length > 60 
    ? lastMessage.content.slice(0, 60) + '...' 
    : lastMessage.content
}

const formatTime = (date: Date) => {
  const d = new Date(date)
  const hours = d.getHours().toString().padStart(2, '0')
  const minutes = d.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

const formatDateLabel = (date: Date) => {
  const d = new Date(date)
  const year = d.getFullYear()
  const month = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  return `${year}年${month}月${day}日`
}

const openConversation = (conversation: typeof chatStore.conversations[0]) => {
  chatStore.selectConversation(conversation.id)
  router.push(`/chat/${conversation.companionId}`)
}

const deleteConversation = (id: string) => {
  if (confirm('确定要删除这个对话吗？')) {
    chatStore.deleteConversation(id)
  }
}

const clearAllHistory = () => {
  chatStore.conversations.forEach(conv => chatStore.deleteConversation(conv.id))
  showClearConfirm.value = false
}
</script>
