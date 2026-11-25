<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Boxes, Database, LayoutDashboard, Search } from 'lucide-vue-next'

import { useCollectionStore } from '@/stores/collections'

const route = useRoute()
const store = useCollectionStore()

const navs = [
  { to: '/overview', label: '概览', icon: LayoutDashboard },
  { to: '/collections', label: '知识库', icon: Database },
  { to: '/retrieve', label: '检索调试', icon: Search },
]

/** 当前激活项：详情页也要让「知识库」保持高亮 */
const activeKey = computed(() => {
  if (route.path.startsWith('/collections')) return '/collections'
  if (route.path.startsWith('/retrieve')) return '/retrieve'
  return '/overview'
})

const healthLabel = computed(() => {
  if (store.healthChecking && !store.health) return '检测中…'
  if (!store.health?.reachable) return '8002 离线'
  if (store.milvusDown) return '向量库不可用'
  return `8002 在线 · ${store.health.data?.version || ''}`.trim()
})

/** 绿=可检索；黄=进程在但向量库挂了（检索必失败）；红=连不上 */
const dotClass = computed(() => {
  if (!store.health?.reachable) return store.healthChecking ? 'bg-neutral-500' : 'bg-rose-400'
  return store.vectorReady ? 'bg-emerald-400' : 'bg-amber-400'
})

/** 悬停给出原因：503 的 message 里带 Milvus 的具体错误 */
const healthTip = computed(() => {
  if (!store.health?.reachable) return store.healthError || '8002 未启动'
  if (store.milvusDown) return store.healthError || 'Milvus 不可用，检索会失败；请确认 milvus-standalone 容器在运行'
  return `${store.health.data?.service || 'RAG'} · 向量后端 ${store.health.data?.vectorStore || '?'}`
})

onMounted(() => {
  void store.ping()
})
</script>

<template>
  <aside
    class="flex w-[228px] shrink-0 flex-col border-r border-ink-700/80 bg-ink-900/60"
  >
    <div class="flex items-center gap-2.5 px-5 py-[18px]">
      <span
        class="grid size-8 place-items-center rounded-lg bg-accent/15 text-accent ring-1 ring-accent/30"
      >
        <Boxes :size="17" />
      </span>
      <div class="leading-tight">
        <p class="text-[13px] font-semibold text-neutral-100">
          RAG 知识库
        </p>
        <p class="text-[12px] text-neutral-500">
          Knowledge Console
        </p>
      </div>
    </div>

    <nav class="flex flex-col gap-1 px-3 py-2">
      <RouterLink
        v-for="nav in navs"
        :key="nav.to"
        :to="nav.to"
        class="nav-item"
        :class="{ 'nav-item-active': activeKey === nav.to }"
      >
        <component
          :is="nav.icon"
          :size="15"
          class="shrink-0"
        />
        <span>{{ nav.label }}</span>
      </RouterLink>
    </nav>

    <div class="mt-auto border-t border-ink-700/70 px-4 py-3">
      <div class="flex items-center gap-2">
        <el-tooltip
          :content="healthTip"
          placement="top"
          :show-after="200"
        >
          <span
            class="size-1.5 shrink-0 rounded-full"
            :class="dotClass"
          />
        </el-tooltip>
        <span class="truncate text-[12px] text-neutral-500">{{ healthLabel }}</span>
        <button
          class="-my-1 ml-auto rounded px-1.5 py-1 text-[12px] text-neutral-600 transition-colors hover:bg-ink-800 hover:text-accent"
          type="button"
          @click="store.ping()"
        >
          重测
        </button>
      </div>
    </div>
  </aside>
</template>