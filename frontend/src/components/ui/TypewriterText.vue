<script setup lang="ts">
/**
 * TypewriterText —— 打字机逐字输出
 *
 * 用途：聊天页 AI 消息首次出现时逐字吐字，模拟「正在说」。
 * 只用于**最后一条** AI 消息，历史消息直出，避免整屏都在打。
 *
 * 克制口径：
 * - 默认 18ms/字，文字长时自动加速（总时长封顶 maxDuration）
 * - 只追加文本，不做逐字变形动画
 * - 输出完成后发 emit('done')，外部据此把状态切回普通渲染
 * - prefers-reduced-motion 时直接一次性输出
 * - 组件卸载时清定时器
 *
 * 用法：
 *   <TypewriterText :text="msg.content" :enabled="isLastAiMessage" @done="onTypedDone" />
 */
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface Props {
  /** 要输出的完整文本 */
  text: string
  /** 是否启用打字效果；false 时直接显示全文 */
  enabled?: boolean
  /** 每个字的间隔（ms） */
  speed?: number
  /** 总时长上限（ms），文字多时自动加速 */
  maxDuration?: number
  /** 完成后是否保留光标闪一下 */
  keepCaret?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  enabled: true,
  speed: 18,
  maxDuration: 2400,
  keepCaret: false,
})

const emit = defineEmits<{
  (e: 'done'): void
  (e: 'update:typing', typing: boolean): void
}>()

const shown = ref('')
const typing = ref(false)
let timer: ReturnType<typeof setTimeout> | null = null
/** 记录本轮输出是否已被取消（props 变化时） */
let cancelled = false

const clear = () => {
  if (timer) {
    clearTimeout(timer)
    timer = null
  }
}

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

const start = () => {
  clear()
  cancelled = false

  const full = props.text ?? ''

  if (!props.enabled || prefersReducedMotion()) {
    shown.value = full
    typing.value = false
    emit('update:typing', false)
    emit('done')
    return
  }

  shown.value = ''
  typing.value = true
  emit('update:typing', true)

  // 文字多就提速，保证总时长不超过 maxDuration
  const perChar = Math.max(
    4,
    Math.min(props.speed, props.maxDuration / Math.max(full.length, 1)),
  )

  let index = 0

  const step = () => {
    if (cancelled) return

    // 中文按字、英文按词更自然：遇到空格时多吐一个字符
    index += 1
    shown.value = full.slice(0, index)

    if (index >= full.length) {
      typing.value = false
      emit('update:typing', false)
      emit('done')
      timer = null
      return
    }

    timer = setTimeout(step, perChar)
  }

  timer = setTimeout(step, perChar)
}

onMounted(start)

watch(
  () => [props.text, props.enabled],
  () => {
    cancelled = true
    start()
  },
)

onBeforeUnmount(() => {
  cancelled = true
  clear()
})
</script>

<template>
  <span class="typewriter">
    <span class="typewriter__text">{{ shown }}</span>
    <span
      v-if="typing || (keepCaret && shown.length > 0)"
      class="typewriter__caret"
      aria-hidden="true"
    />
  </span>
</template>

<style scoped>
.typewriter {
  white-space: pre-wrap;
  word-break: break-word;
}

.typewriter__caret {
  display: inline-block;
  width: 2px;
  height: 1em;
  margin-left: 1px;
  vertical-align: -0.12em;
  border-radius: 1px;
  background: var(--accent);
  animation: caret-blink 1s step-end infinite;
}

@media (prefers-reduced-motion: reduce) {
  .typewriter__caret {
    animation: none;
    opacity: 0;
  }
}
</style>
