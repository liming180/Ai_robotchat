<template>
  <div class="min-h-screen bg-slate-900 p-6">
    <!-- 顶部导航 -->
    <nav class="flex items-center justify-between mb-8">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
          <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
          </svg>
        </div>
        <h1 class="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          AI 伴侣广场
        </h1>
      </div>
      
      <div class="flex items-center gap-3">
        <button class="p-2 rounded-lg hover:bg-slate-800 transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
          </svg>
        </button>
        <button 
          @click="$router.push('/profile')"
          class="p-2 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
          </svg>
        </button>
      </div>
    </nav>

    <!-- 搜索和筛选 -->
    <div class="mb-8 space-y-4">
      <div class="relative">
        <svg class="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索你的 AI 伴侣..."
          class="w-full pl-12 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
        />
      </div>
      
      <div class="flex gap-2 overflow-x-auto pb-2">
        <button
          v-for="category in categories"
          :key="category"
          @click="selectedCategory = category"
          :class="[
            'px-4 py-2 rounded-full text-sm font-medium whitespace-nowrap transition-all',
            selectedCategory === category
              ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
          ]"
        >
          {{ category }}
        </button>
      </div>
    </div>

    <!-- 创建新伴侣按钮 -->
    <button
      @click="$router.push('/create')"
      class="w-full mb-8 p-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-medium hover:from-purple-500 hover:to-pink-500 transition-all glow-button flex items-center justify-center gap-2"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/>
      </svg>
      创建你的专属 AI 伴侣
    </button>

    <!-- 收藏伴侣区 -->
    <div v-if="favoriteCompanions.length > 0" class="mb-8">
      <h2 class="text-lg font-semibold mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-pink-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
        </svg>
        我的收藏
      </h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="companion in favoriteCompanions"
          :key="companion.id"
          @click="startChat(companion.id)"
          class="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-purple-500 hover:shadow-lg hover:shadow-purple-500/20 cursor-pointer transition-all"
        >
          <div class="flex items-start gap-4">
            <img
              :src="companion.avatar"
              :alt="companion.name"
              class="w-14 h-14 rounded-full object-cover border-2 border-purple-500"
            />
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-lg truncate">{{ companion.name }}</h3>
              <p class="text-slate-400 text-sm mt-1 line-clamp-2">{{ companion.description }}</p>
              <div class="flex flex-wrap gap-1 mt-2">
                <span class="px-2 py-0.5 text-xs rounded-full bg-slate-700 text-slate-300">
                  {{ companion.category }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- 亲密度条 -->
          <div class="mt-4">
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-400">亲密度</span>
              <span class="text-pink-400">{{ companion.intimacy }}%</span>
            </div>
            <div class="h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full transition-all"
                :style="{ width: companion.intimacy + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 所有伴侣 -->
    <div>
      <h2 class="text-lg font-semibold mb-4">发现更多</h2>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="companion in filteredCompanions"
          :key="companion.id"
          @click="startChat(companion.id)"
          class="bg-slate-800 rounded-xl p-4 border border-slate-700 hover:border-purple-500 hover:shadow-lg hover:shadow-purple-500/20 cursor-pointer transition-all"
        >
          <div class="flex items-start gap-4">
            <img
              :src="companion.avatar"
              :alt="companion.name"
              class="w-14 h-14 rounded-full object-cover border-2 border-slate-600"
            />
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between">
                <h3 class="font-semibold text-lg truncate">{{ companion.name }}</h3>
                <button
                  @click.stop="toggleFavorite(companion.id)"
                  :class="['p-1 rounded-full transition-colors', companion.isFavorite ? 'text-pink-500' : 'text-slate-500 hover:text-slate-300']"
                >
                  <svg
                    :class="['w-5 h-5', companion.isFavorite ? 'fill-current' : '']"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                  </svg>
                </button>
              </div>
              <p class="text-slate-400 text-sm mt-1 line-clamp-2">{{ companion.description }}</p>
              <div class="flex flex-wrap gap-1 mt-2">
                <span class="px-2 py-0.5 text-xs rounded-full bg-slate-700 text-slate-300">
                  {{ companion.category }}
                </span>
                <span v-for="tag in companion.tags.slice(0, 2)" :key="tag" class="px-2 py-0.5 text-xs rounded-full bg-purple-500/20 text-purple-300">
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>
          
          <!-- 亲密度条 -->
          <div class="mt-4">
            <div class="flex justify-between text-xs mb-1">
              <span class="text-slate-400">亲密度</span>
              <span class="text-pink-400">{{ companion.intimacy }}%</span>
            </div>
            <div class="h-1.5 bg-slate-700 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-pink-500 to-purple-500 rounded-full transition-all"
                :style="{ width: companion.intimacy + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '@/stores/companion'

const router = useRouter()
const companionStore = useCompanionStore()

const searchQuery = ref('')
const selectedCategory = ref('全部')

const categories = computed(() => ['全部', '日常聊天', '学习助手', '娱乐陪伴'])

const filteredCompanions = computed(() => {
  let companions = selectedCategory.value === '全部'
    ? companionStore.allCompanions
    : companionStore.filterByCategory(selectedCategory.value)
  
  if (searchQuery.value) {
    companions = companionStore.searchCompanions(searchQuery.value)
  }
  
  return companions
})

const favoriteCompanions = computed(() => companionStore.favoriteCompanions)

const startChat = (companionId: string) => {
  router.push(`/chat/${companionId}`)
}

const toggleFavorite = (id: string) => {
  companionStore.toggleFavorite(id)
}
</script>
