<template>
  <div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
</script>

<style>
/* 全局动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 页面过渡动画 */
.router-link-active {
  transition: all 0.3s ease;
}
</style>