<template>
  <nav class="fixed top-0 left-0 right-0 z-50 backdrop-blur-xl bg-slate-900/60 border-b border-slate-800/50">
    <div class="max-w-7xl mx-auto px-6 py-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3 cursor-pointer" @click="$router.push('/')">
          <div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-pink-500 to-purple-600 flex items-center justify-center shadow-lg shadow-pink-500/30">
            <svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
          <span class="text-2xl font-bold bg-gradient-to-r from-pink-400 via-purple-400 to-orange-400 bg-clip-text text-transparent">AI 情侣</span>
        </div>
        
        <div class="hidden md:flex items-center gap-8">
          <a href="#features" class="text-slate-300 hover:text-white transition-colors">功能特点</a>
          <router-link to="/square" class="text-slate-300 hover:text-white transition-colors">AI 伴侣</router-link>
          <a href="#pricing" class="text-slate-300 hover:text-white transition-colors">价格方案</a>
          
          <!-- 根据登录状态显示不同内容 -->
          <div class="flex items-center gap-4">
            <template v-if="userStore.isAuthenticated">
              <!-- 用户已登录：显示头像和下拉菜单 -->
              <div class="relative" @click="toggleMenu">
                <button class="flex items-center gap-2 hover:opacity-80 transition-opacity">
                  <img 
                    :src="userStore.user?.avatar || defaultUserAvatar" 
                    :alt="userStore.user?.name || '用户'" 
                    @error="handleUserAvatarError"
                    class="w-10 h-10 rounded-full border-2 border-pink-500/50 object-cover"
                  />
                  <span class="text-slate-300 hidden lg:inline">{{ userStore.user?.name }}</span>
                  <svg class="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                  </svg>
                </button>
                
                <!-- 下拉菜单 -->
                <div v-if="menuOpen" class="absolute right-0 mt-2 w-48 bg-slate-800/95 backdrop-blur-xl rounded-2xl border border-white/10 shadow-xl overflow-hidden">
                  <div class="p-4 border-b border-white/10">
                    <p class="font-medium text-white">{{ userStore.user?.name }}</p>
                    <p class="text-xs text-slate-400 mt-1">{{ userStore.user?.email }}</p>
                  </div>
                  <button 
                    @click="handleLogout" 
                    class="w-full px-4 py-3 text-left text-slate-300 hover:bg-white/10 hover:text-white transition-colors flex items-center gap-2"
                  >
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
                    </svg>
                    退出登录
                  </button>
                </div>
              </div>
            </template>
            
            <template v-else>
              <!-- 用户未登录：显示登录/注册按钮 -->
              <button @click="$router.push('/login')" class="px-4 py-2 text-slate-300 hover:text-white transition-colors">登录</button>
              <button @click="$router.push('/login')" class="px-5 py-2.5 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl font-medium hover:from-pink-400 hover:to-purple-500 transition-all shadow-lg shadow-pink-500/30">立即开始</button>
            </template>
          </div>
        </div>
        
        <!-- 移动端菜单按钮 -->
        <button class="md:hidden text-white" @click="toggleMobileMenu">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
          </svg>
        </button>
      </div>
      
      <!-- 移动端菜单 -->
      <div v-if="mobileMenuOpen" class="md:hidden mt-4 pb-4 border-t border-white/10 pt-4">
        <div class="flex flex-col gap-4">
          <a href="#features" class="text-slate-300 hover:text-white transition-colors">功能特点</a>
          <router-link to="/square" class="text-slate-300 hover:text-white transition-colors">AI 伴侣</router-link>
          <a href="#pricing" class="text-slate-300 hover:text-white transition-colors">价格方案</a>
          
          <div class="pt-2 border-t border-white/10">
            <template v-if="userStore.isAuthenticated">
              <div class="flex items-center gap-3 mb-4">
                <img 
                  :src="userStore.user?.avatar || defaultUserAvatar" 
                  :alt="userStore.user?.name || '用户'" 
                  @error="handleUserAvatarError"
                  class="w-10 h-10 rounded-full border-2 border-pink-500/50 object-cover"
                />
                <div>
                  <p class="font-medium text-white">{{ userStore.user?.name }}</p>
                  <p class="text-xs text-slate-400">{{ userStore.user?.email }}</p>
                </div>
              </div>
              <button @click="handleLogout" class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl text-slate-300 hover:text-white transition-colors">
                退出登录
              </button>
            </template>
            
            <template v-else>
              <div class="flex gap-3">
                <button @click="$router.push('/login')" class="flex-1 px-4 py-3 text-slate-300 hover:text-white transition-colors">登录</button>
                <button @click="$router.push('/login')" class="flex-1 px-4 py-3 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl font-medium hover:from-pink-400 hover:to-purple-500 transition-all">
                  立即开始
                </button>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { createSvgAvatarDataUrl } from '@/lib/avatar'

const userStore = useUserStore()
const router = useRouter()

const menuOpen = ref(false)
const mobileMenuOpen = ref(false)
const defaultUserAvatar = createSvgAvatarDataUrl({ seed: 'user-default', label: '你' })

const handleUserAvatarError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (!img) return
  const name = userStore.user?.name || '你'
  const label = name.trim().slice(-1) || '你'
  img.src = createSvgAvatarDataUrl({ seed: `user-${label}`, label })
}

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const toggleMobileMenu = () => {
  mobileMenuOpen.value = !mobileMenuOpen.value
}

const handleLogout = () => {
  userStore.logout()
  menuOpen.value = false
  mobileMenuOpen.value = false
  router.push('/')
}

const handleClickOutside = (e: MouseEvent) => {
  const target = e.target as HTMLElement
  if (!target.closest('.relative')) {
    menuOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>
