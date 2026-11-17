<script setup lang="ts">
/**
 * StreamingCursor —— 流式生成中的呼吸光标
 *
 * 用途：SSE 流式输出时，接在已生成文本（或内容和为空时的占位）后面，
 *      提示「还在写」。和 TypewriterText 的区别：这个不负责吐字，只管光标。
 *
 * 克制口径：只动 opacity / transform: scale，1.1s 循环，不做发光。
 *
 * 用法：
 *   <StreamingCursor v-if="chatStore.isStreaming" />
 *   <StreamingCursor :text="'正在想'" />
 */
interface Props {
  /** 光标前的文案（没内容时显示这个 + 三个跳点） */
  text?: string
  /** 是否用三点跳动画代替单条光标 */
  dots?: boolean
}

withDefaults(defineProps<Props>(), {
  text: '',
  dots: false,
})
</script>

<template>
  <span class="streaming-cursor">
    <span v-if="text" class="streaming-cursor__text">{{ text }}</span>

    <span v-if="dots" class="streaming-cursor__dots" aria-hidden="true">
      <i></i><i></i><i></i>
    </span>
    <span v-else class="streaming-cursor__bar" aria-hidden="true" />

    <span class="sr-only">正在生成回复</span>
  </span>
</template>

<style scoped>
.streaming-cursor {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.streaming-cursor__text {
  color: var(--muted);
  font-size: var(--fs-13);
}

.streaming-cursor__bar {
  display: inline-block;
  width: 2px;
  height: 1em;
  vertical-align: -0.12em;
  border-radius: 1px;
  background: var(--accent);
  animation: cursor-breathe 1.1s var(--ease) infinite;
}

.streaming-cursor__dots {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.streaming-cursor__dots i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--muted-faint);
  animation: typing 1.2s infinite;
}

.streaming-cursor__dots i:nth-child(2) {
  animation-delay: 0.15s;
}

.streaming-cursor__dots i:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes cursor-breathe {
  0%,
  100% {
    opacity: 1;
    transform: scaleY(1);
  }
  50% {
    opacity: 0.3;
    transform: scaleY(0.82);
  }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (prefers-reduced-motion: reduce) {
  .streaming-cursor__bar,
  .streaming-cursor__dots i {
    animation: none;
  }
}
</style>
