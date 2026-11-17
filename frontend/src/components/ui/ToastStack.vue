<script setup lang="ts">
/**
 * ToastStack —— 轻提示渲染层
 *
 * 队列在 composables/useToast.ts（模块级单例），这里只负责画。
 * 放在 App.vue 里一次即可：
 *   <ToastStack />
 */
import { dismissToast, toastItems, type ToastKind } from '@/composables/useToast'

const iconPath: Record<ToastKind, string> = {
  success: 'm4.5 12.5 5 5 10-11',
  error: 'M18 6 6 18M6 6l12 12',
  info: 'M12 8h.01M11 12h1v5',
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-stack" role="status" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="item in toastItems"
          :key="item.id"
          class="toast"
          :class="`toast--${item.kind}`"
        >
          <span class="toast__icon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path :d="iconPath[item.kind]" />
            </svg>
          </span>
          <span class="toast__message">{{ item.message }}</span>
          <button
            type="button"
            class="toast__close"
            aria-label="关闭提示"
            @click="dismissToast(item.id)"
          >
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="1.75"
              stroke-linecap="round"
            >
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-stack {
  position: fixed;
  right: var(--sp-6);
  bottom: var(--sp-6);
  z-index: 300;
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 240px;
  max-width: 360px;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-raise);
  box-shadow: var(--shadow-lift);
  pointer-events: auto;
}

.toast__icon {
  display: grid;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 50%;
  color: var(--on-primary);
  background: var(--primary);
}

.toast--success .toast__icon {
  color: #0e1a14;
  background: var(--accent);
}

.toast--info .toast__icon {
  color: #17120f;
  background: var(--bone);
}

.toast__icon svg {
  width: 11px;
  height: 11px;
}

.toast__message {
  flex: 1;
  min-width: 0;
  color: var(--text);
  font-size: var(--fs-13);
  line-height: 1.6;
  word-break: break-word;
}

.toast__close {
  display: grid;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  place-items: center;
  margin: -2px -4px 0 0;
  border: 0;
  border-radius: 50%;
  color: var(--muted-faint);
  background: transparent;
  cursor: pointer;
}

.toast__close:hover {
  color: var(--text);
}

.toast__close svg {
  width: 13px;
  height: 13px;
}

/* ---- 过渡 ---- */

.toast-enter-active,
.toast-leave-active {
  transition:
    opacity var(--dur-slow) var(--ease),
    transform var(--dur-slow) var(--ease);
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(16px);
}

.toast-move {
  transition: transform var(--dur-slow) var(--ease);
}

@media (max-width: 760px) {
  .toast-stack {
    left: var(--sp-4);
    right: var(--sp-4);
    bottom: var(--sp-4);
  }

  .toast {
    max-width: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .toast-enter-active,
  .toast-leave-active,
  .toast-move {
    transition: none;
  }
}
</style>
