<script setup lang="ts">
/**
 * MotionPage —— 页面入场容器
 *
 * 用途：每个路由页面最外层包一层，切换进来时做一次「上移 + 淡入」。
 * 克制口径：只动 transform 与 opacity，240ms，cubic-bezier(.2,.8,.2,1)。
 * 尊重 prefers-reduced-motion：系统关掉动效时直接直出，不做任何位移动画。
 *
 * 用法：
 *   <MotionPage>
 *     <div class="page-content">...</div>
 *   </MotionPage>
 */
import { onMounted, ref } from 'vue'

interface Props {
  /** 入场位移距离（px），默认 8 */
  distance?: number
  /** 是否禁用（例如需要自己控制入场时） */
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  distance: 8,
  disabled: false,
})

const shown = ref(false)

onMounted(() => {
  if (props.disabled) {
    shown.value = true
    return
  }
  // 下一帧再打开，保证过渡会真正发生（同一帧内加类不触发 transition）
  requestAnimationFrame(() => {
    shown.value = true
  })
})
</script>

<template>
  <div
    class="motion-page"
    :class="{ 'is-shown': shown || disabled }"
    :style="{
      '--motion-page-distance': disabled ? '0px' : `${distance}px`,
    }"
  >
    <slot />
  </div>
</template>

<style scoped>
/*
  用 CSS animation 而不是 transition：
  transition 需要 JS 改类名才触发，若首帧没执行（截图、SSR 水合前、脚本异常）
  页面会停在 opacity:0 显示为空白。animation 一加载就跑，且 fill-mode: both
  保证终态稳定在「完全可见」。
*/
.motion-page {
  animation: motion-page-in var(--dur-page) var(--ease) both;
}

@keyframes motion-page-in {
  from {
    opacity: 0;
    transform: translateY(var(--motion-page-distance, 8px));
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .motion-page {
    animation: none;
  }
}
</style>
