<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    /** 标题右侧的补充说明徽标 */
    badge?: string
  }>(),
  { subtitle: '', badge: '' },
)
</script>

<template>
  <div class="mb-6 flex flex-wrap items-start justify-between gap-4">
    <div class="min-w-0">
      <div class="flex items-center gap-2.5">
        <h1 class="truncate text-[19px] font-semibold tracking-tight text-neutral-50">
          {{ title }}
        </h1>
        <span
          v-if="badge"
          class="chip shrink-0"
        >{{ badge }}</span>
      </div>
      <p
        v-if="subtitle"
        class="mt-1 text-[13px] leading-5 text-neutral-500"
      >
        {{ subtitle }}
      </p>
    </div>
    <div class="flex shrink-0 items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>