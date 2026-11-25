<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ChevronRight, LogOut } from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth'
import { useCollectionStore } from '@/stores/collections'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const collections = useCollectionStore()

/** 面包屑由路由 meta 提供；详情页的动态段取 store 里当前库名。 */
const crumbs = computed(() => {
  const list: { label: string; to?: string }[] = []
  const root = route.meta.crumb as string | undefined
  if (root) list.push({ label: root, to: route.meta.crumbTo as string | undefined })
  const name = collections.currentMeta?.name as string | undefined
  const tail = route.name === 'collection-detail' ? name || '知识库详情' : undefined
  if (tail) list.push({ label: tail })
  return list
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <header
    class="flex h-[52px] shrink-0 items-center gap-3 border-b border-ink-700/80 bg-ink-900/40 px-6 backdrop-blur"
  >
    <nav class="flex items-center gap-1.5 text-[13px]">
      <template
        v-for="(c, i) in crumbs"
        :key="i"
      >
        <ChevronRight
          v-if="i > 0"
          :size="13"
          class="text-neutral-600"
        />
        <RouterLink
          v-if="c.to"
          :to="c.to"
          class="-mx-1 rounded px-1.5 py-1 text-neutral-500 transition-colors hover:bg-ink-800 hover:text-neutral-200"
        >
          {{ c.label }}
        </RouterLink>
        <span
          v-else
          :class="i === crumbs.length - 1 ? 'text-neutral-200' : 'text-neutral-500'"
        >
          {{ c.label }}
        </span>
      </template>
    </nav>

    <div class="ml-auto flex items-center gap-3">
      <span
        class="grid size-7 place-items-center rounded-full bg-ink-800 text-[12px] font-medium text-neutral-300 ring-1 ring-ink-600"
        :title="auth.userEmail"
      >
        {{ auth.userInitial }}
      </span>
      <span class="hidden max-w-[180px] truncate text-[12px] text-neutral-500 sm:block">
        {{ auth.userEmail }}
      </span>
      <button
        type="button"
        class="flex items-center gap-1 rounded-md px-2 py-1 text-[12px] text-neutral-500 transition-colors hover:bg-ink-800 hover:text-neutral-200"
        @click="logout"
      >
        <LogOut :size="13" />
        退出
      </button>
    </div>
  </header>
</template>