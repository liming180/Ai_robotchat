<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { FileText, RefreshCw } from 'lucide-vue-next'

import CopyButton from '@/components/common/CopyButton.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { api, apiErrorMessage } from '@/lib/api'
import type { DocumentDetail } from '@/lib/api'
import { formatBytes, formatDateTime, sourceLabel } from '@/lib/format'

const props = defineProps<{
  /** 要打开的文档 id；置空表示关闭 */
  documentId: string
}>()

const emit = defineEmits<{
  close: []
  changed: []
  edit: [doc: DocumentDetail]
}>()

const visible = computed(() => !!props.documentId)
const loading = ref(false)
const detail = ref<DocumentDetail | null>(null)
const activeTab = ref('chunks')

async function load() {
  if (!props.documentId) return
  loading.value = true
  detail.value = null
  try {
    detail.value = await api.getDocument(props.documentId, true)
  } catch (e) {
    ElMessage.error(apiErrorMessage(e, '文档详情加载失败'))
  } finally {
    loading.value = false
  }
}

watch(
  () => props.documentId,
  (id) => {
    if (id) {
      activeTab.value = 'chunks'
      void load()
    }
  },
)

function close() {
  emit('close')
}
</script>

<template>
  <el-drawer
    :model-value="visible"
    :title="detail?.title || '文档详情'"
    size="640px"
    @update:model-value="(v: boolean) => !v && close()"
  >
    <div
      v-loading="loading"
      class="min-h-[200px]"
    >
      <template v-if="detail">
        <!-- 元信息 -->
        <div class="mb-4 grid grid-cols-2 gap-x-4 gap-y-2.5 rounded-lg border border-ink-700/70 bg-ink-900/60 p-4">
          <div>
            <p class="text-[12px] text-neutral-600">
              状态
            </p>
            <div class="mt-1">
              <StatusTag
                :status="detail.status"
                size="md"
              />
            </div>
          </div>
          <div>
            <p class="text-[12px] text-neutral-600">
              来源
            </p>
            <p class="mt-1 text-[12px] text-neutral-300">
              {{ sourceLabel(detail.sourceType) }}
            </p>
          </div>
          <div>
            <p class="text-[12px] text-neutral-600">
              切片数
            </p>
            <p class="mono mt-1 text-[12px] text-neutral-300">
              {{ detail.chunkCount }}
            </p>
          </div>
          <div>
            <p class="text-[12px] text-neutral-600">
              大小
            </p>
            <p class="mono mt-1 text-[12px] text-neutral-300">
              {{ formatBytes(detail.fileSize) }}
            </p>
          </div>
          <div>
            <p class="text-[12px] text-neutral-600">
              创建时间
            </p>
            <p class="mt-1 text-[12px] text-neutral-400">
              {{ formatDateTime(detail.createdAt) }}
            </p>
          </div>
          <div>
            <p class="text-[12px] text-neutral-600">
              文档 ID
            </p>
            <div class="mt-1 flex items-center gap-1.5">
              <p
                class="mono truncate text-[12px] text-neutral-400"
                :title="detail.id"
              >
                {{ detail.id.slice(0, 12) }}…
              </p>
              <CopyButton
                :text="detail.id"
                label=""
              />
            </div>
          </div>
          <div
            v-if="detail.errorMsg"
            class="col-span-2"
          >
            <p class="text-[12px] text-neutral-600">
              失败原因
            </p>
            <p class="mt-1 rounded-md border border-rose-500/25 bg-rose-500/5 px-2.5 py-1.5 text-[12px] text-rose-300">
              {{ detail.errorMsg }}
            </p>
          </div>
        </div>

        <div class="mb-3 flex items-center gap-2">
          <el-button
            size="small"
            :loading="loading"
            @click="load"
          >
            <RefreshCw
              :size="12"
              class="mr-1"
            />
            刷新
          </el-button>
          <el-button
            v-if="detail.sourceType === 'manual'"
            size="small"
            type="primary"
            plain
            @click="emit('edit', detail)"
          >
            编辑正文
          </el-button>
        </div>

        <el-tabs v-model="activeTab">
          <el-tab-pane
            :label="`切片 (${detail.chunks?.length ?? 0})`"
            name="chunks"
          >
            <div
              v-if="detail.chunks?.length"
              class="flex flex-col gap-2"
            >
              <div
                v-for="chunk in detail.chunks"
                :key="chunk.id"
                class="rounded-lg border border-ink-700/70 bg-ink-900/60 p-3"
              >
                <div class="mb-1.5 flex items-center gap-2">
                  <span class="mono rounded bg-ink-800 px-1.5 py-0.5 text-[12px] text-neutral-400">
                    #{{ chunk.chunkIndex }}
                  </span>
                  <span class="mono text-neutral-600">{{ chunk.charCount }} 字</span>
                  <CopyButton
                    class="ml-auto"
                    :text="chunk.content"
                  />
                </div>
                <p class="max-h-[180px] overflow-y-auto whitespace-pre-wrap text-[12px] leading-5 text-neutral-300">
                  {{ chunk.content }}
                </p>
              </div>
            </div>
            <p
              v-else
              class="py-8 text-center text-[12px] text-neutral-600"
            >
              {{ ['completed', 'failed', 'error'].includes(detail.status) ? '没有切片数据' : '正在解析，切片生成后可见' }}
            </p>
          </el-tab-pane>

          <el-tab-pane
            label="原始正文"
            name="raw"
          >
            <div
              v-if="detail.rawContent"
              class="max-h-[440px] overflow-y-auto whitespace-pre-wrap rounded-lg border border-ink-700/70 bg-ink-900/60 p-4 text-[12px] leading-5 text-neutral-300"
            >
              {{ detail.rawContent }}
            </div>
            <p
              v-else
              class="flex flex-col items-center gap-2 py-8 text-center text-[12px] text-neutral-600"
            >
              <FileText :size="16" />
              {{ detail.filePath ? '二进制文件，正文不入库' : '没有原始正文' }}
            </p>
          </el-tab-pane>
        </el-tabs>
      </template>
    </div>
  </el-drawer>
</template>