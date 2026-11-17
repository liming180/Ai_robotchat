<script setup lang="ts">
/**
 * ModalDialog —— 对话框
 *
 * 用途：删除伴侣二次确认、写笔记、编辑记忆。
 *
 * 克制口径：
 * - 遮罩 opacity 淡入 200ms，卡片 opacity + scale(0.98→1) 200ms
 * - Esc 关闭、点遮罩关闭（可通过 closeOnBackdrop 关掉）
 * - 打开时锁定 body 滚动、焦点移入卡片；关闭后焦点回到触发元素
 * - 只用 transform / opacity，不做模糊背景动画
 *
 * 用法：
 *   <ModalDialog v-model="open" title="删除伴侣「小暖」？" @close="reset">
 *     <p>此操作不可恢复。</p>
 *     <template #footer>
 *       <button @click="open = false">取消</button>
 *       <button @click="confirm">确认删除</button>
 *     </template>
 *   </ModalDialog>
 */
import { nextTick, onBeforeUnmount, ref, watch } from 'vue'

interface Props {
  modelValue: boolean
  /** 标题 */
  title?: string
  /** 说明文字（可选，标题下方小字） */
  description?: string
  /** 宽度（px） */
  width?: number
  /** 点遮罩是否关闭 */
  closeOnBackdrop?: boolean
  /** Esc 是否关闭 */
  closeOnEsc?: boolean
  /** 是否显示右上角关闭按钮 */
  showClose?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  width: 520,
  closeOnBackdrop: true,
  closeOnEsc: true,
  showClose: true,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'close'): void
}>()

const card = ref<HTMLElement | null>(null)
/** 打开前的焦点元素，关闭后还回去 */
let lastActive: HTMLElement | null = null

const close = () => {
  emit('update:modelValue', false)
  emit('close')
}

const onBackdrop = () => {
  if (props.closeOnBackdrop) close()
}

const onKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.closeOnEsc) {
    event.stopPropagation()
    close()
    return
  }

  // 焦点圈在对话框内：Tab 到末尾时回到第一个可聚焦元素
  if (event.key !== 'Tab' || !card.value) return

  const focusables = card.value.querySelectorAll<HTMLElement>(
    'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])',
  )
  if (focusables.length === 0) return

  const first = focusables[0]
  const last = focusables[focusables.length - 1]

  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}

const lockScroll = (lock: boolean) => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = lock ? 'hidden' : ''
}

watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      lastActive = document.activeElement as HTMLElement | null
      lockScroll(true)
      await nextTick()
      card.value?.focus()
    } else {
      lockScroll(false)
      lastActive?.focus?.()
      lastActive = null
    }
  },
)

onBeforeUnmount(() => {
  lockScroll(false)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="modal-layer"
        @click.self="onBackdrop"
        @keydown="onKeydown"
      >
        <div
          ref="card"
          class="modal-card"
          role="dialog"
          aria-modal="true"
          :aria-label="title || undefined"
          :style="{ maxWidth: `${width}px` }"
          tabindex="-1"
        >
          <header v-if="title || showClose" class="modal-head">
            <div class="modal-head__copy">
              <h2 v-if="title" class="modal-title">{{ title }}</h2>
              <p v-if="description" class="modal-desc">{{ description }}</p>
            </div>
            <button
              v-if="showClose"
              type="button"
              class="modal-close"
              aria-label="关闭"
              @click="close"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </header>

          <div class="modal-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="modal-foot">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-layer {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: grid;
  place-items: center;
  padding: var(--sp-6);
  background: rgba(9, 11, 9, 0.66);
  backdrop-filter: blur(3px);
}

.modal-card {
  width: 100%;
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
  box-shadow: var(--shadow-lift);
}

.modal-card:focus {
  outline: none;
}

.modal-head {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-4);
  padding: var(--sp-5) var(--sp-5) var(--sp-4);
  border-bottom: 1px solid var(--line);
}

.modal-head__copy {
  min-width: 0;
  flex: 1;
}

.modal-title {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-19);
  font-weight: 700;
  line-height: 1.35;
}

.modal-desc {
  margin: 6px 0 0;
  color: var(--muted-dim);
  font-size: var(--fs-13);
  line-height: 1.7;
}

.modal-close {
  display: grid;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  place-items: center;
  border: 0;
  border-radius: 50%;
  color: var(--muted);
  background: transparent;
  cursor: pointer;
  transition: color var(--dur) var(--ease), background var(--dur) var(--ease);
}

.modal-close:hover {
  color: var(--text-strong);
  background: rgba(255, 255, 255, 0.06);
}

.modal-close svg {
  width: 17px;
  height: 17px;
}

.modal-body {
  padding: var(--sp-5);
}

.modal-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--sp-2);
  padding: var(--sp-4) var(--sp-5);
  border-top: 1px solid var(--line);
  background: var(--bg);
}

/* ---- 过渡 ---- */

.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--dur-slow) var(--ease);
}

.modal-enter-active .modal-card,
.modal-leave-active .modal-card {
  transition:
    opacity var(--dur-slow) var(--ease),
    transform var(--dur-slow) var(--ease);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-card,
.modal-leave-to .modal-card {
  opacity: 0;
  transform: scale(0.98) translateY(6px);
}

@media (prefers-reduced-motion: reduce) {
  .modal-enter-active,
  .modal-leave-active,
  .modal-enter-active .modal-card,
  .modal-leave-active .modal-card {
    transition: none;
  }
}
</style>
