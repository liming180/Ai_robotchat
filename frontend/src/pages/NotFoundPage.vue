<template>
  <div class="not-found">
    <div class="not-found__inner">
      <p class="not-found__code" aria-hidden="true">404</p>
      <h1 class="not-found__title">页面不存在</h1>
      <p class="not-found__desc">你访问的页面可能已被移除，或者地址输入有误。</p>

      <div class="not-found__actions">
        <button type="button" class="btn btn-primary" @click="router.push('/')">
          <ArrowLeft :size="16" />
          返回首页
        </button>
        <button type="button" class="btn btn-ghost" @click="router.push('/square')">
          去伴侣广场
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowLeft } from 'lucide-vue-next'

const router = useRouter()
</script>

<style scoped>
.not-found {
  display: grid;
  min-height: 100vh;
  place-items: center;
  padding: var(--sp-6);
  text-align: center;
}

.not-found__inner {
  max-width: 30em;
}

.not-found__code {
  margin: 0;
  color: var(--primary);
  font-size: clamp(72px, 14vw, 132px);
  font-weight: 760;
  line-height: 1;
  letter-spacing: -0.04em;
  font-variant-numeric: tabular-nums;
}

.not-found__title {
  margin: var(--sp-4) 0 0;
  color: var(--text-strong);
  font-size: var(--fs-25);
  font-weight: 720;
}

.not-found__desc {
  margin: var(--sp-3) 0 0;
  color: var(--muted);
  font-size: var(--fs-14);
  line-height: var(--lh-body);
}

.not-found__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--sp-3);
  margin-top: var(--sp-7);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 20px;
  border: 0;
  border-radius: var(--radius);
  font-size: var(--fs-14);
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.btn-primary {
  color: var(--on-primary);
  background: var(--primary);
  box-shadow: var(--shadow-primary);
}

.btn-primary:hover {
  background: var(--primary-hover);
}

.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: var(--text);
  background: transparent;
}

.btn-ghost:hover {
  border-color: var(--line-strong);
  background: rgba(255, 255, 255, 0.04);
}
</style>
