<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { History, Search, TriangleAlert } from 'lucide-vue-next'

import { hasServiceToken } from '@/lib/api'
import type { CollectionItem, CompanionItem } from '@/lib/api'
import { useCollectionStore } from '@/stores/collections'

const props = defineProps<{
  collections: CollectionItem[]
  companions: CompanionItem[]
  searching?: boolean
}>()

const emit = defineEmits<{
  search: [payload: { query: string; companionId?: string; collectionIds?: string[]; topK?: number; scoreThreshold?: number }]
}>()

const store = useCollectionStore()
const HISTORY_KEY = 'rag_retrieve_history'

const scope = ref<'companion' | 'collections'>('companion')
const query = ref('')
const companionId = ref('')
const collectionIds = ref<string[]>([])
const topK = ref(8)
/** 后端 retrieve_top_k 默认 8；E-2 修复后 8 是召回与上下文长度的平衡点，给出常用档位 */
const TOP_K_OPTIONS = [3, 5, 8, 10, 15, 20, 30]
const useThreshold = ref(false)
const threshold = ref(0.3)
const history = ref<string[]>(loadHistory())

const canSubmit = computed(() => {
  if (!query.value.trim()) return false
  if (scope.value === 'companion') return !!companionId.value
  return collectionIds.value.length > 0
})

/** 快捷示例：检索页最容易卡在「不知道该问什么」，给几条真实用例 */
const EXAMPLES = [
  '本项目的技术栈是什么',
  '数据库连接池怎么配',
  '知识库切片长度怎么选',
]

const collectionOptions = computed(() =>
  props.collections.map((c) => ({
    value: c.id,
    label: c.name,
    companion: c.companionId ? store.companionName(c.companionId) : '未绑定',
    status: c.status,
  })),
)

function loadHistory(): string[] {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    return raw ? (JSON.parse(raw) as string[]).slice(0, 8) : []
  } catch {
    return []
  }
}

function saveHistory(q: string) {
  history.value = [q, ...history.value.filter((h) => h !== q)].slice(0, 8)
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history.value))
  } catch {
    /* 存不进去就算了 */
  }
}

function submit() {
  if (!query.value.trim()) {
    ElMessage.warning('请输入要检索的问题')
    return
  }
  if (scope.value === 'companion' && !companionId.value) {
    ElMessage.warning('请选择要检索的角色')
    return
  }
  if (scope.value === 'collections' && !collectionIds.value.length) {
    ElMessage.warning('请选择至少一个知识库')
    return
  }
  saveHistory(query.value.trim())
  emit('search', {
    query: query.value.trim(),
    companionId: scope.value === 'companion' ? companionId.value : undefined,
    collectionIds: scope.value === 'collections' ? collectionIds.value : undefined,
    topK: topK.value,
    scoreThreshold: useThreshold.value ? threshold.value : undefined,
  })
}

/** 点历史直接搜 */
function rerun(q: string) {
  query.value = q
  submit()
}

// 从其它页带参进入时自动回填范围
watch(
  () => props.collections,
  () => {
    /* 选项更新即可，不覆盖用户选择 */
  },
)

defineExpose({
  /** 详情页「库内检索」跳转时预填 collectionIds */
  presetScope(ids: string[]) {
    scope.value = 'collections'
    collectionIds.value = ids
  },
})
</script>

<template>
  <div class="panel p-5">
    <div class="mb-4 flex items-center gap-1.5 text-[13px] font-medium text-neutral-200">
      <Search
        :size="14"
        class="text-accent"
      />
      检索调试
    </div>

    <!-- 范围 -->
    <div class="mb-4">
      <p class="mb-1.5 text-[12px] text-neutral-500">
        检索范围
      </p>
      <el-radio-group v-model="scope">
        <el-radio-button value="companion">
          按角色
        </el-radio-button>
        <el-radio-button value="collections">
          指定知识库
        </el-radio-button>
      </el-radio-group>

      <div class="mt-2.5">
        <el-select
          v-if="scope === 'companion'"
          v-model="companionId"
          filterable
          placeholder="选择 AI 伴侣（自动搜它绑定的全部库）"
          class="w-full"
        >
          <el-option
            v-for="c in companions"
            :key="c.id"
            :value="c.id"
            :label="c.name"
          >
            <span class="flex items-center justify-between">
              <span>{{ c.name }}</span>
              <span class="ml-3 text-[12px] text-neutral-500">
                {{ c.id.startsWith('preset') ? '预置' : '自定义' }}
              </span>
            </span>
          </el-option>
        </el-select>
        <el-select
          v-else
          v-model="collectionIds"
          multiple
          filterable
          collapse-tags
          collapse-tags-tooltip
          placeholder="选择一个或多个知识库"
          class="w-full"
        >
          <el-option
            v-for="opt in collectionOptions"
            :key="opt.value"
            :value="opt.value"
            :label="opt.label"
          >
            <span class="flex items-center justify-between">
              <span class="truncate">{{ opt.label }}</span>
              <span class="ml-3 text-[12px] text-neutral-500">{{ opt.companion }}</span>
            </span>
          </el-option>
        </el-select>
      </div>
    </div>

    <!-- 问题 -->
    <div class="mb-4">
      <p class="mb-1.5 text-[12px] text-neutral-500">
        查询语句
      </p>
      <el-input
        v-model="query"
        type="textarea"
        :rows="3"
        placeholder="用聊天里会出现的说法提问，例如：这个项目用的技术栈是什么？"
        @keydown.ctrl.enter="submit"
        @keydown.meta.enter="submit"
      />
      <p class="mt-1 text-[12px] text-neutral-600">
        Ctrl + Enter 直接检索
      </p>
      <div class="mt-2 flex flex-wrap items-center gap-1.5">
        <span class="text-[12px] text-neutral-600">试一试</span>
        <button
          v-for="ex in EXAMPLES"
          :key="ex"
          type="button"
          class="chip max-w-full truncate transition-colors hover:border-accent/40 hover:text-accent"
          :title="`填入「${ex}」`"
          @click="query = ex"
        >
          {{ ex }}
        </button>
      </div>
    </div>

    <!-- 参数 -->
    <div class="mb-4 grid grid-cols-2 gap-3">
      <div>
        <p class="mb-1.5 text-[12px] text-neutral-500">
          返回条数 topK
        </p>
        <!--
          用下拉而不是 el-input-number：后者的加减把手只有 32×15，
          远低于 24×24 的点击区要求，触控板上很难点准。
        -->
        <el-select
          v-model="topK"
          class="w-full"
        >
          <el-option
            v-for="k in TOP_K_OPTIONS"
            :key="k"
            :label="`${k} 条`"
            :value="k"
          />
        </el-select>
      </div>
      <div>
        <p class="mb-1.5 text-[12px] text-neutral-500">
          分数阈值
        </p>
        <div class="flex items-center gap-3">
          <el-switch v-model="useThreshold" />
          <template v-if="useThreshold">
            <el-slider
              v-model="threshold"
              :min="0"
              :max="1"
              :step="0.01"
              class="!flex-1"
            />
            <span class="mono w-10 shrink-0 text-right text-[12px] text-neutral-300">
              {{ threshold.toFixed(2) }}
            </span>
          </template>
          <span
            v-else
            class="text-[12px] text-neutral-600"
          >不过滤（默认 0.0）</span>
        </div>
      </div>
    </div>

    <el-alert
      v-if="!hasServiceToken"
      class="mb-4"
      type="warning"
      :closable="false"
      show-icon
    >
      <template #title>
        <span class="flex items-center gap-1.5">
          <TriangleAlert :size="13" />
          未配置 VITE_RAG_SERVICE_TOKEN，检索会被后端 401 拦截
        </span>
      </template>
      在 .env.development 里补上与 8002 一致的 token 后重启 dev server。
    </el-alert>

    <el-button
      class="w-full"
      type="primary"
      size="large"
      :disabled="!canSubmit"
      :loading="searching"
      @click="submit"
    >
      <Search
        :size="15"
        class="mr-1.5"
      />
      检索
    </el-button>

    <!-- 历史 -->
    <div
      v-if="history.length"
      class="mt-4 border-t border-ink-700/70 pt-3"
    >
      <p class="mb-2 flex items-center gap-1 text-[12px] text-neutral-600">
        <History :size="11" />
        最近查询
      </p>
      <div class="flex flex-wrap gap-1.5">
        <button
          v-for="h in history"
          :key="h"
          type="button"
          class="chip max-w-full truncate transition-colors hover:border-accent/40 hover:text-accent"
          :title="h"
          @click="rerun(h)"
        >
          {{ h }}
        </button>
      </div>
    </div>
  </div>
</template>