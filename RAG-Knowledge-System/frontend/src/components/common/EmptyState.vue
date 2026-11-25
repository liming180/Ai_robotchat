<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    description?: string
    /** 是否渲染成虚线框（用于大块空白区域的占位） */
    dashed?: boolean
  }>(),
  { description: '', dashed: true },
)
</script>

<template>
  <div
    class="flex flex-col items-center justify-center gap-1.5 px-6 py-12 text-center"
    :class="dashed ? 'rounded-xl border border-dashed border-ink-600/70' : ''"
  >
    <slot name="icon">
      <div class="mb-1 grid size-9 place-items-center rounded-lg bg-ink-800 text-neutral-600">
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
        >
          <path d="M4 7a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
        </svg>
      </div>
    </slot>
    <p class="text-[13px] font-medium text-neutral-300">
      {{ title }}
    </p>
    <p
      v-if="description"
      class="max-w-[380px] text-[12px] leading-5 text-neutral-600"
    >
      {{ description }}
    </p>
    <div
      v-if="$slots.action"
      class="mt-3"
    >
      <slot name="action" />
    </div>
  </div>
</template>