<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="flex h-full flex-col">
    <header
      v-if="!$route.meta.public"
      class="flex items-center gap-6 border-b border-neutral-800 px-6 py-3"
    >
      <span class="text-lg font-semibold text-accent">RAG 知识库</span>
      <nav class="flex gap-4 text-sm text-neutral-300">
        <RouterLink to="/collections" class="hover:text-accent">知识库</RouterLink>
        <RouterLink to="/retrieve" class="hover:text-accent">检索调试</RouterLink>
      </nav>
      <div class="ml-auto flex items-center gap-3 text-sm text-neutral-400">
        <span>{{ auth.userEmail }}</span>
        <el-button size="small" @click="logout">退出</el-button>
      </div>
    </header>
    <main class="flex-1 overflow-auto p-6">
      <RouterView />
    </main>
  </div>
</template>
