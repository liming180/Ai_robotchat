<script setup lang="ts">
/**
 * UserAvatar / CompanionAvatar 的统一实现 —— AvatarImage
 *
 * 背景：项目里每个页面都手写「有 avatar 就 img、失败就 SVG 首字」这段逻辑，
 * 结果换风格时漏掉一处就出现「有的地方真头像、有的地方只有字」。
 * 这里收成一个组件，全站统一用它。
 *
 * 行为：
 * - 有 src 且加载成功 → 渲染图片
 * - src 为空，或图片 onerror → 用 createSvgAvatarDataUrl 生成首字渐变色块兜底
 * - 尺寸/形状由 size + round 控制，颜色兜底按 seed 稳定生成（同一人永远同一色）
 *
 * 用法：
 *   <AvatarImage :src="companion.avatar" :name="companion.name" :seed="companion.id" size="md" />
 *   <AvatarImage :src="user.avatar" :name="user.name" seed="self" size="lg" />
 */
import { computed, ref, watch } from 'vue'
import { createSvgAvatarDataUrl } from '@/lib/avatar'

interface Props {
  /** 图片地址；空字符串/null 直接走兜底 */
  src?: string | null
  /** 用于生成兜底首字的名字 */
  name?: string
  /** 兜底色的种子，传 id 保证同一对象颜色稳定；不传用 name */
  seed?: string
  /** 尺寸档位 */
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  /** 是否圆形（默认 true；方形头像传 false） */
  round?: boolean
  /** 无障碍标签；不传则用 name */
  alt?: string
}

const props = withDefaults(defineProps<Props>(), {
  src: '',
  name: '',
  seed: '',
  size: 'md',
  round: true,
  alt: '',
})

/** 当前 img 是否加载失败 */
const failed = ref(false)

// src 变化时重置失败态：换了新头像要重新尝试加载，不能一直停在兜底
watch(
  () => props.src,
  () => {
    failed.value = false
  },
)

const effectiveSrc = computed(() => (props.src || '').trim())

const showImage = computed(() => Boolean(effectiveSrc.value) && !failed.value)

/** 兜底：名字最后一个字 + 由 seed 稳定派生的渐变色 */
const fallbackSrc = computed(() => {
  const label = (props.name || 'AI').trim().slice(-1) || 'AI'
  return createSvgAvatarDataUrl({
    seed: props.seed || props.name || label,
    label,
  })
})

const onError = () => {
  failed.value = true
}

const ariaLabel = computed(() => props.alt || props.name || '头像')
</script>

<template>
  <span
    class="avatar-img"
    :class="[`avatar-img--${size}`, { 'avatar-img--round': round }]"
  >
    <img
      v-if="showImage"
      :src="effectiveSrc"
      :alt="ariaLabel"
      loading="lazy"
      @error="onError"
    />
    <img v-else :src="fallbackSrc" :alt="ariaLabel" />
  </span>
</template>

<style scoped>
.avatar-img {
  display: inline-grid;
  flex-shrink: 0;
  place-items: center;
  overflow: hidden;
  border: 1px solid var(--line);
  background: var(--bg-raise);
}

.avatar-img img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.avatar-img--round {
  border-radius: 50%;
}

.avatar-img:not(.avatar-img--round) {
  border-radius: var(--radius-sm);
}

/* 尺寸档位，与 tokens 里的头像尺寸保持一致 */
.avatar-img--xs {
  width: 26px;
  height: 26px;
}

.avatar-img--sm {
  width: 34px;
  height: 34px;
}

.avatar-img--md {
  width: 46px;
  height: 46px;
}

.avatar-img--lg {
  width: 64px;
  height: 64px;
}

.avatar-img--xl {
  width: 92px;
  height: 92px;
}
</style>
