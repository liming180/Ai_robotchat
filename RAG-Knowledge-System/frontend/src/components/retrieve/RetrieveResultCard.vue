<script setup lang="ts">
import { computed } from 'vue'
import { FileText } from 'lucide-vue-next'

import CopyButton from '@/components/common/CopyButton.vue'
import type { RetrievedChunk } from '@/lib/api'

const props = defineProps<{
  chunk: RetrievedChunk
  rank: number
  scoreScale: string
}>()

/** cosine/tei：0–1 相似度；rrf：名次融合分，只做相对展示 */
const isRrf = computed(() => props.scoreScale === 'rrf')

const scoreText = computed(() => (isRrf.value ? props.chunk.score.toFixed(4) : props.chunk.score.toFixed(3)))

/** cosine 用条形展示相对长度，rrf 分数量级太小没有可视化意义 */
const barWidth = computed(() => {
  if (isRrf.value) return 0
  return Math.max(4, Math.min(100, props.chunk.score * 100))
})
</script>

<template>
  <div class="rounded-lg border border-ink-700/70 bg-ink-900/60 p-4">
    <div class="mb-2.5 flex items-center gap-2">
      <span
        class="grid size-6 shrink-0 place-items-center rounded-md text-[12px] font-semibold"
        :class="
          rank <= 3
            ? 'bg-accent/15 text-accent ring-1 ring-accent/30'
            : 'bg-ink-800 text-neutral-500 ring-1 ring-ink-600'
        "
      >
        {{ rank }}
      </span>
      <span
        class="min-w-0 flex-1 truncate text-[12px] text-neutral-300"
        :title="chunk.documentTitle || ''"
      >
        <FileText
          :size="11"
          class="mr-1 inline text-neutral-500"
        />
        {{ chunk.documentTitle || '未知文档' }}
        <span
          v-if="chunk.collectionName"
          class="ml-1.5 text-neutral-600"
        >· {{ chunk.collectionName }}</span>
        <span
          v-if="chunk.chunkIndex != null"
          class="ml-1.5 text-neutral-600"
        >· #{{ chunk.chunkIndex }}</span>
      </span>

      <div class="flex shrink-0 items-center gap-2">
        <div
          v-if="barWidth"
          class="h-1 w-[72px] overflow-hidden rounded-full bg-ink-800"
        >
          <div
            class="h-full rounded-full bg-accent/60"
            :style="{ width: `${barWidth}%` }"
          />
        </div>
        <span
          class="mono text-neutral-400"
          :title="scoreScale"
        >{{ scoreText }}</span>
        <CopyButton :text="chunk.content" />
      </div>
    </div>

    <p class="max-h-[200px] overflow-y-auto whitespace-pre-wrap text-[12px] leading-5 text-neutral-400">
      {{ chunk.content }}
    </p>
  </div>
</template>