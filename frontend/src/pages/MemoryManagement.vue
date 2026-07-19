<template>
  <div class="min-h-screen relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 -z-10">
      <div class="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-pink-600/10 to-transparent"></div>
    </div>

    <!-- 顶部导航 -->
    <nav class="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/80 border-b border-white/10">
      <div class="max-w-4xl mx-auto px-6 py-4">
        <div class="flex items-center gap-4">
          <button @click="$router.back()" class="p-2 rounded-xl hover:bg-white/5 transition-colors">
            <svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <h1 class="text-2xl font-bold text-white">记忆管理</h1>
        </div>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-6 py-8 space-y-6">
      <!-- 分类卡片 -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-6">
        <h3 class="text-lg font-semibold text-white mb-4">记忆分类</h3>
        <div class="grid grid-cols-4 gap-3">
          <button
            v-for="category in memoryCategories"
            :key="category.id"
            @click="selectedCategory = category.id"
            class="flex flex-col items-center gap-2 p-4 rounded-xl border border-white/10 hover:border-violet-500/40 hover:bg-white/5 transition-all"
            :class="selectedCategory === category.id ? 'border-violet-500/40 bg-white/5' : ''"
          >
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/20 to-pink-500/20 flex items-center justify-center">
              <span class="text-lg">{{ category.icon }}</span>
            </div>
            <div class="text-sm font-medium text-white">{{ category.name }}</div>
            <div class="text-xs text-slate-400">{{ getMemoryCount(category.id) }} 条</div>
          </button>
        </div>
      </div>

      <!-- 搜索和添加 -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-6">
        <div class="flex gap-3 mb-4">
          <input
            v-model="searchQuery"
            placeholder="搜索记忆..."
            class="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/40"
          />
          <button
            @click="openAddForm"
            class="px-4 py-2 bg-gradient-to-r from-violet-600 to-pink-500 rounded-xl text-white font-medium hover:opacity-90 transition-all"
          >
            新增记忆
          </button>
        </div>

        <!-- 记忆列表 -->
        <div class="space-y-3">
          <div v-if="filteredMemories.length" class="space-y-3">
            <div
              v-for="memory in filteredMemories"
              :key="memory.id"
              class="flex items-center gap-3 p-4 rounded-xl bg-white/5 hover:bg-white/10 transition-all"
            >
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/20 to-pink-500/20 flex items-center justify-center">
                <span class="text-lg">{{ memoryCategories.find(c => c.id === memory.type)?.icon }}</span>
              </div>
              <div class="flex-1">
                <div class="text-sm text-white">{{ memory.content }}</div>
                <div class="text-xs text-slate-400 mt-1">
                  {{ memoryCategories.find(c => c.id === memory.type)?.name }} · {{ formatDate(memory.createdAt) }}
                </div>
              </div>
              <div class="flex gap-2">
                <button
                  @click="openEditForm(memory)"
                  class="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-white transition-all"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                  </svg>
                </button>
                <button
                  @click="deleteMemory(memory.id)"
                  class="p-2 rounded-lg hover:bg-white/5 text-slate-400 hover:text-red-400 transition-all"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <div v-else class="text-center py-8 text-slate-500">
            <svg class="w-16 h-16 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
            </svg>
            <p>暂无记忆</p>
          </div>
        </div>
      </div>

      <!-- 新增/编辑表单 -->
      <div v-if="showForm" class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-6">
        <h3 class="text-lg font-semibold text-white mb-4">
          {{ editingId ? '编辑记忆' : '新增记忆' }}
        </h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-2">记忆类型</label>
            <select
              v-model="newMemory.type"
              class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-violet-500/40"
            >
              <option v-for="category in memoryCategories" :key="category.id" :value="category.id">
                {{ category.name }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-300 mb-2">记忆内容</label>
            <textarea
              v-model="newMemory.content"
              rows="4"
              placeholder="输入要记住的内容..."
              class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-violet-500/40 resize-none"
            ></textarea>
          </div>
          <div class="flex gap-3">
            <button
              @click="saveMemory"
              class="flex-1 px-4 py-2 bg-gradient-to-r from-violet-600 to-pink-500 rounded-xl text-white font-medium hover:opacity-90 transition-all"
            >
              保存
            </button>
            <button
              @click="showForm = false"
              class="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-slate-300 hover:bg-white/10 transition-all"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMemorySystem } from '@/composables/useMemorySystem'
import { createSvgAvatarDataUrl } from '@/lib/avatar'

const router = useRouter()
const {
  memories,
  memoryCategories,
  selectedCategory,
  searchQuery,
  showForm,
  editingId,
  newMemory,
  filteredMemories,
  getMemoryCount,
  openAddForm,
  openEditForm,
  saveMemory,
  deleteMemory,
  searchMemories,
} = useMemorySystem()

const formatDate = (date: Date) => {
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}
</script>