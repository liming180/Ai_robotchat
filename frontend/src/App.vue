<template>
  <div class="app-root">
    <router-view v-slot="{ Component }">
      <Transition name="route-fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>

    <!-- 全局轻提示容器（队列在 composables/useToast.ts） -->
    <ToastStack />
  </div>
</template>

<script setup lang="ts">
import ToastStack from '@/components/ui/ToastStack.vue'
</script>

<style>
.app-root {
  min-height: 100vh;
}
</style>
