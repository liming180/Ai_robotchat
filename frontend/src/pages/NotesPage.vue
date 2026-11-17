<template>
  <div class="notes">
    <Navbar />

    <main class="notes-main">
      <!-- 页头 -->
      <header class="page-head">
        <div>
          <p class="eyebrow">
            <NotebookPen :size="15" />
            NOTES
          </p>
          <h1 class="page-title">我的笔记</h1>
          <p class="page-lead">
            从对话里留下的东西，以及你自己写的。标上标签就好找了。
          </p>
        </div>
        <p class="page-count">
          共 {{ noteStore.notes.length }} 条 · {{ Math.max(tags.length - 1, 0) }} 个标签
        </p>
      </header>

      <!-- 工具条 -->
      <div class="toolbar">
        <label class="search input-icon">
          <Search :size="17" />
          <input
            v-model="searchQuery"
            class="input"
            type="search"
            placeholder="搜索笔记..."
            aria-label="搜索笔记"
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

        <div class="toolbar__tags">
          <button
            v-for="tag in visibleTagChips"
            :key="tag"
            type="button"
            class="chip"
            :class="{ 'is-active': selectedTag === tag }"
            @click="selectedTag = tag"
          >
            {{ tag }}
          </button>
        </div>

        <button
          type="button"
          class="btn btn-primary toolbar__add"
          @click="toggleComposer"
        >
          <component :is="composerOpen ? X : Plus" :size="16" />
          {{ composerOpen ? '收起' : '写笔记' }}
        </button>
      </div>

      <!-- 写笔记：内联面板（对齐设计稿，比模态更适合本页节奏） -->
      <!-- maxHeight 要盖住面板实际高度（textarea 120 + 标签/伴侣行 + 底栏 ≈ 480px），否则展开会被裁 -->
      <CollapseTransition :max-height="720">
        <section v-if="composerOpen" ref="composerRef" class="write-panel" aria-labelledby="write-title">
          <div class="write-head">
            <h2 id="write-title">{{ editingNote ? '编辑笔记' : '写一条笔记' }}</h2>
            <button type="button" class="icon-btn" aria-label="收起面板" @click="closeComposer">
              <X :size="16" />
            </button>
          </div>

          <div class="write-body">
            <label class="field">
              <span>内容</span>
              <textarea
                ref="contentRef"
                v-model="editContent"
                class="textarea"
                rows="5"
                placeholder="记录你的想法... 第一行会作为标题"
                maxlength="2000"
              />
              <small>{{ editContent.length }} / 2000 · 首行作为标题，其余作为正文</small>
            </label>

            <div class="write-row">
              <label class="field">
                <span>标签</span>
                <input
                  v-model="editTags"
                  class="input input--plain"
                  type="text"
                  placeholder="用逗号分隔，如：温柔, 治愈"
                />
                <small>
                  最多 5 个{{ existingTagHint ? ` · 已有：${existingTagHint}` : '' }}
                </small>
              </label>

              <label class="field">
                <span>关联伴侣（可选）</span>
                <select v-model="editCompanionId" class="select">
                  <option value="">不关联</option>
                  <option
                    v-for="companion in companionOptions"
                    :key="companion.id"
                    :value="companion.id"
                  >
                    {{ companionOptionLabel(companion) }}
                  </option>
                </select>
              </label>
            </div>

            <p v-if="saveError" class="form-error" role="alert">
              <AlertCircle :size="15" />
              {{ saveError }}
            </p>
          </div>

          <div class="write-foot">
            <span class="small">
              {{ editingNote ? '改完立刻生效。' : '也可以从对话里直接「存为笔记」。' }}
            </span>
            <div class="btns">
              <button type="button" class="btn btn-ghost" :disabled="saving" @click="closeComposer">
                取消
              </button>
              <button
                type="button"
                class="btn btn-primary"
                :disabled="!canSave"
                @click="saveNote"
              >
                {{ saving ? '保存中…' : '保存' }}
              </button>
            </div>
          </div>
        </section>
      </CollapseTransition>

      <!-- 错误 -->
      <div v-if="noteStore.error" class="alert" role="alert">
        <AlertCircle :size="15" />
        {{ noteStore.error }}
      </div>

      <!-- 加载中 -->
      <div v-if="noteStore.loading" class="note-grid">
        <SkeletonBlock variant="card" :count="4" />
      </div>

      <!-- 笔记列表 -->
      <MotionStagger v-else-if="filteredNotes.length" :count="filteredNotes.length">
        <div class="note-grid">
          <article
            v-for="note in filteredNotes"
            :key="note.id"
            class="note-card stagger-item"
          >
            <!-- 顶行：来源标记 + 相对日期 -->
            <div class="note-card__top">
              <span class="note-card__kind" :class="{ 'is-ai': isFromChat(note) }">
                <Sparkles v-if="isFromChat(note)" :size="11" />
                {{ isFromChat(note) ? 'AI 生成' : '随笔' }}
              </span>
              <span class="note-card__date">{{ formatDate(note.updatedAt) }}</span>
            </div>

            <!-- 标题：从正文首行派生，无标题则省略 -->
            <h3 v-if="partsOf(note).title" class="note-card__title">
              {{ partsOf(note).title }}
            </h3>

            <!-- 正文：AI 生成用引用块（左侧引导线），手动写用普通段落 -->
            <template v-if="partsOf(note).body">
              <blockquote v-if="isFromChat(note)" class="note-card__quote">
                {{ partsOf(note).body }}
              </blockquote>
              <p v-else class="note-card__body">{{ partsOf(note).body }}</p>
            </template>

            <!-- 来源行：纯文本，不做链接（跳错会话的假链接比没有更糟） -->
            <p v-if="sourceLine(note)" class="note-card__source">
              <MessageSquare :size="12" />
              {{ sourceLine(note) }}
            </p>

            <div class="note-card__foot">
              <div class="note-card__tags">
                <span v-for="tag in note.tags" :key="tag" class="tag">{{ tag }}</span>
              </div>

              <div class="note-card__acts">
                <button
                  type="button"
                  class="note-card__act"
                  aria-label="编辑笔记"
                  @click="openComposer(note)"
                >
                  <Pencil :size="14" />
                </button>
                <button
                  type="button"
                  class="note-card__act note-card__act--danger"
                  :disabled="deletingId === note.id"
                  aria-label="删除笔记"
                  @click="deleteNote(note.id)"
                >
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </article>
        </div>
      </MotionStagger>

      <!-- 空状态 -->
      <EmptyState
        v-else
        icon="notebook"
        :title="emptyTitle"
        :description="emptyDescription"
      >
        <button
          v-if="searchQuery || selectedTag !== '全部'"
          type="button"
          class="btn btn-ghost"
          @click="resetFilters"
        >
          清除筛选条件
        </button>
        <button type="button" class="btn btn-primary" @click="openComposer()">
          写第一条笔记
        </button>
      </EmptyState>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import {
  AlertCircle,
  MessageSquare,
  NotebookPen,
  Pencil,
  Plus,
  Search,
  Sparkles,
  Trash2,
  X,
} from 'lucide-vue-next'
import Navbar from '@/components/Navbar.vue'
import CollapseTransition from '@/components/ui/CollapseTransition.vue'
import MotionStagger from '@/components/ui/MotionStagger.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { useToast } from '@/composables/useToast'
import { useNoteStore } from '@/stores/note'
import { useCompanionStore } from '@/stores/companion'
import { splitNoteContent } from '@/lib/note'
import type { Note } from '@/types'

const noteStore = useNoteStore()
const companionStore = useCompanionStore()
const toast = useToast()

const searchQuery = ref('')
const selectedTag = ref('全部')
/** 写笔记内联面板是否展开 */
const composerOpen = ref(false)
/** 非空表示编辑现有笔记，空表示新增 */
const editingNote = ref<Note | null>(null)
const editContent = ref('')
const editTags = ref('')
/** 新增/编辑共用；空串表示「不关联」 */
const editCompanionId = ref('')
const saving = ref(false)
const saveError = ref('')
const deletingId = ref('')

const composerRef = ref<HTMLElement>()
const contentRef = ref<HTMLTextAreaElement>()

const isFromChat = (note: Note) => Boolean(note.conversationId)

/** 标题/正文拆分的缓存键：内容变则重算，避免每帧都 split */
const partsCache = new Map<string, { title: string; body: string }>()
const partsOf = (note: Note) => {
  const key = `${note.id}::${note.content}`
  let parts = partsCache.get(key)
  if (!parts) {
    parts = splitNoteContent(note.content)
    // 简单上限，防止长时间停留累积
    if (partsCache.size > 200) partsCache.clear()
    partsCache.set(key, parts)
  }
  return parts
}

/** 来源行文案；不关联也未从对话来的笔记不显示来源行 */
const sourceLine = (note: Note) => {
  const name = note.companionId ? getCompanionName(note.companionId) : ''
  if (note.conversationId) {
    return name ? `来自和${name}的对话 · 由伴侣生成` : '来自和伴侣的对话 · 由伴侣生成'
  }
  return name ? `记在${name}名下` : ''
}

const filteredNotes = computed(() => {
  let notes = noteStore.notes

  if (selectedTag.value !== '全部') {
    notes = noteStore.filterByTag(selectedTag.value)
  }

  if (searchQuery.value) {
    notes = noteStore.searchNotes(searchQuery.value)
  }

  return notes
})

const tags = computed(() => ['全部', ...noteStore.allTags])

/** 工具条最多 6 个 chip（含「全部」） */
const visibleTagChips = computed(() => tags.value.slice(0, 6))

/** 表单里提示已有标签，排除「全部」这个伪标签 */
const existingTagHint = computed(() => noteStore.allTags.slice(0, 6).join('、'))

/** 可以记笔记的伴侣：全部可见伴侣（预置伴侣也允许，笔记是用户自己的内容） */
const companionOptions = computed(() => companionStore.companions)

const emptyTitle = computed(() =>
  searchQuery.value || selectedTag.value !== '全部' ? '没有找到匹配的笔记' : '还没有笔记',
)

const emptyDescription = computed(() =>
  searchQuery.value || selectedTag.value !== '全部'
    ? '换个关键词，或者看看其他标签。'
    : '聊到值得留下的句子，就从对话里存一条；也可以直接写。',
)

const resetFilters = () => {
  searchQuery.value = ''
  selectedTag.value = '全部'
}

const getCompanionName = (id: string) => {
  const companion = companionStore.getCompanionById(id)
  return companion?.name || ''
}

/** 下拉选项文案：带描述前缀区分同名伴侣（如两个「小智」），描述超 12 字截断 */
const companionOptionLabel = (companion: { name: string; description: string }) => {
  const desc = companion.description.trim()
  if (!desc) return companion.name
  const brief = desc.length > 12 ? `${desc.slice(0, 12)}…` : desc
  return `${companion.name} · ${brief}`
}

onMounted(async () => {
  await Promise.all([noteStore.loadNotes(), companionStore.loadCompanions()])
})

/** 与 CollapseTransition 的展开时长（--dur-slow 200ms）对齐，留 60ms 余量 */
const COLLAPSE_DURATION_MS = 260

/**
 * 展开动画结束后把面板完整滚进视口。
 *
 * 首次 scrollIntoView 发生在 nextTick，此刻面板高度≈0（刚从 max-height:0 开始展开），
 * 浏览器判定「无需滚动」；动画撑到全高后底部（下拉/保存按钮）会留在视口外。
 *
 * **不能用 transitionend 监听 .collapse-box**：面板内输入框自带
 * `transition: border-color, box-shadow`，openComposer 又会在 nextTick 里 focus，
 * 聚焦触发的 box-shadow 过渡（160ms）会冒泡到 .collapse-box，比展开动画（200ms）更早，
 * `{ once: true }` 把它消费掉后补滚发生在面板仍矮的时刻，等于没修。
 * 因此只用定时器，时长与 --dur-slow 对齐。
 */
const scrollComposerIntoViewAfterExpand = () => {
  window.setTimeout(() => {
    // 面板已收起（v-if 卸载、ref 置空）就不再滚动
    if (!composerRef.value) return
    // block:'start' + scroll-margin-top（见 .write-panel 样式）保证顶部不被 sticky Navbar 遮住
    composerRef.value.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, COLLAPSE_DURATION_MS)
}

/** 打开内联面板：不传 note 为新增 */
const openComposer = (note?: Note) => {
  editingNote.value = note ?? null
  editContent.value = note?.content ?? ''
  editTags.value = note?.tags.join(', ') ?? ''
  // 新增默认「不关联」：随手的笔记不该被迫挂到某个伴侣名下
  editCompanionId.value = note?.companionId ?? ''
  saveError.value = ''
  composerOpen.value = true
  // 等面板渲染完再聚焦，否则 ref 还是 undefined
  nextTick(() => {
    contentRef.value?.focus()
    // 展开动画结束后再滚动，保证下拉与保存按钮可见（验收清单第 9 条）。
    // 不再在 nextTick 里先滚一次：此刻面板高度≈0，scrollIntoView 是空操作。
    scrollComposerIntoViewAfterExpand()
  })
}

/** 工具条按钮：展开时收起，收起时打开新增 */
const toggleComposer = () => {
  if (composerOpen.value) closeComposer()
  else openComposer()
}

const closeComposer = () => {
  if (saving.value) return
  composerOpen.value = false
  editingNote.value = null
  saveError.value = ''
}

const canSave = computed(
  () => Boolean(editContent.value.trim()) && !saving.value,
)

/** 逗号分隔文本 → 去空去重的标签数组，最多 5 个（与表单提示一致） */
const parseTagInput = (raw: string) =>
  [...new Set(
    raw
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t),
  )].slice(0, 5)

const saveNote = async () => {
  if (!canSave.value) return
  saving.value = true
  saveError.value = ''
  const tagList = parseTagInput(editTags.value)
  const isEdit = Boolean(editingNote.value)

  try {
    if (editingNote.value) {
      // 空串传下去表示「解除关联」，undefined 才是不修改
      await noteStore.updateNote(editingNote.value.id, {
        content: editContent.value,
        tags: tagList,
        companionId: editCompanionId.value,
      })
    } else {
      await noteStore.addNote({
        content: editContent.value,
        tags: tagList,
        // 空串不传，后端按「不关联」处理
        companionId: editCompanionId.value || undefined,
      })
    }
    composerOpen.value = false
    editingNote.value = null
    toast.success(isEdit ? '笔记已更新' : '笔记已保存')
  } catch (e) {
    saveError.value = `保存失败：${(e as Error).message}`
    toast.error('保存失败，请重试')
  } finally {
    saving.value = false
  }
}

const deleteNote = async (id: string) => {
  if (!confirm('确定要删除这条笔记吗？删除后不可恢复。')) return
  deletingId.value = id
  try {
    await noteStore.deleteNote(id)
    toast.success('笔记已删除')
    // 删的正是正在编辑的那条，顺手收起面板，避免对着已删笔记继续编辑
    if (editingNote.value?.id === id) closeComposer()
  } catch (e) {
    toast.error(`删除失败：${(e as Error).message}`)
  } finally {
    deletingId.value = ''
  }
}

const pad2 = (n: number) => String(n).padStart(2, '0')

/**
 * 相对日期：今天 14:41 / 昨天 23:22 / 11-14
 * 跨年的时间信息不能省，否则「11-14」会歧义，所以非当年补上年份。
 */
const formatDate = (date: Date) => {
  const d = new Date(date)
  if (Number.isNaN(d.getTime())) return ''

  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const startOfTarget = new Date(d.getFullYear(), d.getMonth(), d.getDate())
  const dayDiff = Math.round((startOfToday.getTime() - startOfTarget.getTime()) / 86400000)

  const time = `${pad2(d.getHours())}:${pad2(d.getMinutes())}`
  if (dayDiff === 0) return `今天 ${time}`
  if (dayDiff === 1) return `昨天 ${time}`

  const monthDay = `${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`
  return d.getFullYear() === now.getFullYear() ? monthDay : `${d.getFullYear()}-${monthDay}`
}
</script>

<style scoped>
.notes {
  min-height: 100vh;
}

.notes-main {
  width: min(1100px, calc(100% - var(--gutter) * 2));
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

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--sp-8);
  padding-bottom: var(--sp-6);
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

.page-count {
  margin: 0;
  flex-shrink: 0;
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

/* ---------- 工具条 ---------- */
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4) 0;
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  margin-bottom: var(--sp-6);
}

.search {
  position: relative;
  flex: 1 1 240px;
  max-width: 320px;
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

/* 表单里的纯文本框不需要搜索框那样的左右留白 */
.input--plain {
  padding: 10px 14px;
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

.toolbar__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.toolbar__add {
  margin-left: auto;
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

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: var(--text);
  background: transparent;
}

.btn-ghost:hover:not(:disabled) {
  border-color: var(--line-strong);
  background: rgba(255, 255, 255, 0.04);
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.icon-btn {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--muted-faint);
  background: transparent;
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.icon-btn:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.06);
}

/* ---------- 提示 ---------- */
.alert {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--sp-4);
  padding: 11px 14px;
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--danger-soft);
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

.small {
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

/* ---------- 写笔记内联面板 ---------- */
.write-panel {
  /* 面板顶部与 sticky Navbar 之间留出呼吸位，避免 scrollIntoView 把首行送到导航栏底下 */
  scroll-margin-top: calc(var(--topbar-h) + var(--sp-4));
  margin-bottom: var(--sp-6);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.write-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--line);
}

.write-head h2 {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-16);
  font-weight: 650;
}

.write-body {
  padding: var(--sp-5);
}

.write-body .field + .field {
  margin-top: var(--sp-4);
}

.write-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: var(--sp-4);
  margin-top: var(--sp-4);
}

/* write-row 内的 field 自带 margin，会与 grid gap 叠加，去掉 */
.write-row .field + .field {
  margin-top: 0;
}

.write-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: var(--sp-4) var(--sp-5);
  border-top: 1px solid var(--line);
  background: var(--bg-raise);
}

.write-foot .btns {
  display: flex;
  gap: var(--sp-2);
}

/* ---------- 表单 ---------- */
.field {
  display: block;
}

.field > span {
  display: block;
  margin-bottom: var(--sp-2);
  color: var(--text);
  font-size: var(--fs-13);
  font-weight: 650;
}

.field > small {
  display: block;
  margin-top: 7px;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.textarea,
.select {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-card);
  color: var(--text);
  background: var(--bg);
  font-size: var(--fs-14);
  line-height: 1.75;
  transition:
    border-color var(--dur) var(--ease),
    box-shadow var(--dur) var(--ease);
}

.textarea {
  min-height: 120px;
  resize: vertical;
}

.select {
  min-height: 46px;
  appearance: none;
  background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' stroke='%23aaa9a2' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m4 6.5 4 4 4-4'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding-right: 38px;
}

.textarea::placeholder,
.select:invalid {
  color: var(--muted-faint);
}

.textarea:focus,
.select:focus {
  outline: none;
  border-color: var(--accent-line);
  box-shadow: var(--ring-accent);
}

.form-error {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: var(--sp-4);
  padding: 10px 12px;
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--danger-soft);
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

/* ---------- 笔记网格 ---------- */
.note-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sp-4);
}

.note-card {
  display: flex;
  flex-direction: column;
  padding: var(--sp-5);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
  box-shadow: var(--shadow-card);
  transition:
    border-color var(--dur-slow) var(--ease),
    background var(--dur-slow) var(--ease);
}

.note-card:hover {
  border-color: var(--line-strong);
  background: var(--bg-raise);
}

.note-card__top {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-bottom: var(--sp-3);
}

.note-card__kind {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 22px;
  padding: 0 8px;
  border-radius: var(--radius-pill);
  color: var(--muted);
  background: var(--bg-raise);
  font-size: var(--fs-12);
  white-space: nowrap;
}

/* AI 来源：青绿点缀，与手动笔记的灰胶囊区分 */
.note-card__kind.is-ai {
  color: var(--accent);
  background: var(--accent-soft);
}

.note-card__date {
  margin-left: auto;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  font-variant-numeric: tabular-nums;
}

.note-card__title {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-16);
  font-weight: 650;
  line-height: 1.4;
  letter-spacing: -0.005em;
}

.note-card__body {
  margin: var(--sp-2) 0 0;
  max-height: calc(1.75em * 4);
  overflow: hidden;
  color: var(--muted);
  font-size: var(--fs-14);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 引用式：AI 生成的内容带左侧引导线 */
.note-card__quote {
  margin: var(--sp-3) 0 0;
  padding-left: var(--sp-3);
  border-left: 2px solid var(--line-strong);
  max-height: calc(1.75em * 4);
  overflow: hidden;
  color: var(--text);
  font-size: var(--fs-14);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.note-card__source {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 24px;
  margin: var(--sp-3) 0 0;
  color: var(--muted);
  font-size: var(--fs-12);
}

.note-card__foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: auto;
  padding-top: var(--sp-4);
}

.note-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.tag {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 8px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--muted-dim);
  font-size: var(--fs-12);
  white-space: nowrap;
}

.note-card__acts {
  display: flex;
  gap: 2px;
  margin-left: auto;
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

.note-card:hover .note-card__acts {
  opacity: 1;
}

.note-card__act {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--muted-faint);
  background: transparent;
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.note-card__act:hover:not(:disabled) {
  color: var(--text);
  background: rgba(255, 255, 255, 0.06);
}

.note-card__act--danger:hover:not(:disabled) {
  color: var(--primary);
  background: var(--danger-soft);
}

.note-card__act:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ---------- 响应式 ---------- */
@media (max-width: 1024px) {
  .note-grid {
    grid-template-columns: 1fr;
  }

  .page-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar__add {
    margin-left: 0;
  }

  .write-row {
    grid-template-columns: 1fr;
  }

  .write-row .field + .field {
    margin-top: var(--sp-4);
  }
}

@media (max-width: 760px) {
  .notes-main {
    padding: var(--sp-10) 0 var(--sp-16);
  }

  .page-head {
    gap: var(--sp-3);
  }

  .search {
    max-width: none;
  }

  .toolbar__add {
    width: 100%;
  }

  .note-card__acts {
    opacity: 1;
  }

  /* 窄屏放宽正文行数，避免截掉太多 */
  .note-card__body,
  .note-card__quote {
    max-height: calc(1.75em * 6);
  }
}
</style>
