<template>
  <div class="history">
    <Navbar />

    <main class="history-main">
      <!-- 页头 -->
      <header class="page-head">
        <div class="page-head__row">
          <div>
            <p class="eyebrow">
              <MessageSquare :size="15" />
              CHAT HISTORY
            </p>
            <h1 class="page-title">聊天记录</h1>
            <p class="page-lead">
              所有对话按时间倒序。点进去可以接着聊，内容一条都不会丢。
            </p>
          </div>

          <div class="page-head__actions">
            <button
              type="button"
              class="btn btn-ghost"
              :disabled="!chatStore.conversations.length"
              @click="showClearConfirm = true"
            >
              <Trash2 :size="16" />
              清空历史
            </button>
            <button type="button" class="btn btn-primary" @click="router.push('/square')">
              <Plus :size="16" />
              开始新对话
            </button>
          </div>
        </div>
      </header>

      <!-- 筛选条 -->
      <div class="toolbar">
        <label class="search input-icon">
          <Search :size="17" />
          <input
            v-model="searchQuery"
            class="input"
            type="search"
            placeholder="搜索聊天记录..."
            aria-label="搜索聊天记录"
          />
          <button
            v-if="searchQuery"
            type="button"
            class="search__clear"
            aria-label="清空搜索"
            @click="searchQuery = ''"
          >
            <X :size="15" />
          </button>
        </label>

        <div class="toolbar__chips">
          <button
            v-for="option in timeOptions"
            :key="option.value"
            type="button"
            class="chip"
            :class="{ 'is-active': selectedTime === option.value }"
            @click="selectedTime = option.value"
          >
            {{ option.label }}
          </button>
        </div>

        <p class="toolbar__count">
          {{ toolbarCount }}
        </p>
      </div>

      <!-- 错误 -->
      <div v-if="chatStore.error" class="alert" role="alert">
        <AlertCircle :size="15" />
        {{ chatStore.error }}
      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="groups">
        <SkeletonBlock variant="row" :count="4" />
      </div>

      <!-- 列表 -->
      <div v-else-if="groupedConversations.length" class="groups">
        <section v-for="group in groupedConversations" :key="group.date" class="group">
          <h2 class="group__label">
            {{ group.date }}
            <span>{{ group.conversations.length }}</span>
          </h2>

          <MotionStagger :count="group.conversations.length">
            <div class="conv-list">
              <article
                v-for="conversation in group.conversations"
                :key="conversation.id"
                class="conv-card stagger-item"
                tabindex="0"
                @click="openConversation(conversation)"
                @keydown.enter="openConversation(conversation)"
              >
                <AvatarImage
                  :src="getCompanionAvatar(conversation.companionId)"
                  :name="getCompanionName(conversation.companionId)"
                  :seed="conversation.companionId"
                  size="md"
                />

                <div class="conv-card__copy">
                  <div class="conv-card__row">
                    <h3 class="conv-card__title">{{ conversation.title }}</h3>
                    <span class="conv-card__peer">
                      {{ getCompanionName(conversation.companionId) }}
                    </span>
                    <span class="conv-card__time">
                      {{ formatTime(conversation.updatedAt) }}
                    </span>
                  </div>

                  <p class="conv-card__preview">{{ getPreviewText(conversation) }}</p>

                  <div class="conv-card__meta">
                    <span class="tag">
                      <MessageSquare :size="12" />
                      {{ conversation.messages.length }} 条
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  class="conv-card__del"
                  aria-label="删除这个对话"
                  @click.stop="deleteConversation(conversation.id)"
                >
                  <Trash2 :size="15" />
                </button>

                <span class="conv-card__go" aria-hidden="true">
                  <ArrowRight :size="16" />
                </span>
              </article>
            </div>
          </MotionStagger>
        </section>
      </div>

      <!-- 空状态 -->
      <EmptyState
        v-else
        icon="message"
        :title="emptyTitle"
        :description="emptyDescription"
      >
        <button
          v-if="searchQuery || selectedTime !== 'all'"
          type="button"
          class="btn btn-ghost"
          @click="resetFilters"
        >
          清除筛选条件
        </button>
        <button type="button" class="btn btn-primary" @click="router.push('/square')">
          去挑一个伴侣
        </button>
      </EmptyState>
    </main>

    <!-- 清空确认 -->
    <ModalDialog
      v-model="showClearConfirm"
      title="清空所有聊天记录？"
      description="所有会话与消息都会被删除，无法撤销。你的记忆与情绪记录不受影响。"
      :width="460"
    >
      <p class="modal-warn">
        共 <strong>{{ chatStore.conversations.length }}</strong> 个会话将被删除。
      </p>

      <template #footer>
        <button type="button" class="btn btn-ghost" @click="showClearConfirm = false">
          取消
        </button>
        <button type="button" class="btn btn-danger" @click="clearAllHistory">
          确认清空
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AlertCircle,
  ArrowRight,
  MessageSquare,
  Plus,
  Search,
  Trash2,
  X,
} from 'lucide-vue-next'
import Navbar from '@/components/Navbar.vue'
import MotionStagger from '@/components/ui/MotionStagger.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import AvatarImage from '@/components/ui/AvatarImage.vue'
import ModalDialog from '@/components/ui/ModalDialog.vue'
import { useToast } from '@/composables/useToast'
import { useChatStore } from '@/stores/chat'
import { useCompanionStore } from '@/stores/companion'

const router = useRouter()
const chatStore = useChatStore()
const companionStore = useCompanionStore()
const toast = useToast()

const searchQuery = ref('')
const selectedTime = ref('all')
const showClearConfirm = ref(false)
/** 首屏加载态：数据未到时不渲染空态，避免「暂无聊天记录」先闪一下 */
const loading = ref(true)

const timeOptions = [
  { label: '全部时间', value: 'all' },
  { label: '今天', value: 'today' },
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' },
]

onMounted(async () => {
  // 历史页需要消息内容做预览与搜索，因此带 messages 拉全量。
  // 成功失败都置 false：失败时也要落到空态/错误提示，不能卡在「加载中」。
  loading.value = true
  try {
    await Promise.all([
      companionStore.loadCompanions(),
      chatStore.loadConversations(undefined, true),
    ])
  } finally {
    loading.value = false
  }
})

const filteredConversations = computed(() => {
  let conversations = [...chatStore.conversations].sort(
    (a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
  )

  // 搜索筛选
  if (searchQuery.value) {
    const keyword = searchQuery.value.toLowerCase()
    conversations = conversations.filter((conv) => {
      const titleMatch = conv.title.toLowerCase().includes(keyword)
      const messageMatch = conv.messages.some((msg) =>
        msg.content.toLowerCase().includes(keyword),
      )
      return titleMatch || messageMatch
    })
  }

  // 时间筛选
  const now = new Date()
  if (selectedTime.value === 'today') {
    conversations = conversations.filter(
      (conv) => new Date(conv.updatedAt).toDateString() === now.toDateString(),
    )
  } else if (selectedTime.value === 'week') {
    const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
    conversations = conversations.filter((conv) => new Date(conv.updatedAt) >= weekAgo)
  } else if (selectedTime.value === 'month') {
    const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
    conversations = conversations.filter((conv) => new Date(conv.updatedAt) >= monthAgo)
  }

  return conversations
})

const groupedConversations = computed(() => {
  const groups: { date: string; conversations: typeof chatStore.conversations }[] = []
  const today = new Date().toDateString()
  const yesterday = new Date(Date.now() - 86400000).toDateString()

  filteredConversations.value.forEach((conv) => {
    const convDate = new Date(conv.updatedAt).toDateString()
    let dateLabel = formatDateLabel(new Date(conv.updatedAt))

    if (convDate === today) dateLabel = '今天'
    else if (convDate === yesterday) dateLabel = '昨天'

    const existingGroup = groups.find((g) => g.date === dateLabel)
    if (existingGroup) {
      existingGroup.conversations.push(conv)
    } else {
      groups.push({ date: dateLabel, conversations: [conv] })
    }
  })

  return groups
})

const toolbarCount = computed(() => {
  const total = chatStore.conversations.length
  const shown = filteredConversations.value.length
  if (searchQuery.value || selectedTime.value !== 'all') {
    return `筛选出 ${shown} / ${total} 个会话`
  }
  return `共 ${total} 个会话`
})

const emptyTitle = computed(() => {
  if (searchQuery.value || selectedTime.value !== 'all') return '没有符合条件的对话'
  return '还没有聊天记录'
})

const emptyDescription = computed(() => {
  if (searchQuery.value || selectedTime.value !== 'all') {
    return '换个关键词，或者把时间范围放宽看看。'
  }
  return '挑一个伴侣聊几句，这里就会长起来。'
})

const resetFilters = () => {
  searchQuery.value = ''
  selectedTime.value = 'all'
}

const getCompanionName = (companionId: string) => {
  return companionStore.getCompanionById(companionId)?.name || '未知'
}

/** 伴侣头像地址；为空时 AvatarImage 会按 seed 生成首字兜底 */
const getCompanionAvatar = (companionId: string) => {
  return companionStore.getCompanionById(companionId)?.avatar || ''
}

/** 头像首字与色调已收进 AvatarImage 组件，这里不再需要 */

/**
 * 卡片摘要 = 首条**用户**消息，与标题同源。
 *
 * 历史版本取的是 `messages[最后一条]`，而聊天每轮都是 user → assistant 两条，
 * 最后一条必然是 AI 回复：摘要显示成 AI 的话，与取自首条用户消息的标题对不上，
 * 看起来像「串会话」，实际是取值口径错了。
 */
const getPreviewText = (conversation: typeof chatStore.conversations[0]) => {
  const firstUserMessage = conversation.messages.find((m) => m.role === 'user')
  const source = firstUserMessage?.content?.trim() || conversation.title
  if (!source) return '暂无消息'
  return source.length > 60 ? `${source.slice(0, 60)}...` : source
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

const deleteConversation = async (id: string) => {
  if (!confirm('确定要删除这个对话吗？')) return
  try {
    await chatStore.deleteConversation(id)
    toast.success('对话已删除')
  } catch (e) {
    chatStore.error = `删除对话失败：${(e as Error).message}`
  }
}

/** 清空历史 = 逐条 DELETE；失败的重试不掩盖成功项，最后给出汇总提示 */
const clearAllHistory = async () => {
  const targets = [...chatStore.conversations]
  const total = targets.length
  showClearConfirm.value = false
  let failed = 0
  for (const conv of targets) {
    try {
      await chatStore.deleteConversation(conv.id)
    } catch {
      failed += 1
    }
  }
  if (failed) {
    chatStore.error = `有 ${failed} 个对话删除失败，请稍后重试（其余已删除）`
    toast.error(`${failed} 个对话删除失败`)
  } else if (total > 0) {
    toast.success(`已清空 ${total} 个对话`)
  }
}
</script>

<style scoped>
.history {
  min-height: 100vh;
}

.history-main {
  width: min(920px, calc(100% - var(--gutter) * 2));
  margin: 0 auto;
  padding: var(--sp-14) 0 var(--sp-24);
}

/* ---------- 页头 ---------- */
.eyebrow {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0 0 13px;
  color: var(--accent);
  font-size: var(--fs-12);
  font-weight: 750;
}

.page-head__row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--sp-8);
  padding-bottom: var(--sp-8);
}

.page-title {
  margin: 0;
  color: var(--text-strong);
  font-size: clamp(30px, 4vw, var(--fs-34));
  font-weight: 760;
  line-height: var(--lh-tight);
}

.page-lead {
  margin: var(--sp-3) 0 0;
  max-width: 34em;
  color: var(--muted);
  font-size: var(--fs-14);
  line-height: var(--lh-body);
}

.page-head__actions {
  display: flex;
  flex-shrink: 0;
  gap: var(--sp-2);
}

/* ---------- 按钮 ---------- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 16px;
  border: 0;
  border-radius: var(--radius);
  font-size: var(--fs-13);
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--dur) var(--ease),
    border-color var(--dur) var(--ease),
    opacity var(--dur) var(--ease);
}

.btn-primary {
  color: var(--on-primary);
  background: var(--primary);
  box-shadow: var(--shadow-primary);
}

.btn-primary:hover {
  background: var(--primary-hover);
}

.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: var(--text);
  background: transparent;
}

.btn-ghost:hover {
  border-color: var(--line-strong);
  background: rgba(255, 255, 255, 0.04);
}

.btn-danger {
  border: 1px solid var(--primary-line);
  color: var(--primary);
  background: var(--danger-soft);
}

.btn-danger:hover {
  background: rgba(255, 139, 114, 0.16);
}

.btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ---------- 筛选条 ---------- */
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4) 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.search {
  position: relative;
  flex: 1 1 260px;
  max-width: 340px;
}

.input-icon > svg {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--muted-faint);
  pointer-events: none;
}

.input {
  width: 100%;
  min-height: 42px;
  padding: 10px 38px 10px 42px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-card);
  color: var(--text);
  background: var(--bg);
  font-size: var(--fs-13);
  transition:
    border-color var(--dur) var(--ease),
    box-shadow var(--dur) var(--ease);
}

.input::placeholder {
  color: var(--muted-faint);
}

.input:focus {
  outline: none;
  border-color: var(--accent-line);
  box-shadow: var(--ring-accent);
}

.search__clear {
  position: absolute;
  right: 8px;
  top: 50%;
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  color: var(--muted-faint);
  background: transparent;
  transform: translateY(-50%);
  cursor: pointer;
}

.search__clear:hover {
  color: var(--text);
}

.toolbar__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: transparent;
  font-size: var(--fs-13);
  white-space: nowrap;
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.chip:hover {
  color: var(--text-strong);
  border-color: var(--line-strong);
}

.chip.is-active {
  color: #171917;
  background: var(--bone);
  border-color: var(--bone);
  font-weight: 720;
}

.toolbar__count {
  margin: 0 0 0 auto;
  color: var(--muted-faint);
  font-size: var(--fs-13);
  white-space: nowrap;
}

/* ---------- 提示 ---------- */
.alert {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: var(--sp-4);
  padding: 11px 14px;
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--danger-soft);
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

/* ---------- 分组 ---------- */
.groups {
  display: flex;
  flex-direction: column;
  gap: var(--sp-7);
  padding-top: var(--sp-6);
}

.group__label {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  margin: 0 0 var(--sp-3);
  color: var(--muted-faint);
  font-size: var(--fs-12);
  font-weight: 650;
  letter-spacing: 0.04em;
}

.group__label span {
  display: inline-grid;
  min-width: 20px;
  height: 18px;
  padding: 0 5px;
  place-items: center;
  border-radius: var(--radius-pill);
  background: rgba(255, 255, 255, 0.06);
  color: var(--muted);
  font-size: var(--fs-11);
}

.conv-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

/* ---------- 会话卡 ---------- */
.conv-card {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-4);
  padding: var(--sp-4);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
  cursor: pointer;
  transition:
    border-color var(--dur-slow) var(--ease),
    background var(--dur-slow) var(--ease),
    transform var(--dur-slow) var(--ease);
}

.conv-card:hover {
  border-color: rgba(101, 216, 197, 0.36);
  background: var(--bg-raise);
  transform: translateX(2px);
}

.conv-card__copy {
  min-width: 0;
  flex: 1;
}

.conv-card__row {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 4px var(--sp-2);
}

.conv-card__title {
  margin: 0;
  min-width: 0;
  color: var(--text-strong);
  font-size: var(--fs-14);
  font-weight: 650;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-card__peer {
  color: var(--muted-faint);
  font-size: var(--fs-12);
  white-space: nowrap;
}

.conv-card__time {
  margin-left: auto;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.conv-card__preview {
  display: -webkit-box;
  overflow: hidden;
  margin: 6px 0 0;
  color: var(--muted);
  font-size: var(--fs-13);
  line-height: 1.65;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.conv-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--sp-3);
}

.tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 24px;
  padding: 0 8px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--muted-dim);
  font-size: var(--fs-12);
  white-space: nowrap;
}

.conv-card__del {
  display: grid;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  place-items: center;
  border: 0;
  border-radius: 50%;
  color: var(--muted-faint);
  background: transparent;
  opacity: 0;
  cursor: pointer;
  transition:
    opacity var(--dur) var(--ease),
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.conv-card:hover .conv-card__del {
  opacity: 1;
}

.conv-card__del:hover {
  color: var(--primary);
  background: var(--danger-soft);
}

.conv-card__go {
  display: grid;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 50%;
  color: var(--muted-faint);
  background: rgba(255, 255, 255, 0.04);
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.conv-card:hover .conv-card__go {
  color: #1b1e1b;
  background: var(--bone);
}

.modal-warn {
  margin: 0;
  color: var(--muted);
  font-size: var(--fs-14);
}

.modal-warn strong {
  color: var(--primary);
  font-weight: 700;
}

/* ---------- 响应式 ---------- */
@media (max-width: 760px) {
  .history-main {
    padding: var(--sp-10) 0 var(--sp-16);
  }

  .page-head__row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--sp-4);
  }

  .page-head__actions {
    width: 100%;
  }

  .page-head__actions > * {
    flex: 1;
  }

  .search {
    max-width: none;
  }

  .toolbar__count {
    display: none;
  }

  .conv-card {
    flex-wrap: wrap;
    gap: var(--sp-3);
  }

  .conv-card__copy {
    flex: 1 1 100%;
    order: 2;
  }

  .conv-card__del {
    order: 1;
    margin-left: auto;
    opacity: 1;
  }

  .conv-card__go {
    display: none;
  }
}
</style>
