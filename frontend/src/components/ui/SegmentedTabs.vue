<script setup lang="ts">
/**
 * SegmentedTabs —— 分段切换器（指示条滑动）
 *
 * 用途：广场分类（全部/日常聊天/…）、登录-注册-验证码、笔记类型筛选。
 * 相比一堆 chip，指示条滑动让「当前在哪一段」更清楚。
 *
 * 克制口径：
 * - 指示条用 transform: translateX + width，200ms
 * - 按钮本身只有颜色过渡，不做缩放
 * - 键盘可用：左右方向键切换，符合 tablist 语义
 *
 * 用法：
 *   <SegmentedTabs v-model="category" :options="categories" />
 *   <SegmentedTabs v-model="tab" :options="[{label:'登录',value:'login'}, ...]" variant="underline" />
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

export interface SegmentedOption {
  label: string
  value: string
  /** 可选的计数徽标 */
  count?: number
}

interface Props {
  modelValue: string
  options: SegmentedOption[]
  /** pill：米白胶囊（广场分类）；underline：下划线（登录 tab） */
  variant?: 'pill' | 'underline'
  /** 无障碍标签 */
  ariaLabel?: string
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'pill',
  ariaLabel: '切换分类',
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const wrap = ref<HTMLElement | null>(null)
const buttons = ref<HTMLButtonElement[]>([])

/** 指示条位置与宽度 */
const indicator = ref({ left: 0, width: 0 })

const activeIndex = computed(() =>
  props.options.findIndex((o) => o.value === props.modelValue),
)

const measure = () => {
  const index = activeIndex.value
  if (index < 0) return
  const el = buttons.value[index]
  if (!el) return
  indicator.value = {
    left: el.offsetLeft,
    width: el.offsetWidth,
  }
}

const select = (value: string) => {
  if (value === props.modelValue) return
  emit('update:modelValue', value)
}

/** 键盘：左右方向键在选项间移动 */
const onKeydown = (event: KeyboardEvent) => {
  const { key } = event
  if (key !== 'ArrowLeft' && key !== 'ArrowRight') return

  event.preventDefault()
  const step = key === 'ArrowRight' ? 1 : -1
  const next = (activeIndex.value + step + props.options.length) % props.options.length
  const target = props.options[next]
  if (!target) return

  select(target.value)
  nextTick(() => {
    buttons.value[next]?.focus()
  })
}

let resizeObserver: ResizeObserver | null = null

onMounted(() => {
  nextTick(measure)
  if ('ResizeObserver' in window && wrap.value) {
    resizeObserver = new ResizeObserver(() => measure())
    resizeObserver.observe(wrap.value)
  }
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  resizeObserver = null
})

watch(
  () => [props.modelValue, props.options.length],
  () => nextTick(measure),
)
</script>

<template>
  <div
    ref="wrap"
    class="segmented"
    :class="`segmented--${variant}`"
    role="tablist"
    :aria-label="ariaLabel"
    @keydown="onKeydown"
  >
    <span
      class="segmented__indicator"
      :style="{
        transform: `translateX(${indicator.left}px)`,
        width: `${indicator.width}px`,
      }"
      aria-hidden="true"
    />

    <button
      v-for="option in options"
      :key="option.value"
      ref="buttons"
      type="button"
      role="tab"
      class="segmented__btn"
      :class="{ 'is-active': option.value === modelValue }"
      :aria-selected="option.value === modelValue"
      :tabindex="option.value === modelValue ? 0 : -1"
      @click="select(option.value)"
    >
      {{ option.label }}
      <span v-if="typeof option.count === 'number'" class="segmented__count">
        {{ option.count }}
      </span>
    </button>
  </div>
</template>

<style scoped>
.segmented {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  flex-wrap: wrap;
}

.segmented__indicator {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  border-radius: var(--radius-sm);
  transition:
    transform var(--dur-slow) var(--ease),
    width var(--dur-slow) var(--ease);
  pointer-events: none;
}

.segmented__btn {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 36px;
  padding: 0 14px;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: transparent;
  font-size: var(--fs-13);
  white-space: nowrap;
  transition: color var(--dur) var(--ease);
}

.segmented__btn:hover {
  color: var(--text-strong);
}

.segmented__btn.is-active {
  color: #171917;
  font-weight: 720;
}

.segmented__count {
  color: inherit;
  opacity: 0.6;
  font-size: var(--fs-11);
}

/* ---- pill：米白胶囊 ---- */
.segmented--pill {
  padding: 4px;
  border-radius: var(--radius);
  background: var(--bg-soft);
}

.segmented--pill .segmented__indicator {
  background: var(--bone);
}

/* ---- underline：下划线 ---- */
.segmented--underline {
  gap: var(--sp-6);
  border-bottom: 1px solid var(--line);
}

.segmented--underline .segmented__indicator {
  top: auto;
  bottom: -1px;
  height: 2px;
  border-radius: 2px;
  background: var(--primary);
}

.segmented--underline .segmented__btn {
  min-height: 40px;
  padding: 0 0 10px;
}

.segmented--underline .segmented__btn.is-active {
  color: var(--text-strong);
  font-weight: 650;
}

@media (prefers-reduced-motion: reduce) {
  .segmented__indicator {
    transition: none;
  }
}
</style>
