<script setup lang="ts">
/**
 * SkeletonBlock —— 骨架屏（微光扫动）
 *
 * 用途：广场/记录/记忆加载中，替代「正在加载…」这行字。
 * 形状要和真实内容接近，加载完不留跳动。
 *
 * 克制口径：
 * - 微光用伪元素的 translateX 扫过（2s 循环），不是整体闪烁
 * - prefers-reduced-motion 时静态显示，不扫
 *
 * 用法：
 *   <SkeletonBlock :rows="3" />
 *   <SkeletonBlock variant="card" :count="4" />
 *   <SkeletonBlock variant="text" :rows="2" width="60%" />
 */
interface Props {
  /** 形状：文本行 / 卡片 / 头像行 */
  variant?: 'text' | 'card' | 'row'
  /** 行数或卡片数 */
  rows?: number
  /** 卡片/行数（variant=card 或 row 时生效） */
  count?: number
  /** 单行宽度，可传 '60%' 这类 */
  width?: string
  /** 行高（px） */
  height?: number
}

withDefaults(defineProps<Props>(), {
  variant: 'text',
  rows: 3,
  count: 1,
  width: '100%',
  height: 14,
})
</script>

<template>
  <div
    class="skeleton"
    :class="`skeleton--${variant}`"
    role="status"
    aria-live="polite"
    aria-label="正在加载"
  >
    <!-- 文本行 -->
    <template v-if="variant === 'text'">
      <span
        v-for="i in rows"
        :key="i"
        class="skeleton__bar"
        :style="{
          width: i === rows && rows > 1 ? '62%' : width,
          height: `${height}px`,
        }"
      />
    </template>

    <!-- 卡片 -->
    <template v-else-if="variant === 'card'">
      <div v-for="i in count" :key="i" class="skeleton__card">
        <span class="skeleton__bar skeleton__bar--circle" style="width: 92px; height: 92px" />
        <span class="skeleton__bar" style="width: 44%; height: 18px" />
        <span class="skeleton__bar" style="width: 78%; height: 13px" />
        <span class="skeleton__bar" style="width: 62%; height: 13px" />
      </div>
    </template>

    <!-- 头像 + 两行 -->
    <template v-else>
      <div v-for="i in count" :key="i" class="skeleton__row">
        <span class="skeleton__bar skeleton__bar--circle" style="width: 40px; height: 40px" />
        <div class="skeleton__row-copy">
          <span class="skeleton__bar" style="width: 38%; height: 14px" />
          <span class="skeleton__bar" style="width: 76%; height: 12px" />
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.skeleton {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  width: 100%;
}

.skeleton__bar {
  position: relative;
  display: block;
  overflow: hidden;
  border-radius: var(--radius-sm);
  background: rgba(255, 255, 255, 0.06);
}

.skeleton__bar--circle {
  border-radius: 50%;
}

/* 微光扫过 */
.skeleton__bar::after {
  content: '';
  position: absolute;
  inset: 0;
  transform: translateX(-100%);
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.07),
    transparent
  );
  animation: skeleton-sweep 2s var(--ease) infinite;
}

@keyframes skeleton-sweep {
  100% {
    transform: translateX(100%);
  }
}

/* ---- 卡片 ---- */
.skeleton--card {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: var(--sp-4);
}

.skeleton__card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: var(--sp-4);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

/* ---- 行 ---- */
.skeleton--row {
  gap: var(--sp-4);
}

.skeleton__row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

.skeleton__row-copy {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 8px;
}

@media (prefers-reduced-motion: reduce) {
  .skeleton__bar::after {
    animation: none;
  }
}
</style>
