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
      <p v-if="error" class="px-4 py-3 rounded-xl border border-amber-500/30 bg-amber-500/10 text-sm text-amber-300" role="alert">
        {{ error }}
      </p>

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
              <!-- 编辑/删除需要 Python 端提供 update/delete 接口，本轮（任务四）只做新增，二期开放 -->
              <div class="flex gap-2">
                <span class="text-xs text-slate-600 self-center">只读</span>
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
        <h3 class="text-lg font-semibold text-white mb-4">新增记忆</h3>
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
          <p v-if="saveError" class="text-sm text-red-300" role="alert">{{ saveError }}</p>
          <div class="flex gap-3">
            <button
              @click="saveMemory"
              :disabled="saving || !newMemory.content.trim()"
              class="flex-1 px-4 py-2 bg-gradient-to-r from-violet-600 to-pink-500 rounded-xl text-white font-medium hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ saving ? '保存中...' : '保存' }}
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
import { onMounted } from 'vue'
import { useMemorySystem } from '@/composables/useMemorySystem'

const {
  memoryCategories,
  selectedCategory,
  searchQuery,
  showForm,
  saving,
  saveError,
  newMemory,
  filteredMemories,
  getMemoryCount,
  load,
  openAddForm,
  saveMemory,
  error,
} = useMemorySystem()

onMounted(() => {
  load()
})

const formatDate = (date: Date) => {
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}
</script>