<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Database,
  LayoutGrid,
  List,
  Plus,
  RefreshCw,
  Search,
  Settings2,
  Trash2,
} from 'lucide-vue-next'

import PageHeader from '@/components/layout/PageHeader.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import CollectionFormDrawer from '@/components/collection/CollectionFormDrawer.vue'
import { api, apiErrorMessage } from '@/lib/api'
import type { CollectionItem } from '@/lib/api'
import { formatNumber, formatRelative } from '@/lib/format'
import { useCollectionStore } from '@/stores/collections'

const router = useRouter()
const store = useCollectionStore()

const loading = ref(false)
const error = ref('')
const rows = ref<CollectionItem[]>([])
const total = ref(0)
const view = ref<'card' | 'list'>('card')

const query = reactive({ keyword: '', companionId: '', page: 1, pageSize: 12 })

const drawerOpen = ref(false)
const editing = ref<CollectionItem | null>(null)

/** 角色筛选下拉：只列本人+预置，按 store 缓存 */
const companionOptions = computed(() => store.companions)

async function load() {
  loading.value = true
  error.value = ''
  try {
    const res = await api.listCollections({
      keyword: query.keyword.trim() || undefined,
      companionId: query.companionId || undefined,
      page: query.page,
      pageSize: query.pageSize,
    })
    rows.value = res.items || []
    total.value = res.total || 0

    // 页码回落：删除最后一页最后一条后，避免停在空白页
    const maxPage = Math.max(1, Math.ceil(total.value / query.pageSize))
    if (query.page > maxPage) {
      query.page = maxPage
      await load()
      return
    }
  } catch (e) {
    error.value = apiErrorMessage(e, '知识库列表加载失败')
  } finally {
    loading.value = false
  }
}

function resetAndLoad() {
  query.page = 1
  void load()
}

function openCreate() {
  editing.value = null
  drawerOpen.value = true
}

function openEdit(item: CollectionItem) {
  editing.value = item
  drawerOpen.value = true
}

function onSaved() {
  store.invalidate()
  void load()
}

async function toggleStatus(item: CollectionItem) {
  const next = item.status === 'active' ? 'disabled' : 'active'
  try {
    await api.updateCollection(item.id, { status: next })
    item.status = next
    ElMessage.success(next === 'active' ? '已启用' : '已停用')
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '状态切换失败'))
  }
}

async function remove(item: CollectionItem) {
  try {
    await ElMessageBox.confirm(
      `删除「${item.name}」？该库下 ${item.documentCount} 篇文档、${item.chunkCount} 个切片与向量会一并清除。`,
      '删除知识库',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await api.deleteCollection(item.id)
    ElMessage.success('已删除')
    store.invalidate()
    await load()
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '删除失败'))
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
      title="知识库"
      :subtitle="`共 ${total} 个知识库 · 每个库按角色路由给 AI 伴侣检索`"
    >
      <template #actions>
        <el-button
          :loading="loading"
          @click="load"
        >
          <RefreshCw
            :size="13"
            class="mr-1"
          />
          刷新
        </el-button>
        <el-button
          type="primary"
          @click="openCreate"
        >
          <Plus
            :size="13"
            class="mr-1"
          />
          新建知识库
        </el-button>
      </template>
    </PageHeader>

    <el-alert
      v-if="error"
      class="mb-4"
      type="error"
      :title="error"
      :closable="false"
      show-icon
    />

    <!-- 筛选条 -->
    <div class="mb-4 flex flex-wrap items-center gap-2">
      <el-input
        v-model="query.keyword"
        class="!w-[240px]"
        placeholder="搜索名称 / 描述"
        clearable
        :prefix-icon="Search"
        @keyup.enter="resetAndLoad"
        @clear="resetAndLoad"
      />
      <el-select
        v-model="query.companionId"
        class="!w-[180px]"
        clearable
        placeholder="全部角色"
        @change="resetAndLoad"
      >
        <el-option
          v-for="c in companionOptions"
          :key="c.id"
          :value="c.id"
          :label="c.name"
        />
      </el-select>
      <el-button @click="resetAndLoad">
        筛选
      </el-button>

      <div class="ml-auto flex items-center gap-1 rounded-lg border border-ink-700/70 p-0.5">
        <button
          type="button"
          class="rounded-md p-1.5 transition-colors"
          :class="view === 'card' ? 'bg-ink-800 text-neutral-200' : 'text-neutral-600 hover:text-neutral-400'"
          title="卡片视图"
          @click="view = 'card'"
        >
          <LayoutGrid :size="14" />
        </button>
        <button
          type="button"
          class="rounded-md p-1.5 transition-colors"
          :class="view === 'list' ? 'bg-ink-800 text-neutral-200' : 'text-neutral-600 hover:text-neutral-400'"
          title="列表视图"
          @click="view = 'list'"
        >
          <List :size="14" />
        </button>
      </div>
    </div>

    <!-- 卡片视图 -->
    <div
      v-if="view === 'card'"
      v-loading="loading"
      class="min-h-[180px]"
    >
      <div
        v-if="rows.length"
        class="grid gap-3 md:grid-cols-2 xl:grid-cols-3"
      >
        <article
          v-for="item in rows"
          :key="item.id"
          class="panel group flex flex-col p-4 transition-colors hover:border-accent/35"
        >
          <div class="flex items-start gap-2">
            <RouterLink
              :to="`/collections/${item.id}`"
              class="min-w-0 flex-1"
            >
              <p
                class="truncate text-[14px] font-medium text-neutral-100"
                :title="item.name"
              >
                {{ item.name }}
              </p>
              <p class="mt-0.5 truncate text-[12px] text-neutral-600">
                {{ item.companionId ? store.companionName(item.companionId) : '未绑定角色' }}
              </p>
            </RouterLink>
            <StatusTag :status="item.status" />
          </div>

          <p class="mt-2 line-clamp-2 min-h-[34px] text-[12px] leading-[17px] text-neutral-500">
            {{ item.description || '没有描述' }}
          </p>

          <div class="mt-3 flex items-center gap-3 border-t border-ink-700/60 pt-3 text-[12px] text-neutral-500">
            <span>{{ item.documentCount }} 文档</span>
            <span class="text-neutral-700">·</span>
            <span>{{ formatNumber(item.chunkCount) }} 切片</span>
            <span class="text-neutral-700">·</span>
            <span class="mono">c{{ item.chunkSize }}/o{{ item.chunkOverlap }}</span>
            <span class="ml-auto shrink-0">{{ formatRelative(item.updatedAt) }}</span>
          </div>

          <div class="mt-2.5 flex items-center gap-1">
            <RouterLink
              :to="`/collections/${item.id}`"
              class="flex-1"
            >
              <el-button
                size="small"
                class="w-full"
              >
                <Database
                  :size="12"
                  class="mr-1"
                />
                进入
              </el-button>
            </RouterLink>
            <el-tooltip
              content="编辑设置"
              placement="top"
            >
              <el-button
                size="small"
                @click="openEdit(item)"
              >
                <Settings2 :size="12" />
              </el-button>
            </el-tooltip>
            <el-tooltip
              :content="item.status === 'active' ? '停用' : '启用'"
              placement="top"
            >
              <el-button
                size="small"
                @click="toggleStatus(item)"
              >
                {{ item.status === 'active' ? '停用' : '启用' }}
              </el-button>
            </el-tooltip>
            <el-tooltip
              content="删除"
              placement="top"
            >
              <el-button
                size="small"
                @click="remove(item)"
              >
                <Trash2 :size="12" />
              </el-button>
            </el-tooltip>
          </div>
        </article>
      </div>
      <EmptyState
        v-else-if="!loading"
        title="还没有知识库"
        description="新建一个库、绑定角色、上传文档，聊天时就能被检索到。"
      >
        <template #action>
          <el-button
            type="primary"
            size="small"
            @click="openCreate"
          >
            <Plus
              :size="12"
              class="mr-1"
            />
            新建知识库
          </el-button>
        </template>
      </EmptyState>
    </div>

    <!-- 列表视图 -->
    <div
      v-else
      class="panel overflow-hidden"
    >
      <el-table
        v-loading="loading"
        :data="rows"
        row-key="id"
        empty-text="没有匹配的知识库"
        @row-click="(row: CollectionItem) => router.push(`/collections/${row.id}`)"
      >
        <el-table-column
          label="名称"
          min-width="200"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <div class="flex flex-col">
              <span class="text-[13px] text-neutral-200">{{ row.name }}</span>
              <span class="truncate text-[12px] text-neutral-600">{{ row.description || '—' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column
          label="角色"
          width="130"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <span class="text-[12px] text-neutral-400">{{ row.companionId ? store.companionName(row.companionId) : '未绑定' }}</span>
          </template>
        </el-table-column>
        <el-table-column
          label="状态"
          width="92"
        >
          <template #default="{ row }">
            <StatusTag :status="row.status" />
          </template>
        </el-table-column>
        <el-table-column
          label="文档"
          width="72"
          align="right"
        >
          <template #default="{ row }">
            <span class="mono text-neutral-400">{{ row.documentCount }}</span>
          </template>
        </el-table-column>
        <el-table-column
          label="切片"
          width="82"
          align="right"
        >
          <template #default="{ row }">
            <span class="mono text-neutral-400">{{ formatNumber(row.chunkCount) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          label="切片参数"
          width="104"
        >
          <template #default="{ row }">
            <span class="mono text-neutral-500">{{ row.chunkSize }} / {{ row.chunkOverlap }}</span>
          </template>
        </el-table-column>
        <el-table-column
          label="更新时间"
          width="106"
        >
          <template #default="{ row }">
            <span class="text-[12px] text-neutral-500">{{ formatRelative(row.updatedAt) }}</span>
          </template>
        </el-table-column>
        <el-table-column
          label=""
          width="108"
          align="right"
        >
          <template #default="{ row }">
            <div
              class="flex items-center justify-end gap-0.5"
              @click.stop
            >
              <button
                type="button"
                class="rounded-md p-1.5 text-neutral-500 hover:bg-ink-800 hover:text-neutral-200"
                title="编辑设置"
                @click="openEdit(row)"
              >
                <Settings2 :size="13" />
              </button>
              <button
                type="button"
                class="rounded-md p-1.5 text-neutral-500 hover:bg-ink-800 hover:text-rose-300"
                title="删除"
                @click="remove(row)"
              >
                <Trash2 :size="13" />
              </button>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div
      v-if="total > query.pageSize"
      class="mt-4 flex justify-end"
    >
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.pageSize"
        :total="total"
        :page-sizes="[12, 24, 48]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="load"
        @size-change="resetAndLoad"
      />
    </div>

    <CollectionFormDrawer
      v-model="drawerOpen"
      :collection="editing"
      :companions="companionOptions"
      @saved="onSaved"
    />
  </div>
</template>