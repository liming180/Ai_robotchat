<script setup lang="ts">
/**
 * ToggleSwitch —— 开关
 *
 * 用途：聊天页「知识库增强（RAG）」、个人空间偏好设置。
 * 项目里原来是手写的 div + 绝对定位圆点，这里统一成一个可访问的按钮：
 * role="switch" + aria-checked，键盘 Space / Enter 可切换。
 *
 * 克制口径：圆点用 transform: translateX 过渡，180ms。
 *
 * 用法：
 *   <ToggleSwitch v-model="enableRAG" label="知识库增强" />
 *   <ToggleSwitch v-model="on" size="sm" />
 */
interface Props {
  modelValue: boolean
  /** 无障碍标签 */
  label?: string
  /** 尺寸 */
  size?: 'sm' | 'md'
  /** 是否禁用 */
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  label: '',
  size: 'md',
  disabled: false,
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'change', value: boolean): void
}>()

const toggle = () => {
  if (props.disabled) return
  const next = !props.modelValue
  emit('update:modelValue', next)
  emit('change', next)
}
</script>

<template>
  <button
    type="button"
    role="switch"
    class="toggle"
    :class="[`toggle--${size}`, { 'is-on': modelValue }]"
    :aria-checked="modelValue"
    :aria-label="label || undefined"
    :disabled="disabled"
    @click="toggle"
  >
    <span class="toggle__knob" aria-hidden="true" />
  </button>
</template>

<style scoped>
.toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  flex-shrink: 0;
  border: 0;
  border-radius: var(--radius-pill);
  background: #343832;
  cursor: pointer;
  transition: background var(--dur) var(--ease);
}

.toggle:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.toggle__knob {
  position: absolute;
  top: 50%;
  border-radius: 50%;
  background: #8d8f89;
  transform: translateY(-50%);
  transition:
    transform var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

/* md：38×22 */
.toggle--md {
  width: 38px;
  height: 22px;
}

.toggle--md .toggle__knob {
  left: 3px;
  width: 16px;
  height: 16px;
}

.toggle--md.is-on {
  background: rgba(101, 216, 197, 0.32);
}

.toggle--md.is-on .toggle__knob {
  transform: translate(16px, -50%);
  background: var(--accent);
}

/* sm：32×18 */
.toggle--sm {
  width: 32px;
  height: 18px;
}

.toggle--sm .toggle__knob {
  left: 2px;
  width: 14px;
  height: 14px;
}

.toggle--sm.is-on {
  background: rgba(101, 216, 197, 0.32);
}

.toggle--sm.is-on .toggle__knob {
  transform: translate(14px, -50%);
  background: var(--accent);
}

@media (prefers-reduced-motion: reduce) {
  .toggle,
  .toggle__knob {
    transition: none;
  }
}
</style>
