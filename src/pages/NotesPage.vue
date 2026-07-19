<script setup lang="ts">
import { ref, computed } from 'vue'
import { useNoteStore } from '@/stores/note'
import { useCompanionStore } from '@/stores/companion'
import { Search, Trash2, Edit2, X } from 'lucide-vue-next'

const noteStore = useNoteStore()
const companionStore = useCompanionStore()

const searchQuery = ref('')
const selectedTag = ref('全部')
const showEditModal = ref(false)
const editingNote = ref<any>(null)
const editContent = ref('')
const editTags = ref('')

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

const getCompanionName = (id: string) => {
  const companion = companionStore.getCompanionById(id)
  return companion?.name || '未知'
}

const deleteNote = (id: string) => {
  noteStore.deleteNote(id)
}

const openEditModal = (note: any) => {
  editingNote.value = note
  editContent.value = note.content
  editTags.value = note.tags.join(', ')
  showEditModal.value = true
}

const saveEdit = () => {
  if (!editContent.value.trim() || !editingNote.value) return
  const tags = editTags.value.split(',').map(t => t.trim()).filter(t => t)
  noteStore.updateNote(editingNote.value.id, editContent.value, tags)
  showEditModal.value = false
  editingNote.value = null
  editContent.value = ''
  editTags.value = ''
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

    <div class="glass-card p-4 mb-6">
      <div class="relative">
        <Search class="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索笔记..."
          class="w-full pl-10 pr-4 py-3 rounded-xl glass-input focus:outline-none focus:ring-2 focus:ring-pink-300"
        />
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
              @click="openEditModal(note)"
              class="p-2 rounded-full hover:bg-white/30 transition-colors"
            >
              <Edit2 class="w-4 h-4 text-gray-600" />
            </button>
            <button
              @click="deleteNote(note.id)"
              class="p-2 rounded-full hover:bg-white/30 transition-colors"
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

      <div v-if="filteredNotes.length === 0" class="text-center py-12">
        <div class="glass-card p-8">
          <p class="text-gray-600 mb-4">还没有笔记</p>
          <p class="text-sm text-gray-500">开始与 AI 伴侣聊天，记录你的想法吧！</p>
        </div>
      </div>
    </div>

    <div v-if="showEditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="glass-card p-6 w-full max-w-md">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-semibold text-gray-800">编辑笔记</h3>
          <button @click="showEditModal = false" class="p-1 rounded-full hover:bg-white/30">
            <X class="w-5 h-5 text-gray-600" />
          </button>
        </div>
        <textarea
          v-model="editContent"
          placeholder="记录你的想法..."
          class="w-full px-4 py-3 rounded-xl glass-input focus:outline-none focus:ring-2 focus:ring-pink-300 mb-4 resize-none"
          rows="4"
        ></textarea>
        <input
          v-model="editTags"
          type="text"
          placeholder="标签（用逗号分隔）"
          class="w-full px-4 py-3 rounded-xl glass-input focus:outline-none focus:ring-2 focus:ring-pink-300 mb-4"
        />
        <div class="flex gap-3">
          <button
            @click="showEditModal = false"
            class="flex-1 px-4 py-2 rounded-xl glass-card hover:bg-white/40 text-gray-700 font-medium"
          >
            取消
          </button>
          <button
            @click="saveEdit"
            :disabled="!editContent.trim()"
            class="flex-1 px-4 py-2 rounded-xl glass-button text-white font-medium disabled:opacity-50"
          >
            保存
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
