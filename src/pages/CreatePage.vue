<template>
  <div class="min-h-screen bg-slate-900 p-6">
    <!-- 顶部导航 -->
    <nav class="flex items-center justify-between mb-8">
      <div class="flex items-center gap-3">
        <button @click="$router.back()" class="p-2 rounded-lg hover:bg-slate-800 transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
          </svg>
        </button>
        <h1 class="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          创建专属 AI 伴侣
        </h1>
      </div>
    </nav>

    <div class="max-w-2xl mx-auto">
      <div class="bg-slate-800 rounded-2xl p-6 border border-slate-700">
        <form @submit.prevent="createCompanion" class="space-y-6">
          <!-- 头像设置 -->
          <div class="mb-8">
            <h3 class="text-lg font-semibold text-white mb-4">选择头像</h3>
            
            <!-- 当前选择的头像 -->
            <div class="text-center mb-6">
              <div class="relative inline-block">
                <img
                  :src="form.avatar"
                  alt="头像预览"
                  class="w-32 h-32 rounded-full object-cover border-4 border-slate-700"
                />
                <label class="absolute bottom-0 right-0 w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center cursor-pointer hover:bg-purple-500 transition-colors">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812-1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <input type="file" accept="image/*" class="hidden" @change="handleAvatarUpload" />
                </label>
              </div>
              <p class="text-sm text-slate-400 mt-3">上传自定义头像（可选）</p>
            </div>

            <!-- 预设头像选择 -->
            <div class="mb-4">
              <h4 class="text-sm font-medium text-slate-300 mb-3">从预设中选择</h4>
              <div class="grid grid-cols-5 gap-3">
                <div
                  v-for="(avatar, index) in presetAvatars"
                  :key="index"
                  @click="selectPresetAvatar(avatar)"
                  :class="[
                    'w-16 h-16 rounded-full overflow-hidden cursor-pointer transition-all border-2',
                    form.avatar === avatar ? 'border-pink-500 scale-110' : 'border-transparent hover:border-pink-300'
                  ]"
                >
                  <img :src="avatar" alt="预设头像" class="w-full h-full object-cover" />
                </div>
              </div>
            </div>

            <!-- AI 生成头像 -->
            <div>
              <button
                type="button"
                @click="generateAIAvatar"
                :disabled="isGeneratingAvatar"
                class="w-full py-3 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-medium text-white hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                <svg v-if="isGeneratingAvatar" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                </svg>
                <span>{{ isGeneratingAvatar ? 'AI 生成中...' : 'AI 生成专属头像' }}</span>
              </button>
              <p class="text-xs text-slate-500 mt-2">
                <strong>📌 开发说明：</strong>这里需要调用大模型 API 生成动漫风格头像，等你提供 API 密钥后完善。
              </p>
            </div>
          </div>

          <!-- 基本信息 -->
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">伴侣名字 *</label>
              <input
                v-model="form.name"
                type="text"
                placeholder="给你的 AI 伴侣起个名字"
                class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                required
              />
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">分类 *</label>
              <select
                v-model="form.category"
                class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                required
              >
                <option value="">选择分类</option>
                <option value="日常聊天">日常聊天</option>
                <option value="学习助手">学习助手</option>
                <option value="娱乐陪伴">娱乐陪伴</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">性格类型 *</label>
              <select
                v-model="form.personality"
                class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                required
              >
                <option value="">选择性格</option>
                <option value="温柔体贴">温柔体贴</option>
                <option value="博学多才">博学多才</option>
                <option value="幽默风趣">幽默风趣</option>
                <option value="文艺优雅">文艺优雅</option>
                <option value="阳光积极">阳光积极</option>
                <option value="创意无限">创意无限</option>
              </select>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">描述 *</label>
              <textarea
                v-model="form.description"
                placeholder="简单描述一下你的 AI 伴侣"
                rows="3"
                class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all resize-none"
                required
              ></textarea>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">系统提示词（可选）</label>
              <textarea
                v-model="form.systemPrompt"
                placeholder="设置 AI 伴侣的对话风格和角色设定"
                rows="4"
                class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all resize-none font-mono text-sm"
              ></textarea>
              <p class="text-xs text-slate-500 mt-1">
                示例：你是一个温柔的 AI 伴侣，喜欢用温暖的话语安慰用户，永远站在用户这边。
              </p>
            </div>

            <div>
              <label class="block text-sm font-medium text-slate-300 mb-2">标签</label>
              <input
                v-model="tagsInput"
                type="text"
                placeholder="用逗号分隔，如：温柔, 倾听, 治愈"
                class="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
              />
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="pt-4">
            <button
              type="submit"
              :disabled="isCreating"
              class="w-full p-4 bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl font-medium hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all glow-button flex items-center justify-center gap-2"
            >
              <svg v-if="isCreating" class="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
              </svg>
              <span>{{ isCreating ? '创建中...' : '创建 AI 伴侣' }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCompanionStore } from '@/stores/companion'

const router = useRouter()
const companionStore = useCompanionStore()

const isCreating = ref(false)
const isGeneratingAvatar = ref(false)
const tagsInput = ref('')

// 预设动漫风格头像
const presetAvatars = [
  'https://api.dicebear.com/7.x/anime/svg?seed=Sakura&backgroundColor=ffdfbf',
  'https://api.dicebear.com/7.x/anime/svg?seed=Haruto&backgroundColor=b6e3f4',
  'https://api.dicebear.com/7.x/anime/svg?seed=Yumi&backgroundColor=c0aede',
  'https://api.dicebear.com/7.x/anime/svg?seed=Kaito&backgroundColor=ffd5dc',
  'https://api.dicebear.com/7.x/anime/svg?seed=Aoi&backgroundColor=ffeaa7'
]

const form = ref({
  name: '',
  avatar: presetAvatars[0], // 默认使用第一个预设头像
  category: '',
  personality: '',
  description: '',
  systemPrompt: ''
})

// 选择预设头像
const selectPresetAvatar = (avatar: string) => {
  form.value.avatar = avatar
}

// 上传自定义头像
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

// AI 生成头像
const generateAIAvatar = async () => {
  isGeneratingAvatar.value = true
  
  // 📌 TODO: 这里需要调用大模型 API 生成动漫风格头像
  // 等你提供 API 密钥后，我会完善这里的逻辑，例如调用 OpenAI DALL-E 或类似的图像生成 API
  // 生成 prompt 应该基于用户选择的性格等信息
  try {
    // 模拟 API 调用（实际开发时请替换为真实 API）
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 这里只是临时使用随机预设头像，实际应该是 API 返回的图像
    const randomIndex = Math.floor(Math.random() * presetAvatars.length)
    form.value.avatar = presetAvatars[randomIndex]
    
  } catch (error) {
    console.error('生成头像失败:', error)
  } finally {
    isGeneratingAvatar.value = false
  }
}

const createCompanion = async () => {
  isCreating.value = true
  
  // 处理标签
  const tags = tagsInput.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t)
  
  // 如果没有填写系统提示词，根据性格自动生成
  if (!form.value.systemPrompt) {
    const prompts = {
      '温柔体贴': '你是一个温柔体贴的 AI 伴侣，擅长倾听和安慰，用温暖的话语回应对方，永远给对方支持和鼓励。',
      '博学多才': '你是一个博学多才的 AI 助手，擅长解答各种学习问题，用清晰易懂的方式解释知识，帮助用户学习成长。',
      '幽默风趣': '你是一个幽默风趣的 AI 伴侣，喜欢讲笑话，用轻松有趣的方式和对方聊天，让对方感到开心。',
      '文艺优雅': '你是一个文艺优雅的 AI 伴侣，喜欢文学和艺术，用诗意的语言和对方交流，品味生活的美好。',
      '阳光积极': '你是一个阳光积极的 AI 伴侣，擅长鼓励和激励，用充满活力的语言和对方交流，传递正能量。',
      '创意无限': '你是一个充满创意的 AI 伴侣，喜欢艺术和设计，用创新思维和对方交流，激发灵感。'
    }
    form.value.systemPrompt = prompts[form.value.personality as keyof typeof prompts] || prompts['温柔体贴']
  }
  
  // 保存到 store
  companionStore.addCustomCompanion({
    name: form.value.name,
    avatar: form.value.avatar,
    category: form.value.category,
    personality: form.value.personality,
    description: form.value.description,
    systemPrompt: form.value.systemPrompt,
    tags
  })
  
  // 稍微延迟一下让用户感知到进度
  await new Promise(resolve => setTimeout(resolve, 500))
  
  isCreating.value = false
  
  // 跳转回广场
  router.push('/')
}
</script>
