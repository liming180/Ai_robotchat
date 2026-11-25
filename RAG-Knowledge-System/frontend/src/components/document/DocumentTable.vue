<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MoreHorizontal, RefreshCw, Trash2 } from 'lucide-vue-next'

import StatusTag from '@/components/common/StatusTag.vue'
import { api, apiErrorMessage } from '@/lib/api'
import type { DocumentItem } from '@/lib/api'
import { formatBytes, formatRelative, isFailed, sourceLabel } from '@/lib/format'
import { useTaskStore } from '@/stores/tasks'

const props = defineProps<{
  documents: DocumentItem[]
  loading?: boolean
}>()

const emit = defineEmits<{
  refresh: []
  open: [doc: DocumentItem]
  edit: [doc: DocumentItem]
  settled: []
}>()

const taskStore = useTaskStore()

const keyword = ref('')
const statusFilter = ref('')
const selected = ref<DocumentItem[]>([])

const STATUS_OPTIONS = [
  { value: '', label: '全部状态' },
  { value: 'pending', label: '排队中' },
  { value: 'parsing', label: '解析中' },
  { value: 'chunking', label: '切片中' },
  { value: 'embedding', label: '向量化中' },
  { value: 'completed', label: '已完成' },
  { value: 'failed', label: '失败' },
]

const filtered = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  return props.documents.filter((d) => {
    if (statusFilter.value === 'failed' ? !isFailed(d.status) : statusFilter.value && d.status !== statusFilter.value)
      return false
    if (kw && !`${d.title} ${d.fileName || ''}`.toLowerCase().includes(kw)) return false
    return true
  })
})

/** 行内进度：优先取轮询表的实时值 */
function progressOf(doc: DocumentItem): number {
  const rec = taskStore.recordOf(doc.taskId)
  return rec && !isFailed(rec.status) ? Math.max(doc.progress, rec.progress || 0) : doc.progress
}

function statusOf(doc: DocumentItem): string {
  const rec = taskStore.recordOf(doc.taskId)
  return rec && !rec.pollError ? rec.status : doc.status
}

function errorMsgOf(doc: DocumentItem): string {
  const rec = taskStore.recordOf(doc.taskId)
  return rec?.errorMsg || doc.errorMsg || ''
}

const busy = computed(() =>
  props.documents.some((d) => !['completed', 'failed', 'error'].includes(d.status)),
)

async function reindexOne(doc: DocumentItem) {
  try {
    const { taskId } = await api.reindexDocument(doc.id)
    taskStore.watch([taskId])
    ElMessage.success(`「${doc.title}」已重新提交解析`)
    emit('refresh')
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '重索引失败'))
  }
}

async function deleteOne(doc: DocumentItem) {
  try {
    await ElMessageBox.confirm(
      `删除「${doc.title}」？切片与向量会一并清除，此操作不可恢复。`,
      '删除文档',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await api.deleteDocument(doc.id)
    ElMessage.success('已删除')
    emit('refresh')
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '删除失败'))
  }
}

async function reindexSelected() {
  const docs = selected.value.filter((d) => d.status !== 'parsing')
  if (!docs.length) return
  try {
    await Promise.all(docs.map((d) => api.reindexDocument(d.id)))
    taskStore.watch(docs.map((d) => d.taskId).filter(Boolean))
    ElMessage.success(`已提交 ${docs.length} 个文档重索引`)
    selected.value = []
    emit('refresh')
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '批量重索引失败'))
  }
}

async function deleteSelected() {
  const docs = [...selected.value]
  if (!docs.length) return
  try {
    await ElMessageBox.confirm(
      `删除选中的 ${docs.length} 个文档？切片与向量会一并清除，此操作不可恢复。`,
      '批量删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  let ok = 0
  let fail = 0
  for (const d of docs) {
    try {
      await api.deleteDocument(d.id)
      ok += 1
    } catch {
      fail += 1
    }
  }
  selected.value = []
  if (fail) ElMessage.warning(`删除完成：${ok} 成功，${fail} 失败`)
  else ElMessage.success(`已删除 ${ok} 个文档`)
  emit('refresh')
}
</script>

<template>
  <div>
    <!-- 工具条 -->
    <div class="mb-3 flex flex-wrap items-center gap-2">
      <el-select
        v-model="statusFilter"
        class="!w-[130px]"
        size="default"
      >
        <el-option
          v-for="opt in STATUS_OPTIONS"
          :key="opt.value"
          :value="opt.value"
          :label="opt.label"
        />
      </el-select>
      <el-input
        v-model="keyword"
        class="!w-[220px]"
        placeholder="搜索标题 / 文件名"
        clearable
      />
      <span class="text-[12px] text-neutral-600">{{ filtered.length }} / {{ documents.length }} 篇</span>

      <div class="ml-auto flex items-center gap-2">
        <el-button
          v-if="selected.length"
          size="small"
          :disabled="busy"
          @click="reindexSelected"
        >
          <RefreshCw
            :size="12"
            class="mr-1"
          />
          重索引 {{ selected.length }}
        </el-button>
        <el-button
          v-if="selected.length"
          size="small"
          type="danger"
          plain
          class="!ml-0"
          @click="deleteSelected"
        >
          <Trash2
            :size="12"
            class="mr-1"
          />
          删除
        </el-button>
        <el-button
          size="small"
          :loading="loading"
          @click="emit('refresh')"
        >
          <RefreshCw
            :size="12"
            class="mr-1"
          />
          刷新
        </el-button>
      </div>
    </div>

    <!-- 表格 -->
    <el-table
      v-loading="loading"
      :data="filtered"
      row-key="id"
      class="doc-table"
      empty-text="没有匹配的文档"
      @selection-change="(rows: DocumentItem[]) => (selected = rows)"
      @row-click="(row: DocumentItem) => emit('open', row)"
    >
      <el-table-column
        type="selection"
        width="34"
      />

      <el-table-column
        label="标题"
        min-width="180"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <div class="flex min-w-0 flex-col">
            <span class="truncate text-[13px] text-neutral-200">{{ row.title }}</span>
            <span
              v-if="row.fileName"
              class="truncate text-[12px] text-neutral-600"
            >
              {{ row.fileName }} · {{ formatBytes(row.fileSize) }}
            </span>
            <!-- 失败原因并入标题格：单开一列在 1280 下必然被切，而且这条信息很少出现 -->
            <span
              v-if="errorMsgOf(row)"
              class="truncate text-[12px] text-rose-300/90"
              :title="errorMsgOf(row)"
            >
              {{ errorMsgOf(row) }}
            </span>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        label="来源"
        width="80"
      >
        <template #default="{ row }">
          <span class="text-[12px] text-neutral-400">{{ sourceLabel(row.sourceType) }}</span>
        </template>
      </el-table-column>

      <el-table-column
        label="状态"
        width="118"
      >
        <template #default="{ row }">
          <StatusTag :status="statusOf(row)" />
          <el-progress
            v-if="['parsing', 'chunking', 'embedding'].includes(statusOf(row))"
            :percentage="progressOf(row)"
            :stroke-width="3"
            :show-text="false"
            class="mt-1.5 !w-[76px]"
          />
        </template>
      </el-table-column>

      <el-table-column
        label="切片"
        width="58"
        align="right"
      >
        <template #default="{ row }">
          <span class="mono text-neutral-400">{{ row.chunkCount }}</span>
        </template>
      </el-table-column>

      <el-table-column
        label="更新时间"
        width="90"
      >
        <template #default="{ row }">
          <span class="text-[12px] text-neutral-500">{{ formatRelative(row.updatedAt) }}</span>
        </template>
      </el-table-column>

      <el-table-column
        label=""
        width="78"
        align="right"
        fixed="right"
      >
        <template #default="{ row }">
          <div
            class="flex items-center justify-end gap-0.5"
            @click.stop
          >
            <el-tooltip
              content="重索引"
              placement="top"
            >
              <button
                type="button"
                class="rounded-md p-1.5 text-neutral-500 transition-colors hover:bg-ink-800 hover:text-neutral-200"
                :disabled="!['completed', 'failed', 'error'].includes(row.status)"
                @click="reindexOne(row)"
              >
                <RefreshCw :size="13" />
              </button>
            </el-tooltip>
            <el-tooltip
              v-if="row.sourceType === 'manual'"
              content="编辑正文"
              placement="top"
            >
              <button
                type="button"
                class="rounded-md p-1.5 text-neutral-500 transition-colors hover:bg-ink-800 hover:text-neutral-200"
                @click="emit('edit', row)"
              >
                <MoreHorizontal :size="13" />
              </button>
            </el-tooltip>
            <el-tooltip
              content="删除"
              placement="top"
            >
              <button
                type="button"
                class="rounded-md p-1.5 text-neutral-500 transition-colors hover:bg-ink-800 hover:text-rose-300"
                @click="deleteOne(row)"
              >
                <Trash2 :size="13" />
              </button>
            </el-tooltip>
          </div>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>