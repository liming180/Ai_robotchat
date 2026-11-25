<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'

const route = useRoute()
const isPublic = computed(() => !!route.meta.public)
</script>

<template>
  <RouterView v-if="isPublic" />
  <div
    v-else
    class="flex h-full overflow-hidden bg-ink-950"
  >
    <AppSidebar />
    <div class="flex min-w-0 flex-1 flex-col">
      <AppHeader />
      <main class="flex-1 overflow-y-auto">
        <div class="mx-auto w-full max-w-[1200px] px-8 py-6">
          <RouterView v-slot="{ Component }">
            <component :is="Component" />
          </RouterView>
        </div>
      </main>
    </div>
  </div>
</template>