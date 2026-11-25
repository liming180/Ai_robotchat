<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, Search } from 'lucide-vue-next'

import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import RetrieveForm from '@/components/retrieve/RetrieveForm.vue'
import RetrieveResultCard from '@/components/retrieve/RetrieveResultCard.vue'
import { api, apiErrorMessage, hasServiceToken } from '@/lib/api'
import type { CollectionItem, RetrieveResult } from '@/lib/api'
import { scoreScaleMeta } from '@/lib/format'
import { useCollectionStore } from '@/stores/collections'

const route = useRoute()
const store = useCollectionStore()

const formRef = ref<InstanceType<typeof RetrieveForm> | null>(null)
const searching = ref(false)
const result = ref<RetrieveResult | null>(null)
const lastQuery = ref('')
const collections = ref<CollectionItem[]>([])

const SERVICE_TOKEN_HINT =
  '检索接口用服务间 token 鉴权（X-Service-Token），不是登录 JWT。前端 .env.development 里的 VITE_RAG_SERVICE_TOKEN 必须与 8002 后端 SERVICE_TOKEN 一致，改完需要重启 dev server。'

async function loadOptions() {
  try {
    // 全量（内部按 100 分页遍历），避免下拉静默截断
    collections.value = await api.listAllCollections()
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '知识库列表加载失败'))
  }
}

async function run(payload: {
  query: string
  companionId?: string
  collectionIds?: string[]
  topK?: number
  scoreThreshold?: number
}) {
  searching.value = true
  lastQuery.value = payload.query
  try {
    result.value = await api.retrieve(payload)
  } catch (e) {
    const msg = apiErrorMessage(e, '检索失败')
    // service token 缺失/不一致会返回 401，登录已失效也会
    if (/x-service-token/i.test(msg) || msg.includes('401')) {
      ElMessage.error(`检索被拒绝：${msg}。${hasServiceToken ? SERVICE_TOKEN_HINT : '前端未配置 VITE_RAG_SERVICE_TOKEN。'}`)
    } else {
      ElMessage.error(msg)
    }
  } finally {
    searching.value = false
  }
}

function exportJson() {
  if (!result.value) return
  const payload = {
    query: lastQuery.value,
    scoreScale: result.value.scoreScale,
    elapsedMs: result.value.elapsedMs,
    searchedCollections: result.value.searchedCollections,
    chunks: result.value.chunks,
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `retrieve-${Date.now()}.json`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('已导出结果 JSON')
}

onMounted(async () => {
  void store.loadCompanions()
  await loadOptions()
  // 从详情页「库内检索」跳转过来时预选知识库
  const preset = route.query.collectionId
  if (typeof preset === 'string' && preset) formRef.value?.presetScope([preset])
})
</script>

<template>
  <div>
    <PageHeader
      title="检索调试"
      subtitle="直接调用 8002 /retrieve，验证召回质量、分数尺度与切片内容"
    >
      <template #actions>
        <el-button
          v-if="result"
          size="small"
          @click="exportJson"
        >
          <Download
            :size="12"
            class="mr-1"
          />
          导出 JSON
        </el-button>
      </template>
    </PageHeader>

    <div class="grid gap-4 lg:grid-cols-[400px_1fr]">
      <RetrieveForm
        ref="formRef"
        :collections="collections"
        :companions="store.companions"
        :searching="searching"
        @search="run"
      />

      <div class="min-w-0">
        <div
          v-if="result"
          class="panel p-4"
        >
          <div class="mb-2 flex flex-wrap items-center gap-2">
            <span class="flex items-center gap-1 text-[13px] font-medium text-neutral-200">
              <Search
                :size="13"
                class="text-accent"
              />
              命中 {{ result.chunks.length }} 条
            </span>
            <span class="chip mono">{{ result.elapsedMs }} ms</span>
            <span
              class="chip"
              :title="scoreScaleMeta(result.scoreScale).hint"
            >
              {{ scoreScaleMeta(result.scoreScale).label }}
            </span>
            <span class="chip">
              检索范围 {{ result.searchedCollections.length }} 个库
            </span>
          </div>

          <p class="mb-3 text-[12px] leading-4 text-neutral-600">
            {{ scoreScaleMeta(result.scoreScale).hint }}
          </p>

          <div
            v-if="result.chunks.length"
            class="flex flex-col gap-2"
          >
            <RetrieveResultCard
              v-for="(chunk, i) in result.chunks"
              :key="`${chunk.documentId}-${chunk.chunkIndex}-${i}`"
              :chunk="chunk"
              :rank="i + 1"
              :score-scale="result.scoreScale"
            />
          </div>
          <EmptyState
            v-else
            title="没有命中切片"
            description="后端返回空 chunks 是正常业务结果：换个问法，或检查该角色是否真的绑定了知识库。"
            :dashed="false"
          />
        </div>

        <EmptyState
          v-else
          title="还没有检索结果"
          description="左侧选范围、输入问题后开始检索，结果会显示分数、来源文档与命中切片。"
        />
      </div>
    </div>
  </div>
</template>