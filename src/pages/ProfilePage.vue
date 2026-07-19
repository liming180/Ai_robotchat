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
          <h1 class="text-2xl font-bold text-white">个人中心</h1>
        </div>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-6 py-8 space-y-6">
      <!-- 用户信息卡片 -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-8">
        <div class="flex flex-col sm:flex-row items-center gap-6">
          <div class="w-24 h-24 rounded-3xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center shadow-xl shadow-pink-500/30">
            <span class="text-3xl font-bold text-white">你</span>
          </div>
          <div class="flex-1 text-center sm:text-left">
            <h2 class="text-2xl font-semibold text-white">用户</h2>
            <p class="text-slate-400 mt-1">欢迎使用 AI 伴侣</p>
          </div>
        </div>
      </div>

      <!-- 统计数据 -->
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 text-center hover:border-pink-500/30 transition-all">
          <div class="text-3xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
            {{ companionStore.allCompanions.length }}
          </div>
          <div class="text-slate-400 text-sm mt-2">AI 伴侣</div>
        </div>
        <div class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 text-center hover:border-pink-500/30 transition-all">
          <div class="text-3xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
            {{ chatStore.conversations.length }}
          </div>
          <div class="text-slate-400 text-sm mt-2">对话</div>
        </div>
        <div class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 text-center hover:border-pink-500/30 transition-all">
          <div class="text-3xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
            {{ totalMessages }}
          </div>
          <div class="text-slate-400 text-sm mt-2">消息</div>
        </div>
      </div>

      <!-- 菜单列表 -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 overflow-hidden">
        <div class="divide-y divide-white/10">
          <button @click="$router.push('/history')" class="w-full p-5 flex items-center gap-4 hover:bg-white/5 transition-colors">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
              </svg>
            </div>
            <div class="flex-1 text-left">
              <div class="font-medium text-white">聊天历史</div>
              <div class="text-sm text-slate-400">查看历史对话</div>
            </div>
            <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>

          <button @click="$router.push('/')" class="w-full p-5 flex items-center gap-4 hover:bg-white/5 transition-colors">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-pink-500/20 to-orange-500/20 flex items-center justify-center">
              <svg class="w-6 h-6 text-pink-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
              </svg>
            </div>
            <div class="flex-1 text-left">
              <div class="font-medium text-white">我的收藏</div>
              <div class="text-sm text-slate-400">管理收藏的伴侣</div>
            </div>
            <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>

          <button @click="$router.push('/create')" class="w-full p-5 flex items-center gap-4 hover:bg-white/5 transition-colors">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500/20 to-pink-500/20 flex items-center justify-center">
              <svg class="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            <div class="flex-1 text-left">
              <div class="font-medium text-white">创建伴侣</div>
              <div class="text-sm text-slate-400">自定义专属 AI</div>
            </div>
            <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>

          <button @click="showSettings = true" class="w-full p-5 flex items-center gap-4 hover:bg-white/5 transition-colors">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-slate-500/20 to-purple-500/20 flex items-center justify-center">
              <svg class="w-6 h-6 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
            </div>
            <div class="flex-1 text-left">
              <div class="font-medium text-white">设置</div>
              <div class="text-sm text-slate-400">通用设置</div>
            </div>
            <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/>
            </svg>
          </button>
        </div>
      </div>

      <!-- 我的收藏 -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-8">
        <h3 class="text-lg font-semibold text-white mb-6 flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-r from-pink-500/20 to-purple-500/20 flex items-center justify-center">
            <svg class="w-5 h-5 text-pink-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
          </div>
          我的收藏
        </h3>
        <div v-if="favoriteCompanions.length > 0" class="space-y-3">
          <div
            v-for="companion in favoriteCompanions"
            :key="companion.id"
            @click="startChat(companion.id)"
            class="flex items-center gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition-all cursor-pointer"
          >
            <img
              :src="companion.avatar"
              :alt="companion.name"
              class="w-14 h-14 rounded-2xl object-cover"
            />
            <div class="flex-1 min-w-0">
              <h4 class="font-medium text-white truncate">{{ companion.name }}</h4>
              <p class="text-sm text-slate-400">{{ companion.personality }}</p>
            </div>
            <div class="w-8 h-8 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl flex items-center justify-center">
              <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 12h.01M12 12h.01M19 12h.01M12 5v14"/>
              </svg>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-12">
          <div class="w-16 h-16 rounded-full bg-white/5 mx-auto mb-4 flex items-center justify-center">
            <svg class="w-8 h-8 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
          </div>
          <p class="text-slate-400">还没有收藏的伴侣</p>
          <button
            @click="$router.push('/')"
            class="mt-4 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-slate-300 hover:bg-white/10 transition-colors"
          >
            去广场看看
          </button>
        </div>
      </div>

      <!-- 关于 -->
      <div class="text-center text-slate-500 text-sm pb-20">
        <p class="font-medium">AI 情侣 v1.0</p>
        <p class="mt-1">使用 Vue 3 + TypeScript 构建</p>
        <p class="mt-1">温馨浪漫的 AI 陪伴体验</p>
      </div>
    </div>

    <!-- 设置弹窗 -->
    <div v-if="showSettings" class="fixed inset-0 z-50 flex items-center justify-center p-6">
      <div class="absolute inset-0 bg-black/60" @click="showSettings = false"></div>
      <div class="relative bg-slate-900 border border-white/10 rounded-3xl p-8 max-w-md w-full shadow-2xl">
        <h3 class="text-xl font-bold text-white mb-6">设置</h3>
        <div class="space-y-4">
          <button
            @click="clearAllData" class="w-full p-4 border border-red-500/50 text-red-400 rounded-xl hover:bg-red-500/10 transition-colors flex items-center justify-center gap-3">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
            清除所有数据
          </button>
          <button
            @click="showSettings = false" class="w-full p-4 bg-white/5 border border-white/10 text-slate-300 rounded-xl hover:bg-white/10 transition-colors"
          >
            关闭
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '@/stores/companion'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const companionStore = useCompanionStore()
const chatStore = useChatStore()

const showSettings = ref(false)
const favoriteCompanions = computed(() => companionStore.favoriteCompanions)

const totalMessages = computed(() => {
  return chatStore.conversations.reduce((acc, conv) => acc + conv.messages.length, 0)
})

const startChat = (companionId: string) => {
  router.push(`/chat/${companionId}`)
}

const clearAllData = () => {
  if (confirm('确定要清除所有数据吗？这将删除所有对话和自定义伴侣。')) {
    // 清除 localStorage
    localStorage.clear()
    // 刷新页面来重置所有状态
    location.reload()
  }
}
</script>
