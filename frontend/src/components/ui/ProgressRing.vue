<script setup lang="ts">
/**
 * ProgressRing —— 默契值环形进度
 *
 * 用途：聊天页伴侣头像、广场收藏卡、个人空间收藏列表。
 * 比一条横细线更抓眼，也更贴合「默契」这个情感指标。
 *
 * 克制口径：
 * - 只用 SVG stroke-dashoffset 过渡（GPU 友好），600ms easeOut
 * - 从 0 开始动画到目标值，进入视口/挂载时触发
 * - prefers-reduced-motion 时直接显示终值
 *
 * 用法：
 *   <ProgressRing :value="82" :size="56" />
 *   <ProgressRing :value="82" :size="36" :stroke="2" show-label />
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface Props {
  /** 0–100 */
  value: number
  /** 环的直径（px） */
  size?: number
  /** 环宽（px） */
  stroke?: number
  /** 是否在中心显示百分比文字 */
  showLabel?: boolean
  /** 环颜色，默认青绿 */
  color?: string
  /** 轨道颜色 */
  trackColor?: string
  /** 动画时长（ms） */
  duration?: number
}

const props = withDefaults(defineProps<Props>(), {
  size: 56,
  stroke: 3,
  showLabel: false,
  color: 'var(--accent)',
  trackColor: 'rgba(255,255,255,0.12)',
  duration: 600,
})

/** 动画中的当前值 */
const animated = ref(0)
let rafId = 0

const radius = computed(() => (props.size - props.stroke) / 2)
const circumference = computed(() => 2 * Math.PI * radius.value)
const clamped = computed(() => Math.min(100, Math.max(0, props.value)))

const dashOffset = computed(() => {
  const ratio = animated.value / 100
  return circumference.value * (1 - ratio)
})

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

const animate = () => {
  if (rafId) cancelAnimationFrame(rafId)

  if (prefersReducedMotion()) {
    animated.value = clamped.value
    return
  }

  const end = clamped.value
  const startAt = performance.now()

  const tick = (now: number) => {
    const progress = Math.min((now - startAt) / props.duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    animated.value = end * eased

    if (progress < 1) {
      rafId = requestAnimationFrame(tick)
    } else {
      animated.value = end
      rafId = 0
    }
  }

  rafId = requestAnimationFrame(tick)
}

onMounted(animate)

watch(() => props.value, animate)

onBeforeUnmount(() => {
  if (rafId) cancelAnimationFrame(rafId)
})
</script>

<template>
  <span
    class="progress-ring"
    :style="{ width: `${size}px`, height: `${size}px` }"
    role="img"
    :aria-label="`默契 ${Math.round(clamped)}%`"
  >
    <svg :width="size" :height="size" :viewBox="`0 0 ${size} ${size}`">
      <circle
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="trackColor"
        :stroke-width="stroke"
      />
      <circle
        class="progress-ring__bar"
        :cx="size / 2"
        :cy="size / 2"
        :r="radius"
        fill="none"
        :stroke="color"
        :stroke-width="stroke"
        stroke-linecap="round"
        :stroke-dasharray="circumference"
        :stroke-dashoffset="dashOffset"
        :transform="`rotate(-90 ${size / 2} ${size / 2})`"
      />
    </svg>
    <span v-if="showLabel" class="progress-ring__label">
      {{ Math.round(animated) }}<i>%</i>
    </span>
  </span>
</template>

<style scoped>
.progress-ring {
  position: relative;
  display: inline-grid;
  place-items: center;
  flex-shrink: 0;
}

.progress-ring svg {
  display: block;
}

.progress-ring__label {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--text-strong);
  font-size: var(--fs-11);
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.progress-ring__label i {
  font-style: normal;
  font-size: 0.72em;
  color: var(--muted);
  margin-left: 1px;
}
</style>
