<script setup lang="ts">
/**
 * AnimatedNumber —— 数字滚动计数
 *
 * 用途：首页数字条（4 位伴侣 / 3 秒 / 24 条 / 100%）、个人空间统计。
 * 数字从 0 滚到目标值，让「有多少」这件事被看见。
 *
 * 克制口径：
 * - 用 requestAnimationFrame + easeOutCubic，默认 900ms
 * - 只改文本内容，不触发重排动画（数字宽度用 font-variant-numeric: tabular-nums 锁住）
 * - prefers-reduced-motion 或 disabled 时直接显示终值
 * - 组件卸载时取消 rAF，避免泄漏
 *
 * 用法：
 *   <AnimatedNumber :value="24" />
 *   <AnimatedNumber :value="82" suffix="%" />
 *   <AnimatedNumber :value="3" suffix=" 秒" :decimals="0" />
 */
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

interface Props {
  /** 目标值 */
  value: number
  /** 前缀（如 ¥） */
  prefix?: string
  /** 后缀（如 % / 条 / 秒） */
  suffix?: string
  /** 小数位，默认 0 */
  decimals?: number
  /** 动画时长（ms），默认 900 */
  duration?: number
  /** 起始值，默认 0 */
  from?: number
  /** 关闭动画，直接显示终值 */
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  prefix: '',
  suffix: '',
  decimals: 0,
  duration: 900,
  from: 0,
  disabled: false,
})

const current = ref(props.disabled ? props.value : props.from)
let rafId = 0

const prefersReducedMotion = () =>
  typeof window !== 'undefined' &&
  window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

/** easeOutCubic：开头快、结尾缓，读起来不拖沓 */
const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3)

const stop = () => {
  if (rafId) {
    cancelAnimationFrame(rafId)
    rafId = 0
  }
}

const run = () => {
  stop()

  if (props.disabled || prefersReducedMotion()) {
    current.value = props.value
    return
  }

  const start = props.from
  const end = props.value
  const startAt = performance.now()

  const tick = (now: number) => {
    const elapsed = now - startAt
    const progress = Math.min(elapsed / props.duration, 1)
    current.value = start + (end - start) * easeOutCubic(progress)

    if (progress < 1) {
      rafId = requestAnimationFrame(tick)
    } else {
      current.value = end
      rafId = 0
    }
  }

  rafId = requestAnimationFrame(tick)
}

onMounted(run)

watch(
  () => props.value,
  () => run(),
)

onBeforeUnmount(stop)

const display = computed(() => {
  const fixed = current.value.toFixed(props.decimals)
  // 千分位：只对整数位加，避免影响小数
  const [intPart, decPart] = fixed.split('.')
  const withComma = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  return decPart ? `${withComma}.${decPart}` : withComma
})
</script>

<template>
  <span class="animated-number">
    <span v-if="prefix" class="animated-number__affix">{{ prefix }}</span>
    <span class="animated-number__value">{{ display }}</span>
    <span v-if="suffix" class="animated-number__affix">{{ suffix }}</span>
  </span>
</template>

<style scoped>
.animated-number {
  display: inline-flex;
  align-items: baseline;
  gap: 2px;
  font-variant-numeric: tabular-nums;
  /* 锁住数字宽度，滚动时后面文字不跟着抖 */
  font-feature-settings: 'tnum';
}

.animated-number__value {
  /* 宽度按 4 位数预留，避免从 0 滚到 100 时布局跳动 */
  min-width: 1ch;
}

.animated-number__affix {
  font-size: 0.55em;
  font-weight: 500;
  color: var(--accent);
}
</style>
