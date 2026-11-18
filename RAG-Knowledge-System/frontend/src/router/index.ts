import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: { public: true },
    },
    { path: '/', redirect: '/collections' },
    { path: '/collections', component: () => import('@/pages/CollectionsPage.vue') },
    { path: '/collections/:id', component: () => import('@/pages/CollectionDetailPage.vue') },
    { path: '/retrieve', component: () => import('@/pages/RetrievePage.vue') },
  ],
})

// 登录守卫：未登录访问受限页 → 跳登录；已登录访问登录页 → 跳知识库
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) return '/login'
  if (to.path === '/login' && auth.isLoggedIn) return '/collections'
  return true
})

export default router
