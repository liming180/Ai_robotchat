<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, FilePlus2, RefreshCw, Settings2 } from 'lucide-vue-next'

import PageHeader from '@/components/layout/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import StatCard from '@/components/common/StatCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import UploadPanel from '@/components/document/UploadPanel.vue'
import DocumentTable from '@/components/document/DocumentTable.vue'
import DocumentDrawer from '@/components/document/DocumentDrawer.vue'
import ManualDocDrawer from '@/components/document/ManualDocDrawer.vue'
import CollectionFormDrawer from '@/components/collection/CollectionFormDrawer.vue'
import RetrieveForm from '@/components/retrieve/RetrieveForm.vue'
import RetrieveResultCard from '@/components/retrieve/RetrieveResultCard.vue'
import { api, apiErrorMessage } from '@/lib/api'
import type { CollectionItem, DocumentItem, RetrieveResult } from '@/lib/api'
import { formatNumber, scoreScaleMeta } from '@/lib/format'
import { useCollectionStore } from '@/stores/collections'
import { useTaskStore } from '@/stores/tasks'

const route = useRoute()
const router = useRouter()
const store = useCollectionStore()
const taskStore = useTaskStore()

const collectionId = computed(() => String(route.params.id || ''))
const activeTab = ref('documents')

const loading = ref(true)
const error = ref('')
const collection = ref<CollectionItem | null>(null)
const documents = ref<DocumentItem[]>([])
const docsLoading = ref(false)

const openDocId = ref('')
const manualOpen = ref(false)
const manualEditing = ref<DocumentItem | null>(null)
const editOpen = ref(false)

// 库内检索
const searching = ref(false)
const retrieveResult = ref<RetrieveResult | null>(null)
const retrieveQuery = ref('')

const stats = computed(() => ({
  documents: collection.value?.documentCount ?? documents.value.length,
  chunks: collection.value?.chunkCount ?? 0,
  done: documents.value.filter((d) => d.status === 'completed').length,
  failed: documents.value.filter((d) => d.status === 'failed' || d.status === 'error').length,
}))

async function loadCollection() {
  loading.value = true
  error.value = ''
  try {
    const item = await api.getCollection(collectionId.value)
    collection.value = item
    // 面包屑动态段用 store 里的当前库名
    store.currentMeta = { name: item.name }
  } catch (e) {
    error.value = apiErrorMessage(e, '知识库加载失败')
  } finally {
    loading.value = false
  }
}

async function loadDocuments() {
  if (!collectionId.value) return
  docsLoading.value = true
  try {
    const res = await api.listDocuments(collectionId.value)
    documents.value = res.items || []
    // 刷新/重进页面时恢复未完成任务的轮询（旧实现刷新即丢失进度）
    taskStore.restoreFromDocuments(
      documents.value.map((d) => ({
        taskId: d.taskId,
        status: d.status,
        id: d.id,
        progress: d.progress,
        chunkCount: d.chunkCount,
      })),
    )
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '文档列表加载失败'))
  } finally {
    docsLoading.value = false
  }
}

async function reload() {
  await Promise.all([loadCollection(), loadDocuments()])
}

function onUploaded(taskIds: { taskId: string }[]) {
  taskStore.watch(taskIds.map((t) => t.taskId))
  void loadDocuments()
}

function onManualSaved(taskId: string) {
  taskStore.watch([taskId])
  void loadDocuments()
}

function onDocEdit(doc: DocumentItem) {
  manualEditing.value = doc
  openDocId.value = ''
  manualOpen.value = true
}

function openManualCreate() {
  manualEditing.value = null
  manualOpen.value = true
}

async function runRetrieve(payload: {
  query: string
  collectionIds?: string[]
  topK?: number
  scoreThreshold?: number
}) {
  searching.value = true
  retrieveQuery.value = payload.query
  try {
    retrieveResult.value = await api.retrieve(payload)
    if (!retrieveResult.value.chunks.length) {
      ElMessage.info('没有命中任何切片，试着换一种问法或放宽阈值')
    }
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '检索失败'))
  } finally {
    searching.value = false
  }
}

// 任务进入终态后自动刷新文档列表与统计
watch(
  () => taskStore.lastSettledAt,
  () => {
    void reload()
  },
)

onMounted(async () => {
  await store.loadCompanions()
  await reload()
})

onBeforeUnmount(() => {
  store.currentMeta = null
})
</script>

<template>
  <div>
    <div
      v-if="error"
      class="mb-4"
    >
      <el-alert
        type="error"
        :title="error"
        :closable="false"
        show-icon
      />
      <el-button
        class="mt-3"
        size="small"
        @click="reload"
      >
        <RefreshCw
          :size="12"
          class="mr-1"
        />
        重试
      </el-button>
    </div>

    <template v-else>
      <PageHeader
        :title="collection?.name || '加载中…'"
        :subtitle="collection?.description || ''"
      >
        <template #actions>
          <el-button
            size="small"
            @click="router.push('/collections')"
          >
            <ArrowLeft
              :size="12"
              class="mr-1"
            />
            返回列表
          </el-button>
          <el-button
            size="small"
            @click="reload"
          >
            <RefreshCw
              :size="12"
              class="mr-1"
            />
            刷新
          </el-button>
          <el-button
            size="small"
            type="primary"
            @click="editOpen = true"
          >
            <Settings2
              :size="12"
              class="mr-1"
            />
            设置
          </el-button>
        </template>
      </PageHeader>

      <div
        v-if="collection && !collection.companionId"
        class="mb-4"
      >
        <el-alert
          type="warning"
          :closable="false"
          show-icon
          title="这个库没有绑定角色，文档会入库失败"
        >
          <template #default>
            向量库存库要求 companion_id 非空（Milvus 用它做分区键），未绑定的库上传文档会在
            「向量化」阶段报错。点右上角「设置」补一个角色即可。
          </template>
        </el-alert>
      </div>

      <div
        v-if="collection"
        class="mb-4 flex flex-wrap items-center gap-2"
      >
        <StatusTag
          :status="collection.status"
          size="md"
        />
        <span class="chip">{{ collection.companionId ? store.companionName(collection.companionId) : '未绑定角色' }}</span>
        <span class="chip mono">{{ collection.embeddingModel }} · {{ collection.embeddingDim }}d</span>
        <span class="chip mono">切片 {{ collection.chunkSize }} / 重叠 {{ collection.chunkOverlap }}</span>
        <span
          v-if="collection.parserConfig?.itemsPath"
          class="chip mono"
        >
          itemsPath: {{ collection.parserConfig.itemsPath }}
        </span>
      </div>

      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="文档"
          :value="formatNumber(stats.documents)"
          tone="accent"
        />
        <StatCard
          label="切片"
          :value="formatNumber(stats.chunks)"
          hint="已向量化入库"
        />
        <StatCard
          label="已完成"
          :value="formatNumber(stats.done)"
          :hint="`${stats.failed} 篇失败`"
        />
        <StatCard
          label="平均切片/文档"
          :value="stats.documents ? Math.round(stats.chunks / stats.documents) : 0"
          hint="偏小则上下文不足，偏大则语义被稀释"
        />
      </div>

      <el-tabs
        v-model="activeTab"
        class="mt-5"
      >
        <!-- 文档 -->
        <el-tab-pane
          label="文档"
          name="documents"
        >
          <div class="grid gap-4 lg:grid-cols-[1fr_340px]">
            <div class="panel min-w-0 p-4">
              <div class="mb-3 flex items-center justify-between">
                <h3 class="text-[13px] font-medium text-neutral-200">
                  文档列表
                </h3>
                <el-button
                  size="small"
                  type="primary"
                  plain
                  @click="openManualCreate"
                >
                  <FilePlus2
                    :size="12"
                    class="mr-1"
                  />
                  录入知识
                </el-button>
              </div>
              <DocumentTable
                :documents="documents"
                :loading="docsLoading"
                @refresh="loadDocuments"
                @open="(doc: DocumentItem) => (openDocId = doc.id)"
                @edit="onDocEdit"
              />
            </div>

            <div class="flex flex-col gap-4">
              <UploadPanel
                :collection-id="collectionId"
                @uploaded="onUploaded"
              />
              <div class="panel p-4">
                <h3 class="mb-2 text-[13px] font-medium text-neutral-200">
                  入库流程
                </h3>
                <ol class="flex flex-col gap-1.5 text-[12px] leading-5 text-neutral-500">
                  <li>1. 上传后进入解析队列（pending）</li>
                  <li>2. 解析 → 切片 → 向量化三个状态会实时刷新</li>
                  <li>3. 完成后可点开文档查看切片内容</li>
                  <li>4. 失败文档会显示原因，修正后可重索引</li>
                </ol>
                <p class="mt-3 text-[12px] leading-4 text-neutral-600">
                  页面刷新不会丢进度：未完成任务会按 taskId 自动恢复轮询。
                </p>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 库内检索 -->
        <el-tab-pane
          label="库内检索"
          name="retrieve"
        >
          <div class="grid gap-4 lg:grid-cols-[400px_1fr]">
            <RetrieveForm
              :collections="collection ? [collection] : []"
              :companions="store.companions"
              :searching="searching"
              @search="runRetrieve"
            />
            <div class="min-w-0">
              <div
                v-if="retrieveResult"
                class="panel p-4"
              >
                <div class="mb-3 flex flex-wrap items-center gap-2">
                  <span class="text-[13px] font-medium text-neutral-200">
                    命中 {{ retrieveResult.chunks.length }} 条
                  </span>
                  <span class="chip mono">{{ retrieveResult.elapsedMs }} ms</span>
                  <span class="chip">{{ scoreScaleMeta(retrieveResult.scoreScale).label }}</span>
                </div>
                <p class="mb-3 text-[12px] leading-4 text-neutral-600">
                  {{ scoreScaleMeta(retrieveResult.scoreScale).hint }}
                </p>
                <div
                  v-if="retrieveResult.chunks.length"
                  class="flex flex-col gap-2"
                >
                  <RetrieveResultCard
                    v-for="(chunk, i) in retrieveResult.chunks"
                    :key="`${chunk.documentId}-${chunk.chunkIndex}-${i}`"
                    :chunk="chunk"
                    :rank="i + 1"
                    :score-scale="retrieveResult.scoreScale"
                  />
                </div>
                <EmptyState
                  v-else
                  title="没有命中切片"
                  description="换一种问法，或到设置里调小切片长度让内容更细。"
                  :dashed="false"
                />
              </div>
              <EmptyState
                v-else
                title="还没有检索"
                description="左侧输入问题，只在这个库内召回，方便验证入库质量。"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 设置 -->
        <el-tab-pane
          label="设置"
          name="settings"
        >
          <div class="panel p-5">
            <div class="grid gap-x-8 gap-y-3 text-[13px] sm:grid-cols-2">
              <div>
                <p class="text-[12px] text-neutral-600">
                  知识库 ID
                </p>
                <p class="mono mt-0.5 text-neutral-300">
                  {{ collection?.id }}
                </p>
              </div>
              <div>
                <p class="text-[12px] text-neutral-600">
                  创建时间
                </p>
                <p class="mt-0.5 text-neutral-300">
                  {{ collection?.createdAt || '—' }}
                </p>
              </div>
              <div>
                <p class="text-[12px] text-neutral-600">
                  向量后端
                </p>
                <p class="mt-0.5 text-neutral-300">
                  {{ collection?.embeddingBackend }} · {{ collection?.embeddingModel }} ·
                  {{ collection?.embeddingDim }} 维
                </p>
              </div>
              <div>
                <p class="text-[12px] text-neutral-600">
                  切片参数
                </p>
                <p class="mt-0.5 text-neutral-300">
                  {{ collection?.chunkSize }} 字 / 重叠 {{ collection?.chunkOverlap }} 字
                </p>
              </div>
            </div>
            <el-button
              class="mt-4"
              type="primary"
              plain
              size="small"
              @click="editOpen = true"
            >
              <Settings2
                :size="12"
                class="mr-1"
              />
              修改名称、角色、切片与解析参数
            </el-button>
            <p class="mt-3 text-[12px] leading-4 text-neutral-600">
              改切片参数只影响之后新入库的文档；已有文档需在文档页「重索引」才会按新参数重切。
            </p>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>

    <!-- 抽屉们 -->
    <DocumentDrawer
      :document-id="openDocId"
      @close="openDocId = ''"
      @changed="reload"
      @edit="onDocEdit"
    />
    <ManualDocDrawer
      v-model="manualOpen"
      :collection-id="collectionId"
      :document="manualEditing"
      @saved="onManualSaved"
    />
    <CollectionFormDrawer
      v-model="editOpen"
      :collection="collection"
      :companions="store.companions"
      @saved="reload"
    />
  </div>
</template>