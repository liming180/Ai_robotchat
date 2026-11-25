import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/pages/LoginPage.vue'),
      meta: { public: true },
    },
    {
      path: '/',
      redirect: '/overview',
    },
    {
      path: '/overview',
      name: 'overview',
      component: () => import('@/pages/OverviewPage.vue'),
      meta: { crumb: '概览' },
    },
    {
      path: '/collections',
      name: 'collections',
      component: () => import('@/pages/CollectionsPage.vue'),
      meta: { crumb: '知识库' },
    },
    {
      path: '/collections/:id',
      name: 'collection-detail',
      component: () => import('@/pages/CollectionDetailPage.vue'),
      meta: { crumb: '知识库', crumbTo: '/collections' },
    },
    {
      path: '/retrieve',
      name: 'retrieve',
      component: () => import('@/pages/RetrievePage.vue'),
      meta: { crumb: '检索调试' },
    },
    { path: '/:pathMatch(.*)*', redirect: '/overview' },
  ],
})

// 登录守卫：未登录访问受限页 → 跳登录；已登录访问登录页 → 跳概览
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && auth.isLoggedIn) return '/overview'
  return true
})

export default router