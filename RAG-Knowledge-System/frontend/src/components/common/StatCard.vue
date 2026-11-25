<script setup lang="ts">
withDefaults(
  defineProps<{
    label: string
    value: string | number
    hint?: string
    /** 强调色：默认中性，accent 用于主指标 */
    tone?: 'default' | 'accent'
  }>(),
  { hint: '', tone: 'default' },
)
</script>

<template>
  <div class="panel px-4 py-3.5">
    <p class="text-[12px] text-neutral-500">
      {{ label }}
    </p>
    <p
      class="mt-1.5 text-[22px] font-semibold leading-none tracking-tight"
      :class="tone === 'accent' ? 'text-accent' : 'text-neutral-100'"
    >
      {{ value }}
    </p>
    <p
      v-if="hint"
      class="mt-2 text-[12px] leading-4 text-neutral-600"
    >
      {{ hint }}
    </p>
  </div>
</template>