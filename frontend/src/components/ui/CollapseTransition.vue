<script setup lang="ts">
/**
 * CollapseTransition —— 高度展开 / 收起动画
 *
 * 用途：广场管理菜单、记忆新增面板、登录切换区块、筛选器。
 * 直接 v-if 会「啪」一下出现，这里用 max-height + opacity 过渡，观感连贯。
 *
 * 克制口径：
 * - 只动 opacity / transform / max-height，200ms
 * - 高度用 maxHeight 上限而不是 auto（auto 无法过渡）
 * - prefers-reduced-motion 时即时显示
 *
 * 用法：
 *   <CollapseTransition>
 *     <div v-if="open">...</div>
 *   </CollapseTransition>
 *   <CollapseTransition :max-height="420">...</CollapseTransition>
 */
interface Props {
  /** 展开后的最大高度（px），要略大于内容实际高度 */
  maxHeight?: number
  /** 动画时长（ms） */
  duration?: number
}

withDefaults(defineProps<Props>(), {
  maxHeight: 320,
  duration: 200,
})
</script>

<template>
  <Transition name="collapse" :duration="duration">
    <div class="collapse-box" :style="{ '--collapse-max-height': `${maxHeight}px` }">
      <slot />
    </div>
  </Transition>
</template>

<style scoped>
.collapse-box {
  /* Transition 作用于这个盒子本身 */
  max-height: var(--collapse-max-height, 320px);
}

.collapse-enter-active,
.collapse-leave-active {
  overflow: hidden;
  transition:
    max-height var(--dur-slow) var(--ease),
    opacity var(--dur-slow) var(--ease),
    transform var(--dur-slow) var(--ease);
}

.collapse-enter-from,
.collapse-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-4px);
}

.collapse-enter-to,
.collapse-leave-from {
  max-height: var(--collapse-max-height, 320px);
  opacity: 1;
  transform: translateY(0);
}

@media (prefers-reduced-motion: reduce) {
  .collapse-enter-active,
  .collapse-leave-active {
    transition: none;
  }
}
</style>
