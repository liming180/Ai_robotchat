<template>
  <div class="h-screen flex bg-[#0d0f14] overflow-hidden">

    <!-- 左侧边栏 -->
    <aside class="w-72 flex-shrink-0 hidden md:flex flex-col border-r border-white/5 bg-[#111318]">
      <!-- 侧栏头部 -->
      <div class="p-5 border-b border-white/5">
        <button
          @click="createNewConversation"
          class="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-2xl bg-gradient-to-r from-violet-600 to-pink-500 text-white text-sm font-medium hover:opacity-90 active:scale-[0.98] transition-all shadow-lg shadow-violet-500/20"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/>
          </svg>
          新对话
        </button>
      </div>

      <!-- 对话列表 -->
      <div class="flex-1 overflow-y-auto p-3 space-y-1 scrollbar-thin">
        <p class="text-xs font-medium text-slate-500 uppercase tracking-wider px-3 py-2">历史对话</p>

        <div
          v-for="conv in companionConversations"
          :key="conv.id"
          @click="selectConversation(conv.id)"
          class="group relative flex items-center gap-3 px-3 py-3 rounded-xl cursor-pointer transition-all"
          :class="chatStore.currentConversationId === conv.id
            ? 'bg-white/8 text-white'
            : 'text-slate-400 hover:bg-white/4 hover:text-slate-200'"
        >
          <div class="w-1.5 h-1.5 rounded-full flex-shrink-0 transition-colors"
            :class="chatStore.currentConversationId === conv.id ? 'bg-violet-400' : 'bg-transparent group-hover:bg-slate-600'"/>
          <div class="flex-1 min-w-0">
            <p class="text-sm truncate">{{ conv.title }}</p>
            <p class="text-xs text-slate-600 mt-0.5">{{ formatDate(conv.updatedAt) }}</p>
          </div>
          <button
            @click.stop="deleteConversation(conv.id)"
            class="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-red-500/20 text-slate-500 hover:text-red-400 transition-all flex-shrink-0"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div v-if="companionConversations.length === 0" class="text-center py-10 text-slate-600">
          <svg class="w-10 h-10 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <p class="text-sm">暂无对话记录</p>
        </div>
      </div>
    </aside>

    <!-- 主聊天区 -->
    <main class="flex-1 flex flex-col min-w-0">

      <!-- 顶部导航 -->
      <header class="flex-shrink-0 flex items-center justify-between px-5 py-4 border-b border-white/5 bg-[#111318]/80 backdrop-blur-xl">
        <div class="flex items-center gap-4">
          <button @click="$router.push('/square')" class="p-2 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-colors">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>

          <div v-if="currentCompanion" class="flex items-center gap-3">
            <div class="relative">
              <img
                :src="currentCompanion.avatar"
                :alt="currentCompanion.name"
                @error="handleAvatarError"
                class="w-10 h-10 rounded-xl object-cover"
              />
              <span class="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-400 rounded-full border-2 border-[#111318]"></span>
            </div>
            <div>
              <h2 class="text-sm font-semibold text-white leading-tight">{{ currentCompanion.name }}</h2>
              <p class="text-xs text-emerald-400">在线</p>
            </div>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <div v-if="currentCompanion" class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 text-xs text-slate-300">
            <svg class="w-3.5 h-3.5 text-pink-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
            <span>{{ currentCompanion.intimacy }}%</span>
          </div>
          <button
            @click="$router.push(`/settings/${currentCompanion?.id}`)"
            class="p-2 rounded-xl hover:bg-white/5 text-slate-400 hover:text-white transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"/>
            </svg>
          </button>
        </div>
      </header>

      <!-- 消息区域 -->
      <div class="flex-1 overflow-y-auto" ref="messagesContainer">
        <div class="max-w-3xl mx-auto px-4 py-6 space-y-4">

          <!-- 数据/落库异常提示（不打断聊天） -->
          <p
            v-if="dataWarning || chatStore.error"
            class="px-4 py-3 rounded-xl border border-amber-500/30 bg-amber-500/10 text-xs text-amber-300"
            role="alert"
          >
            {{ dataWarning || chatStore.error }}
          </p>

          <!-- 欢迎屏 -->
          <Transition name="welcome">
            <div v-if="chatStore.currentMessages.length === 0" class="flex flex-col items-center justify-center py-16 text-center select-none">
              <div class="w-20 h-20 rounded-3xl overflow-hidden mb-5 ring-2 ring-white/10 shadow-2xl">
                <img
                  v-if="currentCompanion"
                  :src="currentCompanion.avatar"
                  @error="handleAvatarError"
                  class="w-full h-full object-cover"
                />
              </div>
              <h3 class="text-xl font-semibold text-white mb-2">Hi，我是 {{ currentCompanion?.name }} ✨</h3>
              <p class="text-sm text-slate-400 max-w-xs leading-relaxed">{{ currentCompanion?.description || '很高兴认识你，有什么想聊的吗？' }}</p>

              <!-- 快捷建议 -->
              <div class="flex flex-wrap justify-center gap-2 mt-8">
                <button
                  v-for="s in dynamicSuggestions"
                  :key="s"
                  @click="useQuickReply(s)"
                  class="px-4 py-2 rounded-full bg-white/5 border border-white/10 text-sm text-slate-300 hover:bg-white/10 hover:border-violet-500/40 hover:text-white transition-all"
                >
                  {{ s }}
                </button>
              </div>
            </div>
          </Transition>

          <!-- 消息列表 -->
          <TransitionGroup name="msg">
            <div
              v-for="message in chatStore.currentMessages"
              :key="message.id"
              class="flex gap-3"
              :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
            >
              <!-- AI 头像 -->
              <div v-if="message.role === 'assistant'" class="flex-shrink-0 mt-1">
                <img
                  :src="currentCompanion?.avatar"
                  :alt="currentCompanion?.name"
                  @error="handleAvatarError"
                  class="w-8 h-8 rounded-xl object-cover ring-1 ring-white/10"
                />
              </div>

              <!-- 消息气泡 -->
              <div class="flex flex-col max-w-[72%]" :class="message.role === 'user' ? 'items-end' : 'items-start'">
                <div
                  class="px-4 py-3 rounded-2xl text-sm leading-relaxed"
                  :class="message.role === 'user'
                    ? 'bg-gradient-to-br from-violet-600 to-pink-500 text-white rounded-tr-sm shadow-lg shadow-violet-500/20'
                    : 'bg-[#1e2130] text-slate-100 rounded-tl-sm border border-white/5'"
                >
                  <!-- 图片附件 -->
                  <div v-if="message.images?.length" class="flex flex-wrap gap-2 mb-2">
                    <img
                      v-for="(img, idx) in message.images"
                      :key="idx"
                      :src="img"
                      class="max-w-[200px] max-h-[200px] rounded-xl object-cover cursor-pointer"
                      @click="openImagePreview(img)"
                    />
                  </div>
                  <p v-if="message.content" class="whitespace-pre-wrap break-words">{{ message.content }}</p>
                </div>
                <!-- 操作栏 (AI消息) -->
                <div v-if="message.role === 'assistant'" class="flex items-center gap-1 mt-1.5 px-1">
                  <button
                    @click="copyMessage(message.content)"
                    title="复制"
                    class="p-1.5 rounded-lg text-slate-600 hover:text-slate-300 hover:bg-white/5 transition-colors"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                    </svg>
                  </button>
                </div>
              </div>

              <!-- 用户头像 -->
              <div v-if="message.role === 'user'" class="flex-shrink-0 mt-1">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-pink-500 flex items-center justify-center ring-1 ring-white/10 shadow-md">
                  <span class="text-xs font-bold text-white">我</span>
                </div>
              </div>
            </div>
          </TransitionGroup>

          <!-- 流式输出气泡 / 打字指示器 -->
          <Transition name="typing">
            <div v-if="isTyping" class="flex gap-3 justify-start">
              <div class="flex-shrink-0 mt-1">
                <img
                  :src="currentCompanion?.avatar"
                  @error="handleAvatarError"
                  class="w-8 h-8 rounded-xl object-cover ring-1 ring-white/10"
                />
              </div>
              <div class="max-w-[72%] flex flex-col items-start">
                <div class="px-4 py-3 rounded-2xl rounded-tl-sm bg-[#1e2130] border border-white/5 text-sm text-slate-100 leading-relaxed">
                  <!-- 有流式内容时显示文字，否则显示dots -->
                  <p v-if="streamingContent" class="whitespace-pre-wrap break-words">{{ streamingContent }}<span class="inline-block w-0.5 h-4 bg-violet-400 ml-0.5 align-middle animate-blink"></span></p>
                  <div v-else class="flex items-center gap-1 h-5">
                    <span class="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style="animation-delay:0s"></span>
                    <span class="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style="animation-delay:0.15s"></span>
                    <span class="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style="animation-delay:0.3s"></span>
                  </div>
                </div>
              </div>
            </div>
          </Transition>

        </div>
      </div>

      <!-- 输入区 -->
      <div class="flex-shrink-0 px-4 pb-4 pt-3 border-t border-white/5 bg-[#111318]/80 backdrop-blur-xl">
        <div class="max-w-3xl mx-auto">
          <!-- 图片预览条 -->
          <div v-if="pendingImages.length" class="flex flex-wrap gap-2 mb-2 px-1">
            <div
              v-for="(img, idx) in pendingImages"
              :key="idx"
              class="relative group"
            >
              <img :src="img" class="w-16 h-16 rounded-xl object-cover border border-white/10" />
              <button
                @click="removeImage(idx)"
                class="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-slate-700 border border-white/20 text-slate-300 hover:bg-red-500/80 hover:text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all"
              >
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>

          <div
            class="flex items-end gap-2 px-3 py-3 rounded-2xl bg-[#1a1d26] border transition-all duration-200"
            :class="inputFocused ? 'border-violet-500/50 shadow-lg shadow-violet-500/10' : 'border-white/8'"
          >
            <!-- 图片上传按钮 -->
            <button
              @click="fileInputRef?.click()"
              :disabled="isTyping"
              title="上传图片"
              class="flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-slate-500 hover:text-slate-300 hover:bg-white/5 transition-colors"
            >
              <svg class="w-4.5 h-4.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="width:18px;height:18px">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
              </svg>
            </button>
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              multiple
              class="hidden"
              @change="handleFileSelect"
            />

            <textarea
              v-model="messageInput"
              ref="textareaRef"
              rows="1"
              :placeholder="`发消息给 ${currentCompanion?.name ?? 'TA'}…`"
              class="flex-1 bg-transparent resize-none text-sm text-white placeholder-slate-600 focus:outline-none leading-relaxed max-h-36 overflow-y-auto"
              @keydown.enter.exact.prevent="sendMessage"
              @keydown.enter.shift.exact="() => {}"
              @input="autoResize"
              @focus="inputFocused = true"
              @blur="inputFocused = false"
              @paste="handlePaste"
            ></textarea>

            <button
              @click="sendMessage"
              :disabled="(!messageInput.trim() && !pendingImages.length) || isTyping"
              class="flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center transition-all duration-200"
              :class="(messageInput.trim() || pendingImages.length) && !isTyping
                ? 'bg-gradient-to-br from-violet-600 to-pink-500 text-white hover:opacity-90 active:scale-95 shadow-lg shadow-violet-500/25'
                : 'bg-white/5 text-slate-600 cursor-not-allowed'"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 12h14M12 5l7 7-7 7"/>
              </svg>
            </button>
          </div>
          <p class="text-xs text-slate-600 text-center mt-2">Enter 发送 · Shift+Enter 换行 · 可粘贴图片</p>
        </div>
      </div>

      <!-- 图片全屏预览 -->
      <Transition name="img-preview">
        <div
          v-if="previewImage"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm"
          @click="previewImage = null"
        >
          <img :src="previewImage" class="max-w-[90vw] max-h-[90vh] rounded-2xl shadow-2xl object-contain" />
        </div>
      </Transition>

          <!-- RAG 开关 -->
      <div class="flex-shrink-0 border-t border-white/5 bg-[#111318]/60">
        <div class="px-4 py-2 flex items-center justify-between max-w-4xl mx-auto">
          <button 
            @click="enableRAG = !enableRAG"
            :class="enableRAG ? 'bg-violet-500/20 text-violet-400 border-violet-500/30' : 'bg-white/5 text-slate-500 border-white/10'"
            class="px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 border"
          >
            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/></svg>
            RAG 智能记忆
          </button>
          <span class="text-xs" :class="enableRAG ? 'text-violet-400' : 'text-slate-500'">
            {{ enableRAG ? '🧠 已启用 - AI将检索你的记忆和知识库' : '📝 基础模式 - 直接对话' }}
          </span>
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
import { useUserStore } from '@/stores/user'
import { createSvgAvatarDataUrl } from '@/lib/avatar'
import { uploadImage } from '@/lib/api'
import { useStreamingChat } from '@/composables/useStreamingChat'

const route = useRoute()
const router = useRouter()
const companionStore = useCompanionStore()
const chatStore = useChatStore()
const userStore = useUserStore()

const messageInput = ref('')
const isTyping = ref(false)
const inputFocused = ref(false)
const textareaRef = ref<HTMLTextAreaElement>()
const messagesContainer = ref<HTMLElement>()
const fileInputRef = ref<HTMLInputElement>()
const pendingImages = ref<string[]>([])
const previewImage = ref<string | null>(null)

const enableRAG = ref(true)

const { streamingContent, isStreaming, sendStreaming, fetchSuggestions, reset: resetStream } = useStreamingChat()

const companionId = computed(() => route.params.id as string)
const currentCompanion = computed(() => companionStore.getCompanionById(companionId.value))
const companionConversations = computed(() => chatStore.getConversationsByCompanion(companionId.value))

const DEFAULT_SUGGESTIONS = ['你好呀 👋', '今天过得怎么样？', '给我讲个笑话 😄', '陪我聊聊天']
const dynamicSuggestions = ref<string[]>([...DEFAULT_SUGGESTIONS])

const autoResize = () => {
  if (!textareaRef.value) return
  textareaRef.value.style.height = 'auto'
  textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 144) + 'px'
}

// Compress an image File/Blob to a base64 JPEG data URL (max 1024px, quality 0.85)
const compressImage = (file: File | Blob): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        const MAX = 1024
        let { width, height } = img
        if (width > MAX || height > MAX) {
          if (width > height) { height = Math.round(height * MAX / width); width = MAX }
          else { width = Math.round(width * MAX / height); height = MAX }
        }
        const canvas = document.createElement('canvas')
        canvas.width = width; canvas.height = height
        canvas.getContext('2d')!.drawImage(img, 0, 0, width, height)
        resolve(canvas.toDataURL('image/jpeg', 0.85))
      }
      img.onerror = reject
      img.src = e.target?.result as string
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

const addImagesFromFiles = async (files: FileList | File[]) => {
  const imageFiles = Array.from(files).filter(f => f.type.startsWith('image/'))
  for (const file of imageFiles.slice(0, 4 - pendingImages.value.length)) {
    const compressed = await compressImage(file)
    pendingImages.value.push(compressed)
  }
}

const handleFileSelect = (e: Event) => {
  const input = e.target as HTMLInputElement
  if (input.files?.length) addImagesFromFiles(input.files)
  input.value = ''
}

const handlePaste = async (e: ClipboardEvent) => {
  const items = Array.from(e.clipboardData?.items ?? [])
  const imageItems = items.filter(i => i.type.startsWith('image/'))
  if (!imageItems.length) return
  e.preventDefault()
  for (const item of imageItems.slice(0, 4 - pendingImages.value.length)) {
    const blob = item.getAsFile()
    if (blob) {
      const compressed = await compressImage(blob)
      pendingImages.value.push(compressed)
    }
  }
}

const removeImage = (index: number) => {
  pendingImages.value.splice(index, 1)
}

const openImagePreview = (src: string) => {
  previewImage.value = src
}

const refreshSuggestions = async () => {
  if (!currentCompanion.value || !chatStore.currentMessages.length) return
  const history = chatStore.currentMessages.slice(-6).map(m => ({ role: m.role, content: m.content }))
  const suggestions = await fetchSuggestions(
    currentCompanion.value.systemPrompt || '你是一个温柔体贴的AI伴侣。',
    history,
  )
  if (suggestions.length) dynamicSuggestions.value = suggestions
}

const scrollToBottom = (smooth = false) => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTo({
        top: messagesContainer.value.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto',
      })
    }
  })
}

const selectConversation = async (id: string) => {
  chatStore.selectConversation(id, companionId.value)
  scrollToBottom()
  try {
    await chatStore.loadMessages(id)
    scrollToBottom(true)
    if (chatStore.currentMessages.length) refreshSuggestions()
  } catch (e) {
    chatStore.error = `历史消息加载失败：${(e as Error).message}`
  }
}

/**
 * 新对话（懒创建）：只清空当前选择，不发请求。
 * 首次发送消息时才 POST /conversations，避免侧栏堆一堆空的「新对话」。
 */
const createNewConversation = () => {
  chatStore.startDraft()
  messageInput.value = ''
  pendingImages.value = []
  autoResize()
}

const deleteConversation = async (id: string) => {
  if (!confirm('删除这个对话？')) return
  try {
    await chatStore.deleteConversation(id)
    scrollToBottom()
  } catch (e) {
    chatStore.error = `删除对话失败：${(e as Error).message}`
  }
}

const useQuickReply = (text: string) => {
  messageInput.value = text
  sendMessage()
}

const handleAvatarError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (!img) return
  const name = currentCompanion.value?.name || 'AI'
  const label = name.trim().slice(-1) || 'AI'
  img.src = createSvgAvatarDataUrl({ seed: `${currentCompanion.value?.id}-${label}`, label })
}

/** 落库失败等非致命错误只在页面顶部提示，不打断聊天 */
const dataWarning = ref('')

/**
 * 把待发送的图片（base64）逐张上传到 Java 换 URL。
 * 图片双轨：base64 给 Python 视觉链路，URL 落 MySQL（message.images 只存 URL 数组）。
 */
const uploadPendingImages = async (images?: string[]): Promise<string[]> => {
  if (!images?.length) return []
  return Promise.all(images.map(src => (src.startsWith('data:') ? uploadImage(src) : src)))
}

// ── Core fix: single isTyping flag + streamingContent, no placeholder bubbles ──
const sendMessage = async () => {
  if ((!messageInput.value.trim() && !pendingImages.value.length) || isTyping.value || !currentCompanion.value) return

  const content = messageInput.value.trim()
  const images = pendingImages.value.length ? [...pendingImages.value] : undefined
  messageInput.value = ''
  pendingImages.value = []
  autoResize()

  isTyping.value = true
  resetStream()
  dataWarning.value = ''

  let assistantReply = ''

  try {
    // 懒创建：会话不存在时用首条消息做标题，只建一次
    const conversation = await chatStore.ensureConversation(
      companionId.value,
      chatStore.deriveTitle(content, images),
    )
    const conversationId = conversation.id

    chatStore.addMessage(conversationId, 'user', content, images)

    // 上传图片（失败不阻塞聊天：内存里仍用 base64 展示，只是这次不落 URL）
    let imageUrls: string[] = []
    try {
      imageUrls = await uploadPendingImages(images)
    } catch (uploadError) {
      dataWarning.value = `图片上传失败，本次消息的图片不会同步到服务端：${(uploadError as Error).message}`
    }
    scrollToBottom(true)

    const history = chatStore.currentMessages.slice(-13, -1).map(m => ({
      role: m.role,
      content: m.content,
      images: m.images,
    }))
    const systemPrompt = currentCompanion.value.systemPrompt || '你是一个温柔体贴的AI伴侣。'

    assistantReply = await sendStreaming(
      content,
      systemPrompt,
      history,
      () => scrollToBottom(),
      images,
      enableRAG.value,
      userStore.userId,
      companionId.value,
    )

    chatStore.addMessage(conversationId, 'assistant', assistantReply)

    // 流式结束后落库：user + assistant 两条，generate=false 只落库不调 AI（P0-5 方案 A）
    try {
      await chatStore.saveMessages(
        conversationId,
        { content, images: imageUrls },
        { content: assistantReply },
      )
    } catch (saveError) {
      dataWarning.value = `消息已显示，但保存到服务端失败（刷新后会丢失）：${(saveError as Error).message}`
    }

    // 亲密度失败不影响聊天
    companionStore.increaseIntimacy(companionId.value, 2).catch(() => undefined)

    // Refresh context-aware suggestions after each exchange
    refreshSuggestions()
  } catch (error) {
    console.error('AI 服务错误:', error)
    let errorMessage = 'AI 服务暂时不可用，请稍后再试。'

    if (error instanceof Error) {
      if (error.message.includes('AI 服务响应异常')) {
        errorMessage = 'AI 服务响应异常，请检查网络连接后重试。'
      } else if (error.message.includes('AI 流式响应解析失败')) {
        errorMessage = 'AI 响应解析失败，请重试。'
      } else if (error.message.includes('AI 未生成有效内容')) {
        errorMessage = 'AI 未生成有效内容，请尝试重新发送消息。'
      } else if (error.message.includes('建议服务响应异常')) {
        errorMessage = 'AI 建议服务暂时不可用，请稍后再试。'
      } else if (error.message.includes('AI 未返回有效的建议数据')) {
        errorMessage = 'AI 建议数据异常，请重试。'
      }
    }

    // 流式失败：把错误气泡显示出来，并只落 user 消息（assistant 没有内容可落）
    if (chatStore.currentConversationId) {
      chatStore.addMessage(chatStore.currentConversationId, 'assistant', errorMessage)
      try {
        const imageUrls = await uploadPendingImages(images).catch(() => [] as string[])
        await chatStore.saveMessage(chatStore.currentConversationId, 'user', content, imageUrls)
      } catch {
        // 落库失败不覆盖原始错误提示
      }
    } else {
      // 会话都没建成（Java 不可用）：把输入还原给用户，避免内容凭空消失
      messageInput.value = content
      pendingImages.value = images ? [...images] : []
      dataWarning.value = `无法创建对话：${error instanceof Error ? error.message : String(error)}`
    }
    companionStore.increaseIntimacy(companionId.value, 1).catch(() => undefined)
  } finally {
    isTyping.value = false
    resetStream()
    scrollToBottom(true)
  }
}

const generateFallbackReply = (userMessage: string): string => {
  const lowerMsg = userMessage.toLowerCase()
  if (['你好', 'hello', 'hi', '嗨'].some(k => lowerMsg.includes(k)))
    return '你好呀！很高兴见到你，有什么想聊的吗？ 💖'
  if (['开心', '高兴', '快乐'].some(k => lowerMsg.includes(k)))
    return '太棒了！看到你这么开心，我也跟着快乐起来了 ✨'
  if (['难过', '伤心', '郁闷', '烦'].some(k => lowerMsg.includes(k)))
    return '听到你这么说我很担心... 不过我会一直陪着你的，要不说说发生了什么？ 💙'
  const pool = ['我在这里陪着你呢，有什么想聊的都可以 💖', '嗯嗯，我在听～', '你说得很有道理呢！', '谢谢你愿意和我分享这些 ❤️']
  return pool[Math.floor(Math.random() * pool.length)]
}

const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
  } catch {
    // silent fail
  }
}

const formatDate = (date: Date) => {
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

/** 进入聊天页：补伴侣详情 → 拉该伴侣的会话 → 选中最近一条并加载消息 */
const initConversation = async () => {
  if (!companionStore.getCompanionById(companionId.value)) {
    const companion = await companionStore.loadCompanion(companionId.value)
    if (!companion) {
      router.push('/square')
      return
    }
  }
  try {
    await chatStore.loadConversations(companionId.value)
  } catch (e) {
    chatStore.error = `会话列表加载失败：${(e as Error).message}`
  }

  chatStore.setCompanionConversation(companionId.value)
  if (chatStore.currentConversationId) {
    await selectConversation(chatStore.currentConversationId)
  }
  scrollToBottom()
}

onMounted(() => {
  initConversation()
})

watch(companionId, async newId => {
  if (!newId || !companionStore.getCompanionById(newId)) return
  await chatStore.loadConversations(newId)
  chatStore.setCompanionConversation(newId)
  if (chatStore.currentConversationId) {
    await selectConversation(chatStore.currentConversationId)
  } else {
    scrollToBottom()
  }
})

watch(() => chatStore.currentMessages.length, () => scrollToBottom(true))
</script>

<style scoped>
/* Message entrance animation */
.msg-enter-active {
  transition: all 0.28s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.msg-enter-from {
  opacity: 0;
  transform: translateY(12px) scale(0.96);
}

/* Typing bubble */
.typing-enter-active { transition: all 0.2s ease-out; }
.typing-leave-active { transition: all 0.15s ease-in; }
.typing-enter-from, .typing-leave-to { opacity: 0; transform: translateY(6px); }

/* Welcome screen */
.welcome-enter-active { transition: all 0.4s ease-out; }
.welcome-leave-active { transition: all 0.2s ease-in; }
.welcome-enter-from, .welcome-leave-to { opacity: 0; transform: scale(0.97); }

/* Cursor blink */
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
.animate-blink { animation: blink 0.9s step-end infinite; }

/* Image full-screen preview */
.img-preview-enter-active { transition: all 0.2s ease-out; }
.img-preview-leave-active { transition: all 0.15s ease-in; }
.img-preview-enter-from, .img-preview-leave-to { opacity: 0; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 4px; }
</style>

