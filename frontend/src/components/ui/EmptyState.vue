<script setup lang="ts">
/**
 * EmptyState —— 空状态
 *
 * 替代原来的 components/Empty.vue（那个只有一行 "empty" 占位）。
 * 图标做轻微上下浮动（4px / 3s），提示「这里暂时是空的」但不抢眼。
 *
 * 用法：
 *   <EmptyState title="暂时没有找到合适的伙伴" description="换一个关键词，或者看看其他分类。">
 *     <button class="btn">查看全部伴侣</button>
 *   </EmptyState>
 *   <EmptyState icon="search" title="没有搜索结果" />
 */
interface Props {
  /** 标题 */
  title?: string
  /** 说明 */
  description?: string
  /** 图标名：search / heart / message / notebook / brain / inbox */
  icon?: 'search' | 'heart' | 'message' | 'notebook' | 'brain' | 'inbox'
}

withDefaults(defineProps<Props>(), {
  title: '这里还是空的',
  description: '',
  icon: 'inbox',
})

const iconPaths: Record<string, string> = {
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm6 11-3.6-3.6',
  heart:
    'M20.8 5.6a5.4 5.4 0 0 0-7.6 0L12 6.8l-1.2-1.2a5.4 5.4 0 1 0-7.6 7.6L12 21l8.8-7.8a5.4 5.4 0 0 0 0-7.6Z',
  message:
    'M21 11.5a8.4 8.4 0 0 1-9 8.4 9 9 0 0 1-3.8-.8L3 21l1.9-5.2A8.4 8.4 0 0 1 12 3.1a8.4 8.4 0 0 1 9 8.4Z',
  notebook:
    'M6 3h11a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2Zm2 0v18M11.5 8.5h4M11.5 12.5h4',
  brain:
    'M9.5 4.5A2.9 2.9 0 0 0 6.6 7.4a3 3 0 0 0-1.5 5.3 3 3 0 0 0 1 5.2 2.9 2.9 0 0 0 3.4 2.1V4.5Zm5 0a2.9 2.9 0 0 1 2.9 2.9 3 3 0 0 1 1.5 5.3 3 3 0 0 1-1 5.2 2.9 2.9 0 0 1-3.4 2.1V4.5Z',
  inbox:
    'M3.5 13.5h4l1.5 3h6l1.5-3h4M3.5 13.5 6 4.5h12l2.5 9v4a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-4Z',
}
</script>

<template>
  <div class="empty-state">
    <span class="empty-state__icon" aria-hidden="true">
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="1.6"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path :d="iconPaths[icon]" />
      </svg>
    </span>

    <h3 class="empty-state__title">{{ title }}</h3>
    <p v-if="description" class="empty-state__desc">{{ description }}</p>

    <div v-if="$slots.default" class="empty-state__actions">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.empty-state {
  display: grid;
  min-height: 300px;
  place-items: center;
  align-content: center;
  gap: var(--sp-3);
  padding: var(--sp-12);
  border: 1px dashed rgba(255, 255, 255, 0.14);
  border-radius: var(--radius-card);
  text-align: center;
}

.empty-state__icon {
  display: grid;
  width: 56px;
  height: 56px;
  place-items: center;
  border-radius: 50%;
  color: var(--accent);
  background: var(--accent-soft);
  animation: empty-float 3s var(--ease) infinite;
}

.empty-state__icon svg {
  width: 24px;
  height: 24px;
}

@keyframes empty-float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-4px);
  }
}

.empty-state__title {
  margin: var(--sp-2) 0 0;
  color: var(--text-strong);
  font-size: var(--fs-19);
  font-weight: 700;
}

.empty-state__desc {
  margin: 0;
  max-width: 30em;
  color: var(--muted-dim);
  font-size: var(--fs-14);
  line-height: var(--lh-body);
}

.empty-state__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--sp-2);
  margin-top: var(--sp-3);
}

@media (prefers-reduced-motion: reduce) {
  .empty-state__icon {
    animation: none;
  }
}
</style>
