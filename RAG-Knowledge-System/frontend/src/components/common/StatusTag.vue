<script setup lang="ts">
import { computed } from 'vue'

import { statusMeta } from '@/lib/format'

const props = withDefaults(
  defineProps<{
    status?: string | null
    /** 尺寸：sm 用于表格行内，md 用于头部 */
    size?: 'sm' | 'md'
  }>(),
  { status: '', size: 'sm' },
)

const meta = computed(() => statusMeta(props.status))
</script>

<template>
  <span
    class="inline-flex items-center gap-1.5 rounded-md border font-medium"
    :class="[
      meta.className,
      size === 'sm' ? 'px-1.5 py-[1px] text-[12px]' : 'px-2 py-0.5 text-xs',
    ]"
  >
    <span
      v-if="meta.pulse"
      class="size-1.5 animate-pulse rounded-full bg-current"
      aria-hidden="true"
    />
    {{ meta.label }}
  </span>
</template>