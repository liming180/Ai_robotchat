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
          <h1 class="text-2xl font-bold text-white">人设设置</h1>
        </div>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-6 py-8">
      <div v-if="companion" class="space-y-8">
        <!-- 头像区域 -->
        <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-8">
          <div class="flex flex-col sm:flex-row items-center gap-8">
            <div class="relative">
              <img
                :src="form.avatar"
                class="w-32 h-32 rounded-3xl object-cover border-4 border-white/10 shadow-2xl"
              />
              <label class="absolute bottom-2 right-2 w-10 h-10 bg-gradient-to-r from-pink-500 to-purple-600 rounded-2xl flex items-center justify-center cursor-pointer hover:from-pink-400 hover:to-purple-500 transition-all shadow-lg">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812-1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
                </svg>
                <input type="file" accept="image/*" class="hidden" @change="handleAvatarUpload" />
              </label>
            </div>
            <div class="text-center sm:text-left flex-1">
              <h2 class="text-2xl font-bold text-white mb-2">{{ companion.name }}</h2>
              <p class="text-slate-400 mb-4">{{ companion.description }}</p>
              <div class="flex flex-wrap gap-2">
                <span class="px-3 py-1 text-sm rounded-full bg-pink-500/20 text-pink-300">{{ companion.category }}</span>
                <span class="px-3 py-1 text-sm rounded-full bg-purple-500/20 text-purple-300">{{ companion.personality }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 基本信息 -->
        <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-8">
          <h3 class="text-lg font-semibold text-white mb-6 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-r from-pink-500/20 to-purple-500/20 flex items-center justify-center">
              <svg class="w-5 h-5 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
              </svg>
            </div>
            基本信息
          </h3>

          <div class="grid gap-6">
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">名字</label>
              <input
                v-model="form.name"
                type="text"
                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">分类</label>
              <select
                v-model="form.category"
                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              >
                <option value="日常聊天">日常聊天</option>
                <option value="学习助手">学习助手</option>
                <option value="娱乐陪伴">娱乐陪伴</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">性格</label>
              <select
                v-model="form.personality"
                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all"
              >
                <option value="温柔体贴">温柔体贴</option>
                <option value="博学多才">博学多才</option>
                <option value="幽默风趣">幽默风趣</option>
                <option value="文艺优雅">文艺优雅</option>
                <option value="阳光积极">阳光积极</option>
                <option value="创意无限">创意无限</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">描述</label>
              <textarea
                v-model="form.description"
                rows="3"
                class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all resize-none"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- 对话风格 -->
        <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-8">
          <h3 class="text-lg font-semibold text-white mb-6 flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-r from-purple-500/20 to-orange-500/20 flex items-center justify-center">
              <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
              </svg>
            </div>
            对话风格
          </h3>

          <div>
            <label class="block text-sm font-medium text-slate-300 mb-2">系统提示词</label>
            <textarea
              v-model="form.systemPrompt"
              rows="6"
              class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-pink-500/50 focus:ring-2 focus:ring-pink-500/20 transition-all resize-none font-mono text-sm"
            ></textarea>
            <p class="text-xs text-slate-500 mt-2">
              这决定了 AI 伴侣如何与你对话，包括语气、风格、角色设定等
            </p>
          </div>
        </div>

        <!-- 保存按钮 -->
        <div class="flex gap-4">
          <button
            @click="$router.back()"
            class="flex-1 py-4 bg-white/5 border border-white/10 rounded-xl font-semibold text-slate-300 hover:bg-white/10 transition-all"
          >
            取消
          </button>
          <button
            @click="saveSettings"
            :disabled="isSaving"
            class="flex-1 py-4 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl font-semibold text-white hover:from-pink-400 hover:to-purple-500 transition-all shadow-xl shadow-pink-500/30 disabled:opacity-50 disabled:cursor-not-allowed glow-button flex items-center justify-center gap-2"
          >
            <span v-if="isSaving" class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
            <span v-else>保存设置</span>
          </button>
        </div>
      </div>

      <div v-else class="text-center py-20">
        <div class="w-24 h-24 rounded-full bg-white/5 mx-auto mb-6 flex items-center justify-center">
          <svg class="w-12 h-12 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
        </div>
        <h3 class="text-xl font-semibold text-white mb-2">伴侣未找到</h3>
        <p class="text-slate-400 mb-6">请先选择一个 AI 伴侣</p>
        <button @click="$router.push('/')" class="px-6 py-3 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl font-semibold text-white hover:from-pink-400 hover:to-purple-500 transition-all">
          返回广场
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useCompanionStore } from '@/stores/companion'

const route = useRoute()
const router = useRouter()
const companionStore = useCompanionStore()

const isSaving = ref(false)

const companion = computed(() => {
  return companionStore.getCompanionById(route.params.id as string)
})

const form = ref({
  name: '',
  avatar: '',
  category: '',
  personality: '',
  description: '',
  systemPrompt: ''
})

onMounted(() => {
  if (companion.value) {
    form.value = {
      name: companion.value.name,
      avatar: companion.value.avatar,
      category: companion.value.category,
      personality: companion.value.personality,
      description: companion.value.description,
      systemPrompt: companion.value.systemPrompt
    }
  }
})

const handleAvatarUpload = (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (event) => {
      form.value.avatar = event.target?.result as string
    }
    reader.readAsDataURL(file)
  }
}

const saveSettings = async () => {
  if (!companion.value) return
  isSaving.value = true
  
  await new Promise(resolve => setTimeout(resolve, 800))
  
  companionStore.updateCompanion(route.params.id as string, {
    name: form.value.name,
    avatar: form.value.avatar,
    category: form.value.category,
    personality: form.value.personality,
    description: form.value.description,
    systemPrompt: form.value.systemPrompt
  })
  
  isSaving.value = false
  router.back()
}
</script>
