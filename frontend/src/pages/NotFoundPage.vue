<template>
  <div class="min-h-screen relative overflow-hidden flex items-center justify-center px-6">
    <!-- 背景装饰，与全站暗色风格保持一致 -->
    <div class="fixed inset-0 -z-10">
      <div class="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-pink-600/10 to-transparent"></div>
      <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"></div>
    </div>

    <div class="text-center">
      <p class="text-7xl font-bold mb-4 bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">404</p>
      <h1 class="text-2xl font-bold text-white mb-3">页面不存在</h1>
      <p class="text-slate-400 mb-8">你访问的页面可能已被移除，或者地址输入有误。</p>
      <button
        @click="$router.push('/')"
        class="px-8 py-3 bg-gradient-to-r from-pink-500 to-purple-600 rounded-2xl font-semibold text-white hover:from-pink-400 hover:to-purple-500 transition-all"
      >
        返回首页
      </button>
    </div>
  </div>
</template>
