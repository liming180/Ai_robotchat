<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { CloudUpload, FileText, TriangleAlert, X } from 'lucide-vue-next'

import { api, apiErrorMessage } from '@/lib/api'
import type { UploadResultItem } from '@/lib/api'
import { formatBytes } from '@/lib/format'
import { ACCEPT_ATTR, MAX_FILE_SIZE_MB, guardFiles } from '@/lib/uploadGuard'
import type { RejectedFile } from '@/lib/uploadGuard'

const props = defineProps<{ collectionId: string }>()

const emit = defineEmits<{ uploaded: [items: UploadResultItem[]] }>()

const inputRef = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const submitting = ref(false)
const percent = ref(0)
const accepted = ref<File[]>([])
const rejected = ref<RejectedFile[]>([])

const totalSize = computed(() => accepted.value.reduce((n, f) => n + f.size, 0))

function addFiles(files: FileList | File[]) {
  const result = guardFiles([...files])
  // 同名同大小视为重复，避免重复提交同一文件
  for (const f of result.accepted) {
    if (accepted.value.some((e) => e.name === f.name && e.size === f.size)) continue
    accepted.value.push(f)
  }
  if (result.rejected.length) rejected.value.push(...result.rejected)
}

function onPick(event: Event) {
  const target = event.target as HTMLInputElement
  if (target.files?.length) addFiles(target.files)
  target.value = ''
}

function onDrop(event: DragEvent) {
  dragging.value = false
  const files = event.dataTransfer?.files
  if (files?.length) addFiles(files)
}

function remove(index: number) {
  accepted.value.splice(index, 1)
}

function reset() {
  accepted.value = []
  rejected.value = []
  percent.value = 0
}

async function submit() {
  if (!accepted.value.length) return
  submitting.value = true
  percent.value = 0
  try {
    const items = await api.uploadDocuments(props.collectionId, accepted.value, (p) => {
      percent.value = p
    })
    ElMessage.success(`已提交 ${items.length} 个文件，正在后台解析`)
    emit('uploaded', items)
    reset()
  } catch (e) {
    // 该接口在半成功时只返回 400：前面已落盘的文件已入库，故提示用户刷新核对
    ElMessage.error(apiErrorMessage(e, '上传失败'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="panel p-5">
    <div class="mb-3 flex items-center justify-between">
      <h3 class="text-[13px] font-medium text-neutral-200">
        上传文档
      </h3>
      <span class="text-[12px] text-neutral-600">
        支持 .json / .md / .txt，单文件 ≤ {{ MAX_FILE_SIZE_MB }}MB
      </span>
    </div>

    <div
      class="flex cursor-pointer flex-col items-center justify-center gap-1.5 rounded-xl border border-dashed px-6 py-9 transition-colors"
      :class="
        dragging
          ? 'border-accent/60 bg-accent/5'
          : 'border-ink-600/70 hover:border-ink-600 hover:bg-ink-850/60'
      "
      @click="inputRef?.click()"
      @dragover.prevent="dragging = true"
      @dragleave.prevent="dragging = false"
      @drop.prevent="onDrop"
    >
      <span class="grid size-10 place-items-center rounded-xl bg-ink-800 text-neutral-500">
        <CloudUpload :size="18" />
      </span>
      <p class="text-[13px] text-neutral-300">
        拖拽文件到这里，或
        <span class="text-accent">点击选择</span>
      </p>
      <p class="text-[12px] text-neutral-600">
        格式与大小在提交前校验，避免后端半成功造成脏数据
      </p>
      <input
        ref="inputRef"
        type="file"
        multiple
        hidden
        :accept="ACCEPT_ATTR"
        @change="onPick"
      >
    </div>

    <!-- 待上传 -->
    <div
      v-if="accepted.length"
      class="mt-4"
    >
      <div class="mb-2 flex items-center justify-between">
        <span class="text-[12px] text-neutral-400">
          待上传 {{ accepted.length }} 个 · {{ formatBytes(totalSize) }}
        </span>
        <button
          type="button"
          class="text-[12px] text-neutral-500 hover:text-neutral-300"
          @click="reset"
        >
          清空
        </button>
      </div>
      <ul class="flex flex-col gap-1.5">
        <li
          v-for="(f, i) in accepted"
          :key="`${f.name}-${f.size}`"
          class="flex items-center gap-2 rounded-lg border border-ink-700/70 bg-ink-900 px-3 py-2"
        >
          <FileText
            :size="13"
            class="shrink-0 text-neutral-500"
          />
          <span class="min-w-0 flex-1 truncate text-[12px] text-neutral-300">{{ f.name }}</span>
          <span class="mono shrink-0 text-neutral-600">{{ formatBytes(f.size) }}</span>
          <button
            type="button"
            class="shrink-0 rounded p-0.5 text-neutral-600 hover:bg-ink-800 hover:text-neutral-300"
            @click="remove(i)"
          >
            <X :size="12" />
          </button>
        </li>
      </ul>

      <div
        v-if="submitting"
        class="mt-3"
      >
        <el-progress
          :percentage="percent"
          :stroke-width="4"
          :show-text="false"
        />
        <p class="mt-1.5 text-[12px] text-neutral-600">
          正在传输…上传完成后由后端排队解析
        </p>
      </div>

      <el-button
        class="mt-3 w-full"
        type="primary"
        :loading="submitting"
        @click="submit"
      >
        上传 {{ accepted.length }} 个文件
      </el-button>
    </div>

    <!-- 被拒绝的文件 -->
    <div
      v-if="rejected.length"
      class="mt-4 rounded-lg border border-amber-500/25 bg-amber-500/5 p-3"
    >
      <div class="mb-1.5 flex items-center gap-1.5 text-[12px] text-amber-300">
        <TriangleAlert :size="13" />
        {{ rejected.length }} 个文件被拦下，未提交
      </div>
      <ul class="flex flex-col gap-1">
        <li
          v-for="r in rejected"
          :key="`${r.name}-${r.reason}`"
          class="text-[12px] leading-4 text-neutral-400"
        >
          <span class="text-neutral-300">{{ r.name }}</span>
          <span class="text-neutral-600"> — {{ r.reason }}</span>
        </li>
      </ul>
      <button
        type="button"
        class="mt-2 text-[12px] text-neutral-500 hover:text-neutral-300"
        @click="rejected = []"
      >
        知道了
      </button>
    </div>
  </div>
</template>