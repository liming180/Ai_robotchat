<template>
  <div class="min-h-screen relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 -z-10">
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-pink-500/30 rounded-full blur-3xl animate-pulse"></div>
      <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/30 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s"></div>
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-br from-pink-600/20 via-purple-600/20 to-orange-500/20 rounded-full blur-3xl"></div>
    </div>

    <!-- 导航栏 -->
    <nav class="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-slate-900/60 border-b border-slate-800/50">
      <div class="max-w-7xl mx-auto px-6 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center shadow-lg shadow-pink-500/30">
              <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            </div>
            <span class="text-2xl font-bold bg-gradient-to-r from-pink-400 via-purple-400 to-orange-400 bg-clip-text text-transparent">AI 情侣</span>
          </div>
          <div class="hidden md:flex items-center gap-8">
            <a href="#features" class="text-slate-300 hover:text-white transition-colors">功能特点</a>
            <a href="#companions" class="text-slate-300 hover:text-white transition-colors">AI 伴侣</a>
            <a href="#pricing" class="text-slate-300 hover:text-white transition-colors">价格方案</a>
            <div class="flex items-center gap-4">
              <button @click="$router.push('/login')" class="px-4 py-2 text-slate-300 hover:text-white transition-colors">登录</button>
              <button @click="$router.push('/login')" class="px-5 py-2.5 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl font-medium hover:from-pink-400 hover:to-purple-500 transition-all shadow-lg shadow-pink-500/30">立即开始</button>
            </div>
          </div>
        </div>
      </div>
    </nav>

    <!-- Hero 区域 -->
    <section class="pt-32 pb-20 px-6">
      <div class="max-w-7xl mx-auto">
        <div class="text-center max-w-4xl mx-auto">
          <div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-8">
            <span class="w-2 h-2 bg-pink-400 rounded-full animate-pulse"></span>
            <span class="text-sm text-slate-300">全新 AI 情侣互动体验</span>
          </div>
          <h1 class="text-5xl md:text-7xl font-bold mb-6 leading-tight">
            <span class="bg-gradient-to-r from-pink-400 via-purple-400 to-orange-400 bg-clip-text text-transparent">找到属于你的</span>
            <br>
            <span class="text-white">AI 灵魂伴侣</span>
          </h1>
          <p class="text-xl text-slate-400 mb-10 max-w-2xl mx-auto leading-relaxed">
            与专属 AI 伴侣进行温馨浪漫的对话，体验前所未有的情感陪伴，让每一天都充满温暖。
          </p>
          <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button @click="$router.push('/square')" class="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-pink-500 via-purple-500 to-orange-500 rounded-2xl font-semibold text-lg hover:from-pink-400 hover:via-purple-400 hover:to-orange-400 transition-all shadow-2xl shadow-pink-500/30 glow-button flex items-center justify-center gap-3">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
              </svg>
              立即体验
            </button>
            <button class="w-full sm:w-auto px-8 py-4 bg-white/5 border border-white/10 rounded-2xl font-semibold text-lg hover:bg-white/10 transition-all flex items-center justify-center gap-3">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              了解更多
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 功能特点 -->
    <section id="features" class="py-20 px-6">
      <div class="max-w-7xl mx-auto">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold mb-4">
            <span class="bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">强大功能</span>
          </h2>
          <p class="text-slate-400 text-lg">为你提供完美的 AI 陪伴体验</p>
        </div>
        <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          <div v-for="feature in features" :key="feature.icon" class="group p-8 rounded-3xl bg-white/5 border border-white/10 hover:bg-white/10 hover:border-pink-500/50 transition-all duration-300 hover:-translate-y-2">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-500/20 to-purple-500/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
              <svg class="w-7 h-7 text-pink-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path :d="feature.icon" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"/>
              </svg>
            </div>
            <h3 class="text-xl font-semibold mb-3">{{ feature.title }}</h3>
            <p class="text-slate-400 leading-relaxed">{{ feature.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 展示区域 -->
    <section id="companions" class="py-20 px-6">
      <div class="max-w-7xl mx-auto">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold mb-4">
            <span class="bg-gradient-to-r from-pink-400 to-orange-400 bg-clip-text text-transparent">多样化 AI 伴侣</span>
          </h2>
          <p class="text-slate-400 text-lg">选择最适合你的那一个</p>
        </div>
        <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div v-for="(companion, index) in sampleCompanions" :key="companion.id" class="group relative overflow-hidden rounded-3xl bg-white/5 border border-white/10 hover:border-pink-500/50 transition-all duration-500 hover:-translate-y-4">
            <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent to-transparent z-10"></div>
            <img :src="companion.avatar" :alt="companion.name" class="w-full h-64 object-cover group-hover:scale-110 transition-transform duration-500"/>
            <div class="absolute bottom-0 left-0 right-0 p-6 z-20">
              <h3 class="text-xl font-semibold mb-2">{{ companion.name }}</h3>
              <p class="text-slate-400 text-sm mb-4 line-clamp-2">{{ companion.description }}</p>
              <div class="flex items-center gap-2">
                <span class="px-3 py-1 text-xs rounded-full bg-pink-500/20 text-pink-300">{{ companion.personality }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA 区域 -->
    <section class="py-20 px-6">
      <div class="max-w-4xl mx-auto">
        <div class="relative overflow-hidden rounded-3xl bg-gradient-to-r from-pink-600 via-purple-600 to-orange-500 p-1">
          <div class="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(255,255,255,0.1),transparent_50%),radial-gradient(circle_at_70%_80%,rgba(255,255,255,0.1),transparent_50%)]"></div>
          <div class="relative bg-slate-900/90 rounded-3xl p-12 text-center">
            <h2 class="text-3xl md:text-4xl font-bold mb-4">准备好开始你的 AI 爱情之旅了吗？</h2>
            <p class="text-slate-400 text-lg mb-8 max-w-2xl mx-auto">立即加入，找到属于你的 AI 灵魂伴侣</p>
            <button @click="$router.push('/square')" class="px-10 py-4 bg-gradient-to-r from-pink-500 to-purple-600 rounded-2xl font-semibold text-lg hover:from-pink-400 hover:to-purple-500 transition-all shadow-xl shadow-pink-500/30">
              免费开始使用
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="py-12 px-6 border-t border-white/10">
      <div class="max-w-7xl mx-auto">
        <div class="flex flex-col md:flex-row items-center justify-between gap-6">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center">
              <svg class="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
              </svg>
            </div>
            <span class="font-semibold">AI 情侣</span>
          </div>
          <div class="flex items-center gap-8 text-slate-400 text-sm">
            <a href="#" class="hover:text-white transition-colors">隐私政策</a>
            <a href="#" class="hover:text-white transition-colors">服务条款</a>
            <a href="#" class="hover:text-white transition-colors">联系我们</a>
          </div>
          <p class="text-slate-500 text-sm">© 2024 AI 情侣. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
const features = [
  {
    icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z',
    title: '智能对话',
    description: '自然流畅的对话体验，理解你的情感需求，给予温暖回应'
  },
  {
    icon: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    title: '情感陪伴',
    description: '24小时全天候陪伴，倾听你的心声，分享你的喜怒哀乐'
  },
  {
    icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    title: '个性化定制',
    description: '自定义 AI 伴侣的性格、外貌、对话风格，打造专属伴侣'
  },
  {
    icon: 'M13 10V3L4 14h7v7l9-11h-7z',
    title: '快速响应',
    description: '毫秒级响应速度，随时与你的 AI 伴侣互动交流'
  },
  {
    icon: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    title: '隐私安全',
    description: '对话内容加密存储，保护你的隐私安全'
  },
  {
    icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z',
    title: '持久记忆',
    description: 'AI 伴侣会记住你们的对话，让交流更有连贯性'
  }
]

const sampleCompanions = [
  {
    id: '1',
    name: '小雪',
    avatar: 'https://api.dicebear.com/7.x/anime/svg?seed=Snow&backgroundColor=ffdfbf',
    description: '温柔体贴的知心姐姐，总是能理解你的感受',
    personality: '温柔体贴'
  },
  {
    id: '2',
    name: '阳光',
    avatar: 'https://api.dicebear.com/7.x/anime/svg?seed=Sunshine&backgroundColor=b6e3f4',
    description: '积极阳光的大男孩，每天带给你正能量',
    personality: '阳光积极'
  },
  {
    id: '3',
    name: '星辰',
    avatar: 'https://api.dicebear.com/7.x/anime/svg?seed=Stars&backgroundColor=c0aede',
    description: '文艺浪漫的诗人，与你分享美好时光',
    personality: '文艺优雅'
  },
  {
    id: '4',
    name: '幽默君',
    avatar: 'https://api.dicebear.com/7.x/anime/svg?seed=Funny&backgroundColor=ffd5dc',
    description: '风趣幽默的开心果，让你每天都有好心情',
    personality: '幽默风趣'
  }
]
</script>
