<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useNoteStore } from '@/stores/note'
import { useCompanionStore } from '@/stores/companion'
import { Search, Trash2, Edit2, X, Plus } from 'lucide-vue-next'

const noteStore = useNoteStore()
const companionStore = useCompanionStore()

const searchQuery = ref('')
const selectedTag = ref('全部')
const showEditModal = ref(false)
/** 非空表示编辑现有笔记，空表示新增 */
const editingNote = ref<any>(null)
const editContent = ref('')
const editTags = ref('')
/** 新增/编辑共用的伴侣选择；编辑时回显当前归属 */
const editCompanionId = ref('')
const saving = ref(false)
const saveError = ref('')
const deletingId = ref('')

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

/** 可以记笔记的伴侣：全部可见伴侣（预置伴侣也允许，笔记是用户自己的内容） */
const companionOptions = computed(() => companionStore.companions)

const getCompanionName = (id: string) => {
  const companion = companionStore.getCompanionById(id)
  return companion?.name || '未知'
}

onMounted(async () => {
  await Promise.all([noteStore.loadNotes(), companionStore.loadCompanions()])
})

/** 打开新增表单 */
const openCreateModal = () => {
  editingNote.value = null
  editContent.value = ''
  editTags.value = ''
  // 默认选中第一个伴侣，减少一次点击
  editCompanionId.value = companionOptions.value[0]?.id || ''
  saveError.value = ''
  showEditModal.value = true
}

const openEditModal = (note: any) => {
  editingNote.value = note
  editContent.value = note.content
  editTags.value = note.tags.join(', ')
  editCompanionId.value = note.companionId
  saveError.value = ''
  showEditModal.value = true
}

const closeModal = () => {
  if (saving.value) return
  showEditModal.value = false
  editingNote.value = null
  saveError.value = ''
}

const canSave = computed(() =>
  Boolean(editContent.value.trim()) && Boolean(editCompanionId.value) && !saving.value,
)

const saveNote = async () => {
  if (!canSave.value) return
  saving.value = true
  saveError.value = ''
  const tagList = editTags.value.split(',').map(t => t.trim()).filter(t => t)
  try {
    if (editingNote.value) {
      await noteStore.updateNote(editingNote.value.id, {
        content: editContent.value,
        tags: tagList,
        companionId: editCompanionId.value,
      })
    } else {
      await noteStore.addNote(editCompanionId.value, editContent.value, tagList)
    }
    showEditModal.value = false
    editingNote.value = null
  } catch (e) {
    saveError.value = `保存失败：${(e as Error).message}`
  } finally {
    saving.value = false
  }
}

const deleteNote = async (id: string) => {
  if (!confirm('确定要删除这条笔记吗？删除后不可恢复。')) return
  deletingId.value = id
  try {
    await noteStore.deleteNote(id)
  } catch (e) {
    alert(`删除失败：${(e as Error).message}`)
  } finally {
    deletingId.value = ''
  }
}

const formatDate = (date: Date) => {
  return new Date(date).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<template>
  <div class="p-4 max-w-4xl mx-auto">
    <div class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-800 mb-2">我的笔记</h1>
      <p class="text-gray-600">记录与 AI 伴侣的精彩时刻</p>
    </div>

    <p v-if="noteStore.error" class="mb-6 px-4 py-3 rounded-xl border border-red-500/30 bg-red-500/10 text-sm text-red-300" role="alert">
      {{ noteStore.error }}
    </p>

    <div class="glass-card p-4 mb-6">
      <div class="flex flex-col sm:flex-row gap-3">
        <div class="relative flex-1">
          <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索笔记..."
            class="w-full pl-10 pr-4 py-3 rounded-xl glass-input focus:outline-none focus:ring-2 focus:ring-pink-300"
          />
        </div>
        <button
          type="button"
          class="write-button"
          :disabled="companionOptions.length === 0"
          :title="companionOptions.length === 0 ? '还没有可选的伴侣' : '写一条新笔记'"
          @click="openCreateModal"
        >
          <Plus class="w-5 h-5" />
          写笔记
        </button>
      </div>
    </div>

    <div class="mb-6">
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button
          v-for="tag in tags"
          :key="tag"
          @click="selectedTag = tag"
          :class="[
            'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
            selectedTag === tag
              ? 'bg-gradient-to-r from-pink-400 to-orange-300 text-white shadow-lg'
              : 'glass-card hover:bg-white/40'
          ]"
        >
          {{ tag }}
        </button>
      </div>
    </div>

    <div class="space-y-4">
      <div
        v-for="note in filteredNotes"
        :key="note.id"
        class="glass-card p-4"
      >
        <div class="flex items-start justify-between mb-3">
          <div>
            <p class="text-sm text-gray-600 mb-1">
              来自 {{ getCompanionName(note.companionId) }}
            </p>
            <p class="text-xs text-gray-500">{{ formatDate(note.createdAt) }}</p>
          </div>
          <div class="flex gap-2">
            <button
              type="button"
              aria-label="编辑笔记"
              class="p-2 rounded-full hover:bg-white/30 transition-colors"
              @click="openEditModal(note)"
            >
              <Edit2 class="w-4 h-4 text-gray-600" />
            </button>
            <button
              type="button"
              :disabled="deletingId === note.id"
              :aria-label="`删除笔记`"
              class="p-2 rounded-full hover:bg-white/30 transition-colors disabled:opacity-40"
              @click="deleteNote(note.id)"
            >
              <Trash2 class="w-4 h-4 text-red-500" />
            </button>
          </div>
        </div>

        <p class="text-gray-800 mb-3">{{ note.content }}</p>

        <div v-if="note.tags.length > 0" class="flex flex-wrap gap-2">
          <span
            v-for="tag in note.tags"
            :key="tag"
            class="px-3 py-1 text-xs rounded-full bg-gradient-to-r from-pink-200 to-orange-200 text-gray-700"
          >
            {{ tag }}
          </span>
        </div>
      </div>

      <div v-if="noteStore.loading" class="text-center py-12">
        <p class="text-gray-500">加载中…</p>
      </div>

      <div v-else-if="filteredNotes.length === 0" class="text-center py-12">
        <div class="glass-card p-8">
          <p class="text-gray-600 mb-4">{{ searchQuery || selectedTag !== '全部' ? '没有匹配的笔记' : '还没有笔记' }}</p>
          <p class="text-sm text-gray-500 mb-4">
            {{ searchQuery || selectedTag !== '全部' ? '换个关键词或标签试试' : '点上方「写笔记」，记录与伴侣的精彩时刻' }}
          </p>
          <button
            v-if="!searchQuery && selectedTag === '全部' && companionOptions.length"
            type="button"
            class="write-button mx-auto"
            @click="openCreateModal"
          >
            <Plus class="w-5 h-5" />
            写第一条笔记
          </button>
        </div>
      </div>
    </div>

    <div v-if="showEditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="glass-card p-6 w-full max-w-md">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">{{ editingNote ? '编辑笔记' : '写笔记' }}</h3>
          <button type="button" @click="closeModal" class="p-1 rounded-full hover:bg-white/30" aria-label="关闭">
            <X class="w-5 h-5 text-gray-600" />
          </button>
        </div>

        <label class="block text-sm font-medium text-gray-600 mb-1">来自</label>
        <select
          v-model="editCompanionId"
          class="w-full px-4 py-3 rounded-xl glass-input focus:outline-none focus:ring-2 focus:ring-pink-300 mb-4"
        >
          <option v-if="companionOptions.length === 0" value="" disabled>还没有可选伴侣</option>
          <option v-for="c in companionOptions" :key="c.id" :value="c.id">{{ c.name }}</option>
        </select>

        <label class="block text-sm font-medium text-gray-600 mb-1">内容</label>
        <textarea
          v-model="editContent"
          placeholder="记录你的想法..."
          class="w-full px-4 py-3 rounded-xl glass-input focus:outline-none focus:ring-2 focus:ring-pink-300 mb-4 resize-none"
          rows="4"
        ></textarea>

        <label class="block text-sm font-medium text-gray-600 mb-1">标签</label>
        <input
          v-model="editTags"
          type="text"
          placeholder="用逗号分隔，如：温柔, 治愈"
          class="w-full px-4 py-3 rounded-xl glass-input focus:outline-none focus:ring-2 focus:ring-pink-300 mb-4"
        />

        <p v-if="saveError" class="mb-4 px-3 py-2 rounded-lg border border-red-500/30 bg-red-500/10 text-sm text-red-300" role="alert">
          {{ saveError }}
        </p>

        <div class="flex gap-3">
          <button
            type="button"
            :disabled="saving"
            class="flex-1 px-4 py-2 rounded-xl glass-card hover:bg-white/40 text-gray-700 font-medium disabled:opacity-50"
            @click="closeModal"
          >
            取消
          </button>
          <button
            type="button"
            :disabled="!canSave"
            class="flex-1 px-4 py-2 rounded-xl glass-button text-white font-medium disabled:opacity-50"
            @click="saveNote"
          >
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.write-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 22px;
  border: 0;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #ec4899 0%, #f97316 100%);
  font-weight: 600;
  font-size: 15px;
  white-space: nowrap;
  cursor: pointer;
  transition: transform 160ms ease, opacity 160ms ease;
}

.write-button:hover:not(:disabled) {
  transform: translateY(-1px);
}

.write-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
