<template>
  <div class="chat">
    <!-- ===== 左侧会话列表 ===== -->
    <aside class="chat-side">
      <div class="chat-side__head">
        <button type="button" class="chat-brand" @click="router.push('/square')">
          <span class="chat-brand__mark">
            <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path
                d="M20.8 5.6a5.4 5.4 0 0 0-7.6 0L12 6.8l-1.2-1.2a5.4 5.4 0 1 0-7.6 7.6L12 21l8.8-7.8a5.4 5.4 0 0 0 0-7.6Z"
              />
            </svg>
          </span>
          AI 伴侣
        </button>

        <button type="button" class="chat-new" @click="createNewConversation">
          <Plus :size="15" />
          新对话
        </button>
      </div>

      <div class="chat-list">
        <p class="chat-list__label">历史对话</p>

        <button
          v-for="conv in companionConversations"
          :key="conv.id"
          type="button"
          class="conv"
          :class="{ 'is-active': chatStore.currentConversationId === conv.id }"
          @click="selectConversation(conv.id)"
        >
          <span class="conv__dot" aria-hidden="true" />
          <span class="conv__copy">
            <span class="conv__title">{{ conv.title }}</span>
            <span class="conv__time">{{ formatDate(conv.updatedAt) }}</span>
          </span>
          <span
            class="conv__del"
            role="button"
            tabindex="0"
            aria-label="删除这个对话"
            @click.stop="deleteConversation(conv.id)"
            @keydown.enter.stop="deleteConversation(conv.id)"
          >
            <X :size="13" />
          </span>
        </button>

        <div v-if="!companionConversations.length" class="chat-list__empty">
          <MessageSquare :size="26" />
          <p>暂无对话记录</p>
        </div>
      </div>

      <div class="chat-side__foot">
        <AvatarImage
          :src="userStore.user?.avatar"
          :name="userStore.user?.name"
          :seed="userStore.user?.id || 'self'"
          size="sm"
        />
        <div class="chat-side__user">
          <p class="chat-side__name">{{ userStore.user?.name || '我' }}</p>
          <p class="chat-side__sub">已登录</p>
        </div>
        <button type="button" class="icon-btn" aria-label="我的空间" @click="router.push('/profile')">
          <Settings2 :size="17" />
        </button>
      </div>
    </aside>

    <!-- ===== 主区 ===== -->
    <main class="chat-main">
      <!-- 顶栏 -->
      <header class="chat-head">
        <button type="button" class="chat-back" aria-label="返回伴侣广场" @click="router.push('/square')">
          <ArrowLeft :size="18" />
        </button>

        <div class="chat-peer">
          <AvatarImage
            :src="currentCompanion?.avatar"
            :name="currentCompanion?.name"
            :seed="currentCompanion?.id || 'companion'"
            size="md"
          />
          <div class="chat-peer__copy">
            <p class="chat-peer__name">{{ currentCompanion?.name || '伴侣' }}</p>
            <p class="chat-peer__meta">
              <span class="chat-peer__dot" aria-hidden="true" />
              在线
              <span class="chat-peer__cat">· {{ currentCompanion?.category || '日常聊天' }}</span>
            </p>
          </div>
        </div>

        <div class="chat-head__right">
          <span v-if="currentCompanion" class="intimacy-pill">
            <ProgressRing :value="currentCompanion.intimacy" :size="26" :stroke="2.5" />
            默契 {{ currentCompanion.intimacy }}%
          </span>

          <button
            type="button"
            class="icon-btn"
            title="编辑伴侣人设"
            aria-label="编辑伴侣人设"
            @click="router.push({ path: '/create', query: { edit: currentCompanion?.id } })"
          >
            <SlidersHorizontal :size="17" />
          </button>

          <button
            type="button"
            class="icon-btn"
            title="随笔笔记"
            aria-label="随笔笔记"
            @click="router.push('/notes')"
          >
            <NotebookPen :size="17" />
          </button>
        </div>
      </header>

      <!-- 消息流 -->
      <div ref="messagesContainer" class="chat-stream">
        <div class="chat-stream__inner">
          <!-- 落库/上传等非致命提示 -->
          <div v-if="dataWarning || chatStore.error" class="chat-warn" role="alert">
            <AlertCircle :size="14" />
            {{ dataWarning || chatStore.error }}
          </div>

          <!-- 欢迎屏 -->
          <div v-if="!chatStore.currentMessages.length && !isTyping" class="chat-welcome">
            <AvatarImage
              :src="currentCompanion?.avatar"
              :name="currentCompanion?.name"
              :seed="currentCompanion?.id || 'companion'"
              size="xl"
            />
            <h2>Hi，我是 {{ currentCompanion?.name || '你的伴侣' }}</h2>
            <p>{{ currentCompanion?.description || '很高兴认识你，有什么想聊的吗？' }}</p>

            <div class="chat-welcome__suggests">
              <button
                v-for="s in dynamicSuggestions"
                :key="s"
                type="button"
                class="chip"
                @click="useQuickReply(s)"
              >
                {{ s }}
              </button>
            </div>
          </div>

          <!-- 消息 -->
          <TransitionGroup name="msg" tag="div" class="chat-msgs">
            <div
              v-for="(message, index) in chatStore.currentMessages"
              :key="message.id"
              class="msg"
              :class="message.role === 'user' ? 'msg--me' : 'msg--ai'"
            >
              <AvatarImage
                v-if="message.role === 'assistant'"
                :src="currentCompanion?.avatar"
                :name="currentCompanion?.name"
                :seed="currentCompanion?.id || 'companion'"
                size="sm"
              />

              <div class="msg__body">
                <p v-if="message.role === 'assistant'" class="msg__who">
                  {{ currentCompanion?.name || '伴侣' }}
                </p>

                <div class="msg__text">
                  <!-- 图片附件 -->
                  <div v-if="message.images?.length" class="msg__images">
                    <button
                      v-for="(img, idx) in message.images"
                      :key="idx"
                      type="button"
                      class="msg__image"
                      @click="openImagePreview(img)"
                    >
                      <img :src="img" alt="消息图片" />
                    </button>
                  </div>

                  <!-- 正文：最后一条 AI 消息用打字机，历史消息直出 -->
                  <TypewriterText
                    v-if="message.role === 'assistant' && message.content"
                    :text="message.content"
                    :enabled="isLastMessage(index) && shouldTypeLast"
                    :max-duration="1600"
                    @done="onTyped"
                  />
                  <p v-else-if="message.content" class="msg__plain">{{ message.content }}</p>
                </div>

                <!-- AI 消息操作 -->
                <div v-if="message.role === 'assistant' && message.content" class="msg__tools">
                  <button type="button" class="msg__tool" @click="copyMessage(message.content)">
                    <Copy :size="13" />
                    复制
                  </button>
                  <button
                    type="button"
                    class="msg__tool"
                    :disabled="savingNoteId === message.id"
                    @click="saveMessageAsNote(message)"
                  >
                    <NotebookPen :size="13" />
                    {{ savingNoteId === message.id ? '保存中…' : '存为笔记' }}
                  </button>
                </div>
              </div>
            </div>
          </TransitionGroup>

          <!-- 流式输出 / 等待 -->
          <div v-if="isTyping" class="msg msg--ai">
            <AvatarImage
              :src="currentCompanion?.avatar"
              :name="currentCompanion?.name"
              :seed="currentCompanion?.id || 'companion'"
              size="sm"
            />
            <div class="msg__body">
              <p class="msg__who">{{ currentCompanion?.name || '伴侣' }}</p>
              <div class="msg__text">
                <p v-if="streamingContent" class="msg__plain">
                  {{ streamingContent }}
                  <StreamingCursor />
                </p>
                <StreamingCursor v-else dots text="正在想" />
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="chat-composer">
        <div class="chat-composer__inner">
          <!-- 待发送图片 -->
          <div v-if="pendingImages.length" class="composer-images">
            <div v-for="(img, idx) in pendingImages" :key="idx" class="composer-image">
              <img :src="img" alt="待发送图片" />
              <button
                type="button"
                class="composer-image__del"
                aria-label="移除这张图片"
                @click="removeImage(idx)"
              >
                <X :size="11" />
              </button>
            </div>
          </div>

          <div class="composer-shell" :class="{ 'is-focused': inputFocused }">
            <button
              type="button"
              class="composer-ico"
              title="上传图片"
              aria-label="上传图片"
              :disabled="isTyping"
              @click="fileInputRef?.click()"
            >
              <ImagePlus :size="18" />
            </button>
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              multiple
              class="hidden-input"
              @change="handleFileSelect"
            />

            <textarea
              ref="textareaRef"
              v-model="messageInput"
              rows="1"
              :placeholder="`和 ${currentCompanion?.name ?? 'TA'} 说点什么…`"
              class="composer-input"
              @keydown.enter.exact.prevent="sendMessage"
              @keydown.enter.shift.exact="() => {}"
              @input="autoResize"
              @focus="inputFocused = true"
              @blur="inputFocused = false"
              @paste="handlePaste"
            />

            <button
              type="button"
              class="composer-send"
              aria-label="发送"
              :disabled="(!messageInput.trim() && !pendingImages.length) || isTyping"
              @click="sendMessage"
            >
              <Send :size="16" />
            </button>
          </div>

          <div class="composer-foot">
            <label class="composer-rag">
              <ToggleSwitch v-model="enableRAG" size="sm" label="知识库增强" />
              知识库增强（RAG）
            </label>
            <span class="composer-hint">Enter 发送 · Shift + Enter 换行 · 可粘贴图片</span>
          </div>
        </div>
      </div>
    </main>

    <!-- 图片全屏预览 -->
    <Transition name="fade">
      <div v-if="previewImage" class="img-preview" @click="previewImage = null">
        <img :src="previewImage" alt="预览图片" />
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompanionStore } from '@/stores/companion'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { useNoteStore } from '@/stores/note'
import { uploadImage } from '@/lib/api'
import { describeChatError } from '@/lib/chatError'
import { compressImage } from '@/lib/image'
import { useStreamingChat } from '@/composables/useStreamingChat'
import {
  AlertCircle,
  ArrowLeft,
  Copy,
  ImagePlus,
  MessageSquare,
  NotebookPen,
  Plus,
  Send,
  Settings2,
  SlidersHorizontal,
  X,
} from 'lucide-vue-next'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import StreamingCursor from '@/components/ui/StreamingCursor.vue'
import TypewriterText from '@/components/ui/TypewriterText.vue'
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import AvatarImage from '@/components/ui/AvatarImage.vue'
import { useToast } from '@/composables/useToast'
import type { Message } from '@/types'

const route = useRoute()
const router = useRouter()
const companionStore = useCompanionStore()
const chatStore = useChatStore()
const userStore = useUserStore()
const noteStore = useNoteStore()

const messageInput = ref('')
const isTyping = ref(false)
const inputFocused = ref(false)
const textareaRef = ref<HTMLTextAreaElement>()
const messagesContainer = ref<HTMLElement>()
const fileInputRef = ref<HTMLInputElement>()
const pendingImages = ref<string[]>([])
const previewImage = ref<string | null>(null)

const enableRAG = ref(true)
const toast = useToast()

/**
 * 最后一条 AI 消息是否用打字机。
 * 只在「刚流式结束的那一条」为真，历史消息直出，避免进页面时整屏都在打字。
 */
const shouldTypeLast = ref(false)

const isLastMessage = (index: number) => index === chatStore.currentMessages.length - 1

const onTyped = () => {
  shouldTypeLast.value = false
}

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

// 压缩逻辑已抽到 lib/image.ts（个人空间换头像也要用）

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
  shouldTypeLast.value = false
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
    toast.success('对话已删除')
    scrollToBottom()
  } catch (e) {
    chatStore.error = `删除对话失败：${(e as Error).message}`
  }
}

const useQuickReply = (text: string) => {
  messageInput.value = text
  sendMessage()
}

/** 伴侣头像首字与失败兜底已收进 AvatarImage 组件（按 seed 稳定生成），此处不再需要 */

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
    // 刚生成的这条用打字机补完，历史消息不受影响
    shouldTypeLast.value = true

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
    // 401/403/429/网络错误分别提示，避免把鉴权失败渲染成「检查网络」（P2-5 动作 2）
    const errorMessage = describeChatError(error)

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
    toast.success('已复制')
  } catch {
    toast.error('复制失败，请手动选择文本')
  }
}

/** 正在保存的那条消息 id，用于按钮置灰防重复点击 */
const savingNoteId = ref('')

/**
 * 把一条 AI 回复存为笔记。
 *
 * 标题不落库，由笔记页从正文首行派生（见 lib/note.ts）。
 * conversationId 是「从对话存下来」的唯一凭据，后端会校验归属当前用户。
 * 保存后不跳转，不打断当前对话。
 */
const saveMessageAsNote = async (message: Message) => {
  const conversationId = chatStore.currentConversationId
  if (!conversationId) {
    // 草稿态（还没发过消息）后端没有会话可挂，先提示，不静默丢 conversationId
    toast.info('先发一条消息，再保存为笔记')
    return
  }

  savingNoteId.value = message.id
  try {
    await noteStore.addNote({
      content: message.content,
      companionId: companionId.value,
      conversationId,
    })
    toast.success('已存为笔记，可在「随笔」里查看')
  } catch (e) {
    toast.error(`保存失败：${(e as Error).message}`)
  } finally {
    savingNoteId.value = ''
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
/* ==========================================================================
   对话页
   视觉：暗色暖调底 + 珊瑚橘主色 + 青绿点缀（与 SquarePage 同一套语言）
   ========================================================================== */

html,
body {
  height: 100%;
}

.chat {
  display: flex;
  height: 100vh;
  overflow: hidden;
  background: var(--bg);
}

/* ---------- 左侧会话列表 ---------- */
.chat-side {
  display: flex;
  width: 272px;
  flex-shrink: 0;
  flex-direction: column;
  border-right: 1px solid var(--line);
  background: var(--bg-soft);
}

.chat-side__head {
  padding: var(--sp-5) var(--sp-4) var(--sp-3);
}

.chat-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px var(--sp-4);
  border: 0;
  color: var(--text-strong);
  background: transparent;
  font-size: var(--fs-14);
  font-weight: 720;
  cursor: pointer;
}

.chat-brand__mark {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border-radius: 50%;
  color: #17120f;
  background: var(--primary);
}

.chat-brand__mark svg {
  width: 13px;
  height: 13px;
}

.chat-new {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  width: 100%;
  height: 40px;
  border: 0;
  border-radius: var(--radius);
  color: var(--on-primary);
  background: var(--primary);
  font-size: var(--fs-13);
  font-weight: 700;
  cursor: pointer;
  transition: background var(--dur) var(--ease);
}

.chat-new:hover {
  background: var(--primary-hover);
}

.chat-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-3) var(--sp-2) var(--sp-4);
}

.chat-list__label {
  margin: 0;
  padding: var(--sp-2) var(--sp-3);
  color: var(--muted-faint);
  font-size: var(--fs-12);
  letter-spacing: 0.05em;
}

/* 会话项 */
.conv {
  position: relative;
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 9px var(--sp-3);
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition:
    background var(--dur) var(--ease),
    color var(--dur) var(--ease);
}

.conv + .conv {
  margin-top: 1px;
}

.conv:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text);
}

.conv.is-active {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-strong);
}

.conv.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 9px;
  bottom: 9px;
  width: 2px;
  border-radius: 2px;
  background: var(--accent);
}

.conv__dot {
  width: 5px;
  height: 5px;
  flex-shrink: 0;
  border-radius: 50%;
  background: transparent;
  transition: background var(--dur) var(--ease);
}

.conv.is-active .conv__dot {
  background: var(--accent);
}

.conv__copy {
  min-width: 0;
  flex: 1;
}

.conv__title {
  display: block;
  overflow: hidden;
  font-size: var(--fs-13);
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv__time {
  display: block;
  margin-top: 1px;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.conv__del {
  display: grid;
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  place-items: center;
  border-radius: var(--radius-sm);
  color: var(--muted-faint);
  opacity: 0;
  cursor: pointer;
  transition:
    opacity var(--dur) var(--ease),
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.conv:hover .conv__del {
  opacity: 1;
}

.conv__del:hover {
  color: var(--primary);
  background: var(--danger-soft);
}

.chat-list__empty {
  display: grid;
  gap: var(--sp-2);
  padding: var(--sp-10) var(--sp-4);
  place-items: center;
  color: var(--muted-faint);
  text-align: center;
}

.chat-list__empty p {
  margin: 0;
  font-size: var(--fs-13);
}

.chat-side__foot {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-3) var(--sp-4);
  border-top: 1px solid var(--line);
}

.chat-side__user {
  min-width: 0;
  flex: 1;
}

.chat-side__name {
  margin: 0;
  overflow: hidden;
  color: var(--text);
  font-size: var(--fs-13);
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-side__sub {
  margin: 0;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.icon-btn {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  color: var(--muted);
  background: transparent;
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.icon-btn:hover {
  color: var(--text-strong);
  background: rgba(255, 255, 255, 0.06);
}

/* ---------- 主区 ---------- */
.chat-main {
  display: flex;
  flex: 1;
  min-width: 0;
  min-height: 0;
  flex-direction: column;
}

/* 顶栏 */
.chat-head {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  height: var(--topbar-h);
  flex-shrink: 0;
  padding: 0 var(--sp-6);
  border-bottom: 1px solid var(--line);
  background: rgba(17, 19, 17, 0.9);
  backdrop-filter: blur(18px);
}

.chat-back {
  display: grid;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  margin-left: -8px;
  place-items: center;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: transparent;
  cursor: pointer;
}

.chat-back:hover {
  color: var(--text-strong);
  background: rgba(255, 255, 255, 0.06);
}

.chat-peer {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  min-width: 0;
}

.chat-peer__copy {
  min-width: 0;
}

.chat-peer__name {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-14);
  font-weight: 700;
  line-height: 1.3;
}

.chat-peer__meta {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  white-space: nowrap;
}

.chat-peer__dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--success);
}

.chat-head__right {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-left: auto;
}

.intimacy-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 32px;
  padding: 0 12px 0 6px;
  border: 1px solid var(--line);
  border-radius: var(--radius-pill);
  color: var(--muted);
  font-size: var(--fs-12);
  white-space: nowrap;
}

/* 消息流 */
.chat-stream {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: var(--sp-8) var(--sp-6) var(--sp-6);
}

.chat-stream__inner {
  display: flex;
  max-width: 720px;
  margin: 0 auto;
  flex-direction: column;
  gap: var(--sp-5);
}

.chat-warn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border: 1px solid rgba(232, 189, 97, 0.32);
  border-radius: var(--radius);
  background: rgba(232, 189, 97, 0.08);
  color: var(--amber);
  font-size: var(--fs-12);
}

/* 欢迎屏 */
.chat-welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-12) 0 var(--sp-6);
  text-align: center;
}

.chat-welcome h2 {
  margin: var(--sp-2) 0 0;
  color: var(--text-strong);
  font-size: var(--fs-22);
  font-weight: 720;
}

.chat-welcome p {
  max-width: 28em;
  margin: 0;
  color: var(--muted);
  font-size: var(--fs-14);
  line-height: var(--lh-body);
}

.chat-welcome__suggests {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--sp-2);
  max-width: 520px;
  margin-top: var(--sp-2);
}

.chip {
  display: inline-flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: transparent;
  font-size: var(--fs-13);
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.chip:hover {
  color: var(--text-strong);
  border-color: var(--line-strong);
  background: rgba(255, 255, 255, 0.04);
}

/* 消息 */
.chat-msgs {
  display: flex;
  flex-direction: column;
  gap: var(--sp-5);
}

.msg {
  display: flex;
  gap: var(--sp-3);
  max-width: 82%;
}

.msg--me {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.msg__body {
  min-width: 0;
}

.msg__who {
  margin: 0 0 5px;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.msg--me .msg__who {
  text-align: right;
}

.msg__text {
  padding: 11px 15px;
  border-radius: var(--radius);
  font-size: var(--fs-14);
  line-height: 1.7;
}

.msg--ai .msg__text {
  border: 1px solid var(--line-soft);
  border-top-left-radius: 3px;
  color: var(--text);
  background: var(--bg-raise);
}

.msg--me .msg__text {
  border-top-right-radius: 3px;
  color: var(--text-strong);
  background: #2c3f3a;
}

.msg__plain {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg__images {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}

.msg__image {
  padding: 0;
  border: 0;
  border-radius: var(--radius-sm);
  background: transparent;
  overflow: hidden;
  cursor: zoom-in;
}

.msg__image img {
  display: block;
  max-width: 200px;
  max-height: 200px;
  object-fit: cover;
  transition: opacity var(--dur) var(--ease);
}

.msg__image:hover img {
  opacity: 0.86;
}

.msg__tools {
  display: flex;
  gap: var(--sp-1);
  margin-top: 6px;
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

.msg:hover .msg__tools {
  opacity: 1;
}

.msg__tool {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  padding: 0 8px;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--muted-faint);
  background: transparent;
  font-size: var(--fs-12);
  cursor: pointer;
}

.msg__tool:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.06);
}

/* 消息进入动画（只动 transform / opacity） */
.msg-enter-active {
  transition:
    opacity var(--dur-slow) var(--ease),
    transform var(--dur-slow) var(--ease);
}

.msg-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

/* ---------- 输入区 ---------- */
.chat-composer {
  flex-shrink: 0;
  padding: var(--sp-3) var(--sp-6) var(--sp-5);
  border-top: 1px solid var(--line);
  background: var(--bg);
}

.chat-composer__inner {
  max-width: 720px;
  margin: 0 auto;
}

.composer-images {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  margin-bottom: var(--sp-2);
}

.composer-image {
  position: relative;
}

.composer-image img {
  width: 60px;
  height: 60px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  object-fit: cover;
}

.composer-image__del {
  position: absolute;
  top: -6px;
  right: -6px;
  display: grid;
  width: 18px;
  height: 18px;
  place-items: center;
  border: 1px solid var(--line-strong);
  border-radius: 50%;
  color: var(--muted);
  background: var(--bg-raise);
  cursor: pointer;
}

.composer-image__del:hover {
  color: var(--primary);
  border-color: var(--primary-line);
}

.composer-shell {
  display: flex;
  align-items: flex-end;
  gap: var(--sp-2);
  padding: var(--sp-2) var(--sp-2) var(--sp-2) var(--sp-3);
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
  transition:
    border-color var(--dur) var(--ease),
    box-shadow var(--dur) var(--ease);
}

.composer-shell.is-focused {
  border-color: var(--accent-line);
  box-shadow: var(--ring-accent);
}

.composer-ico {
  display: grid;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  place-items: center;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--muted-faint);
  background: transparent;
  cursor: pointer;
}

.composer-ico:hover:not(:disabled) {
  color: var(--text);
  background: rgba(255, 255, 255, 0.06);
}

.composer-ico:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.hidden-input {
  display: none;
}

.composer-input {
  flex: 1;
  min-height: 34px;
  max-height: 148px;
  padding: 7px 0;
  border: 0;
  color: var(--text);
  background: transparent;
  font-size: var(--fs-14);
  line-height: 1.6;
  resize: none;
}

.composer-input::placeholder {
  color: var(--muted-faint);
}

.composer-input:focus {
  outline: none;
}

.composer-send {
  display: grid;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  place-items: center;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--on-primary);
  background: var(--primary);
  cursor: pointer;
  transition:
    background var(--dur) var(--ease),
    opacity var(--dur) var(--ease);
}

.composer-send:hover:not(:disabled) {
  background: var(--primary-hover);
}

.composer-send:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.composer-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
}

.composer-rag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--muted);
  font-size: var(--fs-12);
  cursor: pointer;
}

.composer-hint {
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

/* ---------- 图片预览 ---------- */
.img-preview {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: grid;
  place-items: center;
  padding: var(--sp-6);
  background: rgba(9, 11, 9, 0.86);
  cursor: zoom-out;
}

.img-preview img {
  max-width: 90vw;
  max-height: 90vh;
  border-radius: var(--radius-card);
  object-fit: contain;
  box-shadow: var(--shadow-lift);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--dur-slow) var(--ease);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ---------- 响应式 ---------- */
@media (max-width: 900px) {
  .chat-side {
    display: none;
  }

  .chat-head {
    padding: 0 var(--sp-4);
    gap: var(--sp-2);
  }

  .chat-peer__cat {
    display: none;
  }

  .intimacy-pill {
    display: none;
  }

  .chat-stream {
    padding: var(--sp-5) var(--sp-4) var(--sp-4);
  }

  .chat-composer {
    padding: var(--sp-3) var(--sp-4) var(--sp-4);
  }

  .msg {
    max-width: 92%;
  }

  .composer-hint {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .msg-enter-active,
  .fade-enter-active,
  .fade-leave-active {
    transition: none;
  }
}
</style>
