<script setup lang="ts">
import { ref } from 'vue'
import { Check, Copy } from 'lucide-vue-next'

const props = withDefaults(
  defineProps<{
    text: string
    label?: string
    size?: 'sm' | 'md'
  }>(),
  { label: '复制', size: 'sm' },
)

const done = ref(false)

async function copy() {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(props.text)
    } else {
      // 非 https / 旧浏览器兜底
      const ta = document.createElement('textarea')
      ta.value = props.text
      ta.style.position = 'fixed'
      ta.style.opacity = '0'
      document.body.appendChild(ta)
      ta.select()
      document.execCommand('copy')
      document.body.removeChild(ta)
    }
    done.value = true
    window.setTimeout(() => (done.value = false), 1400)
  } catch {
    done.value = false
  }
}
</script>

<template>
  <button
    type="button"
    class="flex items-center gap-1 rounded-md border border-ink-600/80 text-neutral-500 transition-colors hover:border-ink-600 hover:bg-ink-800 hover:text-neutral-200"
    :class="size === 'sm' ? 'px-1.5 py-[2px] text-[12px]' : 'px-2 py-1 text-xs'"
    @click="copy"
  >
    <component
      :is="done ? Check : Copy"
      :size="size === 'sm' ? 11 : 13"
    />
    {{ done ? '已复制' : label }}
  </button>
</template>