<script setup lang="ts">
/**
 * MotionStagger —— 列表 / 卡片逐项交错入场
 *
 * 用途：伴侣卡、会话卡、记忆条目、笔记卡这类「一批同时出现」的元素，
 *      按顺序错开一点时间淡入上移，读起来有节奏，但不会显得花哨。
 *
 * 克制口径：
 * - 每项只动 opacity + transform: translateY(8px)
 * - 单项 200ms，步长默认 40ms，总延迟封顶 maxDelay 防止长列表拖太久
 * - prefers-reduced-motion 时全部直出
 *
 * 用法（包裹一个列表）：
 *   <MotionStagger :count="list.length">
 *     <article v-for="item in list" :key="item.id" class="stagger-item">...</article>
 *   </MotionStagger>
 *
 * 注意：子项需要带 class="stagger-item" 才会被作用（不依赖 :deep 选择器穿透）。
 */
import { computed, onMounted, ref } from 'vue'

interface Props {
  /** 子项数量，用来算总延迟；不传则按 CSS 自然顺序 */
  count?: number
  /** 每项之间的步长（ms） */
  step?: number
  /** 首项延迟（ms） */
  delay?: number
  /** 总延迟上限（ms），超过后所有项同时出现 */
  maxDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  count: 0,
  step: 40,
  delay: 0,
  maxDelay: 320,
})

const shown = ref(false)

onMounted(() => {
  requestAnimationFrame(() => {
    shown.value = true
  })
})

/** 生成每项的延迟：--stagger-i 由子项自己取用（:nth-child 也能达到同样效果，这里用 CSS 变量更可控） */
const styleVars = computed(() => ({
  '--stagger-step': `${props.step}ms`,
  '--stagger-delay': `${props.delay}ms`,
  '--stagger-max': `${props.maxDelay}ms`,
}))
</script>

<template>
  <div class="motion-stagger" :class="{ 'is-shown': shown }" :style="styleVars">
    <slot />
  </div>
</template>

<style scoped>
.motion-stagger :deep(.stagger-item) {
  opacity: 0;
  transform: translateY(8px);
  transition:
    opacity var(--dur-slow) var(--ease),
    transform var(--dur-slow) var(--ease);
  transition-delay: 0ms;
  will-change: opacity, transform;
}

/* 逐项步长：前 8 项按 step 递增，之后统一用一个封顶值，避免长列表末尾等太久 */
.motion-stagger.is-shown :deep(.stagger-item:nth-child(1)) { transition-delay: var(--stagger-delay); }
.motion-stagger.is-shown :deep(.stagger-item:nth-child(2)) { transition-delay: calc(var(--stagger-delay) + var(--stagger-step) * 1); }
.motion-stagger.is-shown :deep(.stagger-item:nth-child(3)) { transition-delay: calc(var(--stagger-delay) + var(--stagger-step) * 2); }
.motion-stagger.is-shown :deep(.stagger-item:nth-child(4)) { transition-delay: calc(var(--stagger-delay) + var(--stagger-step) * 3); }
.motion-stagger.is-shown :deep(.stagger-item:nth-child(5)) { transition-delay: calc(var(--stagger-delay) + var(--stagger-step) * 4); }
.motion-stagger.is-shown :deep(.stagger-item:nth-child(6)) { transition-delay: calc(var(--stagger-delay) + var(--stagger-step) * 5); }
.motion-stagger.is-shown :deep(.stagger-item:nth-child(7)) { transition-delay: calc(var(--stagger-delay) + var(--stagger-step) * 6); }
.motion-stagger.is-shown :deep(.stagger-item:nth-child(n + 8)) { transition-delay: var(--stagger-max); }

.motion-stagger.is-shown :deep(.stagger-item) {
  opacity: 1;
  transform: translateY(0);
}

@media (prefers-reduced-motion: reduce) {
  .motion-stagger :deep(.stagger-item),
  .motion-stagger.is-shown :deep(.stagger-item) {
    opacity: 1;
    transform: none;
    transition: none;
    transition-delay: 0ms;
  }
}
</style>
