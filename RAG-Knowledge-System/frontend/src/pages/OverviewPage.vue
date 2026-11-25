<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ArrowRight, Database, FileStack, RefreshCw, Search, Sparkles } from 'lucide-vue-next'

import PageHeader from '@/components/layout/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { api, apiErrorMessage } from '@/lib/api'
import type { CollectionItem } from '@/lib/api'
import { formatNumber, formatRelative } from '@/lib/format'
import { useCollectionStore } from '@/stores/collections'

const store = useCollectionStore()

const loading = ref(false)
const error = ref('')
const collections = ref<CollectionItem[]>([])

const totals = computed(() => {
  const list = collections.value
  return {
    collections: list.length,
    documents: list.reduce((n, c) => n + (c.documentCount || 0), 0),
    chunks: list.reduce((n, c) => n + (c.chunkCount || 0), 0),
    active: list.filter((c) => c.status === 'active').length,
  }
})

/** 按绑定的角色聚合，未绑定的单列一组 */
const byCompanion = computed(() => {
  const map = new Map<string, { name: string; count: number; chunks: number }>()
  for (const c of collections.value) {
    const key = c.companionId || '__none__'
    const entry = map.get(key) || {
      name: c.companionId ? store.companionName(c.companionId) : '未绑定角色',
      count: 0,
      chunks: 0,
    }
    entry.count += 1
    entry.chunks += c.chunkCount || 0
    map.set(key, entry)
  }
  return [...map.values()].sort((a, b) => b.count - a.count).slice(0, 6)
})

const maxGroupCount = computed(() => Math.max(1, ...byCompanion.value.map((g) => g.count)))

const recent = computed(() =>
  [...collections.value]
    .sort((a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''))
    .slice(0, 5),
)

async function load(force = false) {
  loading.value = true
  error.value = ''
  try {
    if (force) store.invalidate()
    // 概览页需要计数，必须拿全量（listAllCollections 内部按 100 分页遍历）
    collections.value = await api.listAllCollections()
    store.allLoaded = true
  } catch (e) {
    error.value = apiErrorMessage(e, '知识库列表加载失败')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void store.loadCompanions()
  void load()
})
</script>

<template>
  <div>
    <PageHeader
      title="概览"
      subtitle="全部知识库的规模、角色分布与最近更新"
    >
      <template #actions>
        <el-button
          :loading="loading"
          @click="load(true)"
        >
          <RefreshCw
            :size="13"
            class="mr-1"
          />
          刷新
        </el-button>
        <RouterLink to="/collections">
          <el-button type="primary">
            <Database
              :size="13"
              class="mr-1"
            />
            管理知识库
          </el-button>
        </RouterLink>
      </template>
    </PageHeader>

    <el-alert
      v-if="error"
      class="mb-5"
      type="error"
      :title="error"
      :closable="false"
      show-icon
    />

    <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="知识库"
        :value="formatNumber(totals.collections)"
        tone="accent"
        :hint="`${totals.active} 个启用中`"
      />
      <StatCard
        label="文档总数"
        :value="formatNumber(totals.documents)"
        hint="含文件上传与手动录入"
      />
      <StatCard
        label="切片总数"
        :value="formatNumber(totals.chunks)"
        hint="已向量化入库的块数"
      />
      <StatCard
        label="平均切片/文档"
        :value="totals.documents ? Math.round(totals.chunks / totals.documents) : 0"
        hint="切片过大易稀释语义，过小则上下文不足"
      />
    </div>

    <div class="mt-4 grid gap-4 lg:grid-cols-[1.15fr_1fr]">
      <!-- 角色分布 -->
      <section class="panel p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-[13px] font-medium text-neutral-200">
            按角色分布
          </h2>
          <span class="subtle">{{ byCompanion.length }} 组</span>
        </div>
        <div
          v-if="byCompanion.length"
          class="flex flex-col gap-3"
        >
          <div
            v-for="g in byCompanion"
            :key="g.name"
            class="flex items-center gap-3"
          >
            <span
              class="w-[104px] shrink-0 truncate text-[12px] text-neutral-400"
              :title="g.name"
            >
              {{ g.name }}
            </span>
            <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-ink-800">
              <div
                class="h-full rounded-full bg-accent/70"
                :style="{ width: `${Math.max(6, (g.count / maxGroupCount) * 100)}%` }"
              />
            </div>
            <span class="mono w-[86px] shrink-0 text-right text-neutral-500">
              {{ g.count }} 库 / {{ formatNumber(g.chunks) }}
            </span>
          </div>
        </div>
        <EmptyState
          v-else
          title="还没有知识库"
          description="新建一个知识库并上传文档，聊天时 AI 伴侣才能检索到。"
          :dashed="false"
        >
          <template #action>
            <RouterLink
              to="/collections"
              class="inline-flex"
            >
              <el-button
                size="small"
                class="!h-8"
              >
                去新建
              </el-button>
            </RouterLink>
          </template>
        </EmptyState>
      </section>

      <!-- 最近更新 -->
      <section class="panel p-5">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-[13px] font-medium text-neutral-200">
            最近更新
          </h2>
          <RouterLink
            to="/collections"
            class="-my-1 flex items-center gap-0.5 rounded px-1.5 py-1 text-[12px] text-neutral-500 hover:bg-ink-800 hover:text-accent"
          >
            全部
            <ArrowRight :size="11" />
          </RouterLink>
        </div>
        <ul
          v-if="recent.length"
          class="-my-1"
        >
          <li
            v-for="c in recent"
            :key="c.id"
          >
            <RouterLink
              :to="`/collections/${c.id}`"
              class="flex items-center gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-ink-800/70"
            >
              <span class="grid size-7 shrink-0 place-items-center rounded-md bg-ink-800 text-neutral-500">
                <FileStack :size="13" />
              </span>
              <span class="min-w-0 flex-1">
                <span class="block truncate text-[13px] text-neutral-200">{{ c.name }}</span>
                <span class="block truncate text-[12px] text-neutral-600">
                  {{ c.documentCount }} 文档 · {{ formatNumber(c.chunkCount) }} 切片
                </span>
              </span>
              <StatusTag :status="c.status" />
              <span class="shrink-0 text-[12px] text-neutral-600">{{ formatRelative(c.updatedAt) }}</span>
            </RouterLink>
          </li>
        </ul>
        <EmptyState
          v-else
          title="暂无记录"
          description="新建知识库后这里会显示最近改动。"
          :dashed="false"
        />
      </section>
    </div>

    <!-- 快捷入口 -->
    <div class="mt-4 grid gap-3 sm:grid-cols-2">
      <RouterLink
        to="/retrieve"
        class="panel group flex items-center gap-3 px-5 py-4 transition-colors hover:border-accent/40"
      >
        <span class="grid size-9 place-items-center rounded-lg bg-accent/10 text-accent ring-1 ring-accent/25">
          <Search :size="16" />
        </span>
        <span class="min-w-0">
          <span class="block text-[13px] text-neutral-200">检索调试</span>
          <span class="block text-[12px] text-neutral-600">指定角色或知识库直接跑一次召回，看分数与命中切片</span>
        </span>
        <ArrowRight
          :size="14"
          class="ml-auto text-neutral-600 transition-colors group-hover:text-accent"
        />
      </RouterLink>
      <RouterLink
        to="/collections"
        class="panel group flex items-center gap-3 px-5 py-4 transition-colors hover:border-accent/40"
      >
        <span class="grid size-9 place-items-center rounded-lg bg-ink-800 text-neutral-400 ring-1 ring-ink-600">
          <Sparkles :size="16" />
        </span>
        <span class="min-w-0">
          <span class="block text-[13px] text-neutral-200">新建知识库</span>
          <span class="block text-[12px] text-neutral-600">绑定角色、设定切片参数与 JSON 解析规则</span>
        </span>
        <ArrowRight
          :size="14"
          class="ml-auto text-neutral-600 transition-colors group-hover:text-accent"
        />
      </RouterLink>
    </div>
  </div>
</template>