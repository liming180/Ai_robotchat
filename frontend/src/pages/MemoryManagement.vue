<template>
  <div class="memory">
    <Navbar />

    <main class="memory-main">
      <!-- 页头 -->
      <header class="page-head">
        <div>
          <p class="eyebrow">
            <Brain :size="15" />
            MEMORY
          </p>
          <h1 class="page-title">记忆管理</h1>
          <p class="page-lead">
            伴侣在对话里记住的关于你的事。都可以改，也可以删——删掉之后它就不再引用。
          </p>
        </div>
        <p class="page-count">
          共 {{ totalCount }} 条
        </p>
      </header>

      <!-- 错误 -->
      <div v-if="error" class="alert" role="alert">
        <AlertCircle :size="15" />
        {{ error }}
      </div>

      <!-- 分类条 -->
      <div class="cat-strip">
        <button type="button" class="cat-item" :class="{ 'is-active': selectedCategory === 'all' }" @click="selectedCategory = 'all'">
          <span class="cat-item__label">
            <Layers :size="15" />
            全部
          </span>
          <strong class="cat-item__value">{{ totalCount }}<i>条</i></strong>
        </button>

        <button
          v-for="category in memoryCategories"
          :key="category.id"
          type="button"
          class="cat-item"
          :class="{ 'is-active': selectedCategory === category.id }"
          @click="selectedCategory = category.id"
        >
          <span class="cat-item__label">
            <component :is="categoryIcon(category.id)" :size="15" />
            {{ category.name }}
          </span>
          <strong class="cat-item__value">
            {{ getMemoryCount(category.id) }}<i>条</i>
          </strong>
        </button>
      </div>

      <!-- 工具条 -->
      <div class="toolbar">
        <label class="search input-icon">
          <Search :size="17" />
          <input
            v-model="searchQuery"
            class="input"
            type="search"
            placeholder="搜索记忆..."
            aria-label="搜索记忆"
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

        <p class="toolbar__count">
          {{ filteredMemories.length }} / {{ totalCount }} 条
        </p>

        <button type="button" class="btn btn-primary toolbar__add" @click="openAddForm">
          <Plus :size="16" />
          新增记忆
        </button>
      </div>

      <!-- 新增 / 编辑面板 -->
      <CollapseTransition :max-height="320">
        <section v-if="showForm" class="form-panel">
          <h2 class="form-panel__title">{{ editingId ? '编辑记忆' : '新增记忆' }}</h2>

          <div class="form-panel__row">
            <label class="field form-panel__type">
              <span>类型</span>
              <select v-model="newMemory.type" class="select">
                <option v-for="category in memoryCategories" :key="category.id" :value="category.id">
                  {{ category.name }}
                </option>
              </select>
            </label>

            <label class="field form-panel__content">
              <span>内容</span>
              <input
                v-model="newMemory.content"
                class="input"
                type="text"
                placeholder="输入要记住的内容..."
                maxlength="200"
                @keydown.enter="saveMemory"
              />
            </label>
          </div>

          <p v-if="saveError" class="form-panel__error" role="alert">{{ saveError }}</p>

          <div class="form-panel__foot">
            <span class="small">
              保存后会立刻参与对话检索，不需要重新开始会话。
            </span>
            <div class="form-panel__actions">
              <button type="button" class="btn btn-ghost" :disabled="saving" @click="cancelForm">
                取消
              </button>
              <button
                type="button"
                class="btn btn-primary"
                :disabled="!newMemory.content.trim() || saving"
                @click="saveMemory"
              >
                {{ saving ? '保存中…' : '保存' }}
              </button>
            </div>
          </div>
        </section>
      </CollapseTransition>

      <!-- 加载中 -->
      <SkeletonBlock v-if="loading" variant="row" :count="4" />

      <!-- 记忆列表 -->
      <MotionStagger v-else-if="filteredMemories.length" :count="filteredMemories.length">
        <div class="mem-list">
          <article
            v-for="memory in filteredMemories"
            :key="memory.id"
            class="mem-item stagger-item"
          >
            <span class="mem-item__icon">
              <component :is="categoryIcon(memory.type)" :size="15" />
            </span>

            <div class="mem-item__copy">
              <p class="mem-item__content">{{ memory.content }}</p>
              <div class="mem-item__meta">
                <span>{{ categoryName(memory.type) }}</span>
                <span class="mem-item__sep">·</span>
                <span>{{ formatDate(memory.createdAt) }}</span>
              </div>
            </div>

            <div v-if="canEdit" class="mem-item__acts">
              <button
                type="button"
                class="mem-item__act"
                aria-label="编辑记忆"
                @click="openEditForm(memory)"
              >
                <Pencil :size="15" />
              </button>
              <button
                type="button"
                class="mem-item__act mem-item__act--danger"
                aria-label="删除记忆"
                @click="openDeleteDialog(memory)"
              >
                <Trash2 :size="15" />
              </button>
            </div>
          </article>
        </div>
      </MotionStagger>

      <!-- 空状态 -->
      <EmptyState
        v-else
        icon="brain"
        :title="emptyTitle"
        :description="emptyDescription"
      >
        <button
          v-if="searchQuery || selectedCategory !== 'all'"
          type="button"
          class="btn btn-ghost"
          @click="resetFilters"
        >
          清除筛选条件
        </button>
        <button type="button" class="btn btn-primary" @click="openAddForm">
          记一条
        </button>
      </EmptyState>

      <!-- 说明 -->
      <aside class="tips">
        <div class="tips__card">
          <h2>记忆怎么用</h2>
          <p>每次回复前，系统会按你这句话去检索相关的记忆，取最接近的几条放进上下文。所以记忆写得具体比写得全更有用。</p>
          <p>不相关的记忆不会被塞进去，不会影响其他话题。</p>
        </div>
        <div class="tips__card">
          <h2>注意</h2>
          <p>记忆是按账号存的，换伴侣不会丢。删除伴侣时记忆不受影响。</p>
          <router-link class="link" to="/calendar">看看情绪日历 →</router-link>
        </div>
      </aside>
    </main>

    <!-- 删除确认 -->
    <ModalDialog
      :model-value="Boolean(deleteTarget)"
      title="删除这条记忆？"
      description="删除后该记忆将从数据库与向量库中移除，不可恢复。"
      :width="440"
      :close-on-backdrop="!deleting"
      :close-on-esc="!deleting"
      @update:model-value="closeDeleteDialog"
    >
      <p v-if="deleteTarget" class="modal-quote">{{ deleteTarget.content }}</p>
      <p v-if="deleteError" class="modal-error" role="alert">{{ deleteError }}</p>

      <template #footer>
        <button type="button" class="btn btn-ghost" :disabled="deleting" @click="closeDeleteDialog">
          取消
        </button>
        <button type="button" class="btn btn-danger" :disabled="deleting" @click="confirmDelete">
          {{ deleting ? '删除中…' : '确认删除' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import {
  AlertCircle,
  Brain,
  CalendarDays,
  Check,
  Heart,
  Layers,
  Pencil,
  Plus,
  Search,
  Sparkles,
  Trash2,
  X,
} from 'lucide-vue-next'
import Navbar from '@/components/Navbar.vue'
import MotionStagger from '@/components/ui/MotionStagger.vue'
import CollapseTransition from '@/components/ui/CollapseTransition.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ModalDialog from '@/components/ui/ModalDialog.vue'
import { useToast } from '@/composables/useToast'
import { useMemoryStore } from '@/stores/memory'
import { useMemorySystem } from '@/composables/useMemorySystem'
import type { MemoryType } from '@/types'

const memoryStore = useMemoryStore()
const toast = useToast()

const {
  memoryCategories,
  selectedCategory,
  searchQuery,
  showForm,
  saving,
  saveError,
  newMemory,
  editingId,
  deleteTarget,
  deleting,
  deleteError,
  canEdit,
  filteredMemories,
  getMemoryCount,
  load,
  openAddForm,
  openEditForm,
  cancelForm,
  saveMemory: submitMemory,
  openDeleteDialog,
  closeDeleteDialog,
  confirmDelete: submitDelete,
  error,
  loading,
} = useMemorySystem()

onMounted(() => {
  load()
})

/** 总数从 store 的 computed 读，和 filteredMemories 同源 */
const totalCount = computed(() => memoryStore.memories.length)

/** 分类图标：用线性 SVG 替换原来的 emoji，与全站图标风格一致 */
const categoryIcon = (type: string) => {
  switch (type) {
    case 'preference':
      return Heart
    case 'habit':
      return Sparkles
    case 'important_date':
      return CalendarDays
    case 'milestone':
      return Check
    default:
      return Brain
  }
}

const categoryName = (type: MemoryType | string) =>
  memoryCategories.find((c) => c.id === type)?.name ?? String(type)

const emptyTitle = computed(() =>
  searchQuery.value || selectedCategory.value !== 'all' ? '没有找到匹配的记忆' : '还没有记忆',
)

const emptyDescription = computed(() =>
  searchQuery.value || selectedCategory.value !== 'all'
    ? '换个关键词，或者切回「全部」看看。'
    : '聊几句之后它会自己记住值得记的事；也可以现在就手动记一条。',
)

const resetFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = 'all'
}

/** 保存后给提示：成功失败都反馈，不静默 */
const saveMemory = async () => {
  const isEdit = Boolean(editingId.value)
  await submitMemory()
  if (!saveError.value) {
    toast.success(isEdit ? '记忆已更新' : '记忆已添加')
  } else {
    toast.error('保存失败，请重试')
  }
}

const confirmDelete = async () => {
  await submitDelete()
  if (!deleteError.value) {
    toast.success('记忆已删除')
  } else {
    toast.error('删除失败，请重试')
  }
}

const formatDate = (date: Date) => {
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}
</script>

<style scoped>
.memory {
  min-height: 100vh;
}

.memory-main {
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

.page-head {
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

.page-count {
  margin: 0;
  flex-shrink: 0;
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

/* ---------- 分类条 ---------- */
.cat-strip {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.cat-item {
  display: block;
  padding: var(--sp-4) var(--sp-4) var(--sp-4) 0;
  border: 0;
  border-right: 1px solid var(--line);
  background: transparent;
  text-align: left;
  cursor: pointer;
  transition: box-shadow var(--dur) var(--ease);
}

.cat-item:last-child {
  border-right: 0;
}

.cat-item__label {
  display: flex;
  align-items: center;
  gap: 7px;
  color: var(--muted);
  font-size: var(--fs-13);
  transition: color var(--dur) var(--ease);
}

.cat-item__value {
  display: flex;
  align-items: baseline;
  gap: 3px;
  margin-top: 6px;
  color: var(--text-strong);
  font-size: var(--fs-22);
  font-weight: 720;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.cat-item__value i {
  font-style: normal;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  font-weight: 400;
}

.cat-item:hover .cat-item__label {
  color: var(--text-strong);
}

.cat-item.is-active {
  box-shadow: inset 0 -2px 0 var(--accent);
}

.cat-item.is-active .cat-item__label,
.cat-item.is-active .cat-item__value {
  color: var(--accent);
}

/* ---------- 工具条 ---------- */
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4) 0;
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

.toolbar__count {
  margin: 0;
  color: var(--muted-faint);
  font-size: var(--fs-13);
  white-space: nowrap;
}

.toolbar__add {
  margin-left: auto;
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

.btn-danger {
  border: 1px solid var(--primary-line);
  color: var(--primary);
  background: var(--danger-soft);
}

.btn-danger:hover:not(:disabled) {
  background: rgba(255, 139, 114, 0.16);
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
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

/* ---------- 新增面板 ---------- */
.form-panel {
  margin-bottom: var(--sp-4);
  padding: var(--sp-5);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

.form-panel__title {
  margin: 0 0 var(--sp-4);
  color: var(--text-strong);
  font-size: var(--fs-16);
  font-weight: 700;
}

.form-panel__row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
}

.form-panel__type {
  flex: 0 0 160px;
}

.form-panel__content {
  flex: 1 1 240px;
}

.field > span {
  display: block;
  margin-bottom: var(--sp-2);
  color: var(--text);
  font-size: var(--fs-13);
  font-weight: 650;
}

.select {
  width: 100%;
  min-height: 42px;
  padding: 10px 38px 10px 16px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-card);
  color: var(--text);
  background: var(--bg);
  font-size: var(--fs-13);
  appearance: none;
  background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='none' stroke='%23aaa9a2' stroke-width='1.75' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m4 6.5 4 4 4-4'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
}

.select:focus {
  outline: none;
  border-color: var(--accent-line);
  box-shadow: var(--ring-accent);
}

.form-panel__error {
  margin: var(--sp-3) 0 0;
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

.form-panel__foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-top: var(--sp-4);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--line);
}

.form-panel__actions {
  display: flex;
  gap: var(--sp-2);
}

.small {
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

/* ---------- 记忆列表 ---------- */
.mem-list {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

.mem-item {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--line);
  transition: background var(--dur) var(--ease);
}

.mem-item:last-child {
  border-bottom: 0;
}

.mem-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.mem-item__icon {
  display: grid;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  place-items: center;
  border-radius: var(--radius-sm);
  color: var(--accent);
  background: var(--accent-soft);
}

.mem-item__copy {
  min-width: 0;
  flex: 1;
}

.mem-item__content {
  margin: 0;
  color: var(--text);
  font-size: var(--fs-14);
  line-height: 1.65;
  word-break: break-word;
}

.mem-item__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 5px;
  margin-top: 5px;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.mem-item__sep {
  color: var(--muted-faint);
}

.mem-item__acts {
  display: flex;
  flex-shrink: 0;
  gap: 2px;
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

.mem-item:hover .mem-item__acts {
  opacity: 1;
}

.mem-item__act {
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

.mem-item__act:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.06);
}

.mem-item__act--danger:hover {
  color: var(--primary);
  background: var(--danger-soft);
}

/* ---------- 说明 ---------- */
.tips {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sp-3);
  margin-top: var(--sp-6);
}

.tips__card {
  padding: var(--sp-5);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

.tips__card h2 {
  margin: 0 0 var(--sp-3);
  color: var(--text-strong);
  font-size: var(--fs-13);
  font-weight: 650;
}

.tips__card p {
  margin: 0;
  color: var(--muted);
  font-size: var(--fs-13);
  line-height: 1.7;
}

.tips__card p + p {
  margin-top: var(--sp-3);
}

.link {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  margin-top: var(--sp-3);
  color: var(--accent);
  font-size: var(--fs-13);
}

.link:hover {
  text-decoration: underline;
}

/* ---------- 弹窗 ---------- */
.modal-quote {
  margin: 0;
  padding: var(--sp-3) var(--sp-4);
  border-left: 2px solid var(--line-strong);
  color: var(--text);
  font-size: var(--fs-14);
  line-height: 1.7;
  word-break: break-word;
}

.modal-error {
  margin: var(--sp-3) 0 0;
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

/* ---------- 响应式 ---------- */
@media (max-width: 900px) {
  .cat-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .cat-item {
    border-right: 0;
    border-bottom: 1px solid var(--line);
  }

  .cat-item:nth-child(odd) {
    border-right: 1px solid var(--line);
  }

  .cat-item:last-child {
    border-bottom: 0;
  }

  .tips {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 760px) {
  .memory-main {
    padding: var(--sp-10) 0 var(--sp-16);
  }

  .page-head {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--sp-3);
  }

  .search {
    max-width: none;
  }

  .toolbar__count {
    display: none;
  }

  .toolbar__add {
    margin-left: 0;
    width: 100%;
  }

  .form-panel__type {
    flex: 1 1 100%;
  }

  .mem-item {
    padding: var(--sp-4);
  }

  .mem-item__acts {
    opacity: 1;
  }
}
</style>
