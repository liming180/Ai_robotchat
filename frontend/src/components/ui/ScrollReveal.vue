<script setup lang="ts">
/**
 * ScrollReveal —— 进入视口后渐显（只播一次）
 *
 * 用途：首页各区块、长页面的段落。滚到时轻轻浮现，不打断阅读。
 *
 * 克制口径：
 * - 只动 opacity + transform: translateY(12px)
 * - IntersectionObserver threshold 0.15，进入 15% 就播
 * - 只播一次（播放后 unobserve），来回滚动不会反复闪
 * - 没有 IntersectionObserver 或 reduced-motion 时直接显示
 *
 * 用法：
 *   <ScrollReveal>
 *     <section>...</section>
 *   </ScrollReveal>
 *   <ScrollReveal :delay="120">...</ScrollReveal>
 */
import { onBeforeUnmount, onMounted, ref } from 'vue'

interface Props {
  /** 延迟（ms），用于同一屏内多个区块错开 */
  delay?: number
  /** 位移距离（px） */
  distance?: number
  /** 触发阈值（0–1） */
  threshold?: number
  /** 关闭动画 */
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  delay: 0,
  distance: 12,
  threshold: 0.15,
  disabled: false,
})

const root = ref<HTMLElement | null>(null)
const shown = ref(false)
let observer: IntersectionObserver | null = null

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

onMounted(() => {
  if (props.disabled || prefersReducedMotion() || !('IntersectionObserver' in window)) {
    shown.value = true
    return
  }

  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          window.setTimeout(() => {
            shown.value = true
          }, props.delay)
          observer?.unobserve(entry.target)
        }
      }
    },
    { threshold: props.threshold, rootMargin: '0px 0px -40px 0px' },
  )

  if (root.value) observer.observe(root.value)
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})
</script>

<template>
  <div
    ref="root"
    class="scroll-reveal"
    :class="{ 'is-shown': shown }"
    :style="{ '--reveal-distance': `${distance}px` }"
  >
    <slot />
  </div>
</template>

<style scoped>
.scroll-reveal {
  opacity: 0;
  transform: translateY(var(--reveal-distance, 12px));
  transition:
    opacity var(--dur-page) var(--ease),
    transform var(--dur-page) var(--ease);
  will-change: opacity, transform;
}

.scroll-reveal.is-shown {
  opacity: 1;
  transform: translateY(0);
  will-change: auto;
}

@media (prefers-reduced-motion: reduce) {
  .scroll-reveal {
    opacity: 1;
    transform: none;
    transition: none;
  }
}
</style>
