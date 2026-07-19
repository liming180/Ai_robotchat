<template>
  <div class="h-screen flex bg-slate-900 relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 -z-10 opacity-30">
      <div class="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-pink-600/10 to-transparent"></div>
    </div>

    <!-- 左侧边栏 - 对话历史 -->
    <aside class="w-72 bg-slate-800/50 backdrop-blur-xl border-r border-white/10 flex flex-col hidden md:flex">
      <div class="p-4 border-b border-white/10">
        <button
          @click="$router.push('/')"
          class="w-full p-4 bg-gradient-to-r from-pink-500 to-purple-600 rounded-2xl font-medium hover:from-pink-400 hover:to-purple-500 transition-all glow-button flex items-center justify-center gap-2"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
          新对话
        </button>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-2">
        <h3 class="text-sm font-medium text-slate-400 mb-3">对话历史</h3>
        <div
          v-for="conversation in companionConversations"
          :key="conversation.id"
          @click="selectConversation(conversation.id)"
          :class="[
            'p-4 rounded-2xl cursor-pointer transition-all group',
            chatStore.currentConversationId === conversation.id
              ? 'bg-gradient-to-r from-pink-500/20 to-purple-500/20 border border-pink-500/30'
              : 'bg-white/5 border border-white/10 hover:bg-white/10'
          ]"
        >
          <div class="flex items-start justify-between">
            <p class="text-sm truncate flex-1 text-white">{{ conversation.title }}</p>
            <button
              @click.stop="deleteConversation(conversation.id)"
              class="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-red-500/20 text-slate-400 hover:text-red-400 transition-all"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
          <p class="text-xs text-slate-500 mt-1">{{ formatDate(conversation.updatedAt) }}</p>
        </div>

        <div v-if="companionConversations.length === 0" class="text-center py-12 text-slate-500">
          <p class="text-sm">还没有对话</p>
          <p class="text-xs mt-1">开始和 {{ currentCompanion?.name }} 聊天吧！</p>
        </div>
      </div>
    </aside>

    <!-- 主聊天区 -->
    <main class="flex-1 flex flex-col bg-slate-900/50">
      <!-- 顶部头部 -->
      <header class="p-4 border-b border-white/10 bg-slate-800/50 backdrop-blur-xl">
        <div class="flex items-center justify-between max-w-4xl mx-auto">
          <div class="flex items-center gap-4">
            <button @click="$router.push('/')" class="p-2 rounded-xl hover:bg-white/5 transition-colors md:hidden">
              <svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
              </svg>
            </button>
            
            <img
              v-if="currentCompanion"
              :src="currentCompanion.avatar"
              :alt="currentCompanion.name"
              class="w-12 h-12 rounded-2xl object-cover"
            />
            
            <div>
              <h2 class="font-semibold text-white">{{ currentCompanion?.name }}</h2>
              <p class="text-xs text-slate-400">{{ currentCompanion?.personality }}</p>
            </div>
          </div>
          
          <div class="flex items-center gap-3">
            <!-- 亲密度显示 -->
            <div v-if="currentCompanion" class="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-xl">
              <svg class="w-5 h-5 text-pink-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
              </svg>
              <span class="text-sm text-slate-300">{{ currentCompanion.intimacy }}%</span>
            </div>
            <!-- 设置按钮 -->
            <button
              @click="$router.push(`/settings/${currentCompanion?.id}`)" class="p-2 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94-1.543.826-3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
            </button>
          </div>
        </div>
      </header>

      <!-- 消息区域 -->
      <div class="flex-1 overflow-y-auto p-4" ref="messagesContainer">
        <div class="max-w-4xl mx-auto space-y-6">
          <!-- 欢迎消息 -->
          <div v-if="chatStore.currentMessages.length === 0" class="text-center py-16">
            <div class="w-24 h-24 rounded-3xl bg-gradient-to-br from-pink-500 to-purple-600 mx-auto mb-6 flex items-center justify-center shadow-xl shadow-pink-500/30">
              <svg class="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
              </svg>
            </div>
            <h3 class="text-2xl font-semibold text-white mb-3">你好！我是 {{ currentCompanion?.name }}</h3>
            <p class="text-slate-400 max-w-md mx-auto">{{ currentCompanion?.description }}</p>
          </div>

          <!-- 消息列表 -->
          <div
            v-for="(message, index) in chatStore.currentMessages"
            :key="message.id"
            :class="[
              'flex gap-4 message-slide-in',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            ]"
            :style="{ animationDelay: `${index * 0.05}s` }"
          >
            <!-- AI 消息 -->
            <div v-if="message.role === 'assistant'" class="flex gap-4 max-w-2xl">
              <img
                v-if="currentCompanion"
                :src="currentCompanion.avatar"
                :alt="currentCompanion.name"
                class="w-10 h-10 rounded-2xl object-cover flex-shrink-0"
              />
              <div class="flex-1">
                <div class="bg-slate-800 rounded-2xl rounded-tl-sm px-5 py-4 border border-white/10">
                  <p class="text-sm leading-relaxed text-slate-200 whitespace-pre-wrap">{{ message.content }}</p>
                </div>
                <div class="flex items-center gap-2 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click="copyMessage(message.content)" class="p-1.5 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                    </svg>
                  </button>
                  <button @click="regenerateMessage" class="p-1.5 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-white transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            <!-- 用户消息 -->
            <div v-else class="flex gap-4 max-w-2xl justify-end">
              <div class="flex-1 flex justify-end">
                <div class="bg-gradient-to-r from-pink-500 to-purple-600 rounded-2xl rounded-tr-sm px-5 py-4 shadow-lg shadow-pink-500/20">
                  <p class="text-sm leading-relaxed text-white whitespace-pre-wrap">{{ message.content }}</p>
                </div>
              </div>
              <div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <span class="text-xs font-bold text-white">你</span>
              </div>
            </div>
          </div>

          <!-- 打字动画 -->
          <div v-if="isTyping" class="flex gap-4">
            <img
              v-if="currentCompanion"
              :src="currentCompanion.avatar"
              :alt="currentCompanion.name"
              class="w-10 h-10 rounded-2xl object-cover flex-shrink-0"
            />
            <div class="bg-slate-800 rounded-2xl rounded-tl-sm px-5 py-4 border border-white/10">
              <div class="flex gap-1.5">
                <span
                  v-for="i in 3"
                  :key="i"
                  class="w-2.5 h-2.5 bg-slate-400 rounded-full"
                  :style="{ animation: `typing 1s infinite ${(i - 1) * 0.2}s` }"
                ></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 快捷回复 -->
      <div v-if="!isTyping && chatStore.currentMessages.length === 0" class="px-4 pb-3">
        <div class="max-w-4xl mx-auto">
          <div class="flex gap-2 overflow-x-auto pb-2">
            <button
              v-for="suggestion in quickSuggestions"
              :key="suggestion"
              @click="useQuickReply(suggestion)"
              class="flex-shrink-0 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-sm text-slate-300 hover:bg-white/10 hover:border-pink-500/30 transition-all"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="p-4 border-t border-white/10 bg-slate-800/50 backdrop-blur-xl">
        <div class="max-w-4xl mx-auto">
          <div class="bg-white/5 border border-white/10 rounded-2xl focus-within:border-pink-500/50 transition-all">
            <textarea
              v-model="messageInput"
              @keydown.enter.prevent="sendMessage"
              placeholder="输入消息..."
              rows="1"
              class="w-full bg-transparent px-5 py-4 resize-none focus:outline-none text-sm text-white placeholder-slate-500"
              ref="textareaRef"
              @input="autoResize"
            ></textarea>
            <div class="flex items-center justify-between px-4 pb-4">
              <div class="flex items-center gap-2">
                <!-- 附件按钮（预留） -->
                <button class="p-2 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7.172l-4.143-4.142a2 2 0 00-2.828 0l-4.143 4.142a2 2 0 00-.585 1.414V18a2 2 0 002 2h11a2 2 0 002-2V8.586a2 2 0 00-.585-1.414z"/>
                  </svg>
                </button>
              </div>
              <button
                @click="sendMessage"
                :disabled="!messageInput.trim() || isTyping"
                class="p-3 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl hover:from-pink-400 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all glow-button"
              >
                <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompanionStore } from '@/stores/companion'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const router = useRouter()
const companionStore = useCompanionStore()
const chatStore = useChatStore()

const messageInput = ref('')
const isTyping = ref(false)
const textareaRef = ref<HTMLTextAreaElement>()
const messagesContainer = ref<HTMLElement>()

const companionId = computed(() => route.params.id as string)
const currentCompanion = computed(() => companionStore.getCompanionById(companionId.value))
const companionConversations = computed(() => chatStore.getConversationsByCompanion(companionId.value))

const quickSuggestions = [
  '你好呀',
  '今天过得怎么样？',
  '给我讲个笑话',
  '我们聊聊天',
]

const autoResize = () => {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 200) + 'px'
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

const selectConversation = (id: string) => {
  chatStore.selectConversation(id)
  scrollToBottom()
}

const deleteConversation = (id: string) => {
  if (confirm('确定要删除这个对话吗？')) {
    chatStore.deleteConversation(id)
  }
}

const useQuickReply = (text: string) => {
  messageInput.value = text
  sendMessage()
}

const sendMessage = async () => {
  if (!messageInput.value.trim() || isTyping.value || !currentCompanion.value) return

  const content = messageInput.value.trim()
  messageInput.value = ''
  
  // 确保有对话
  if (!chatStore.currentConversation || chatStore.currentConversation.companionId !== companionId.value) {
    chatStore.createConversation(companionId.value)
  }

  // 添加用户消息
  chatStore.addMessage(chatStore.currentConversationId, 'user', content)

  // 模拟 AI 回复
  isTyping.value = true
  
  // 滚动到底部
  scrollToBottom()
  
  // 模拟网络延迟
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1500))
  
  // 生成回复
  const personality = currentCompanion.value.personality
  const replies = {
    '温柔体贴': [
      '我在这里陪着你呢，想和我聊些什么都可以～ 💖',
      '谢谢你和我说这些，我能感受到你的心意 ❤️',
      '你今天过得怎么样呀？和我分享一下吧～',
      '有什么我可以帮到你的吗？我会尽力的！',
      '听到你这么说，我感到很开心呢 💕',
    ],
    '阳光积极': [
      '你好呀！今天也要元气满满呢 ✨',
      '保持好心情，一切都会好起来的！加油！',
      '很高兴能和你聊天，今天有什么开心的事吗？',
      '新的一天，新的开始！我们来聊聊开心的事情吧！',
    ],
    '幽默风趣': [
      '哈哈，你好呀！今天开心吗？要不要听个笑话？',
      '哎呀，终于有人来和我聊天啦！我可想死你了！',
      '有我在，保证让你开开心心每一天！',
    ],
    '文艺优雅': [
      '你好呀～ 今天的心情怎么样？要不要和我分享？',
      '生活中的每一刻都值得被记录呢，你说对吗？',
      '在这个美好的时刻，能和你聊天真好',
    ],
  }
  
  const personalityReplies = replies[personality as keyof typeof replies] || replies['温柔体贴']
  const reply = personalityReplies[Math.floor(Math.random() * personalityReplies.length)]
  
  chatStore.addMessage(chatStore.currentConversationId, 'assistant', reply)
  
  // 增加亲密度
  companionStore.increaseIntimacy(companionId.value, 2)
  
  isTyping.value = false
  
  // 滚动到底部
  scrollToBottom()
}

const copyMessage = (content: string) => {
  navigator.clipboard.writeText(content)
  alert('已复制到剪贴板！')
}

const regenerateMessage = () => {
  if (chatStore.currentMessages.length >= 1) {
    const lastUserMessage = chatStore.currentMessages.filter(m => m.role === 'user').pop()
    if (lastUserMessage) {
      messageInput.value = lastUserMessage.content
      sendMessage()
    }
  }
}

const formatDate = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

onMounted(() => {
  // 加载数据
  if (!currentCompanion.value) {
    router.push('/')
  }
  scrollToBottom()
})

// 监听消息变化滚动到底部
watch(() => chatStore.currentMessages.length, () => {
  scrollToBottom()
})
</script>
