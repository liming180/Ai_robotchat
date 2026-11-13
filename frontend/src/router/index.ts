import { createRouter, createWebHistory } from 'vue-router'
import { getAccessToken } from '@/lib/api'
import ChatPage from '@/pages/ChatPage.vue'
import SquarePage from '@/pages/SquarePage.vue'
import CreatePage from '@/pages/CreatePage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import HistoryPage from '@/pages/HistoryPage.vue'
import SettingsPage from '@/pages/SettingsPage.vue'
import MemoryManagement from '@/pages/MemoryManagement.vue'
import EmotionCalendar from '@/pages/EmotionCalendar.vue'
import NotesPage from '@/pages/NotesPage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage,
  },
  {
    path: '/square',
    name: 'square',
    component: SquarePage,
  },
  {
    path: '/login',
    name: 'login',
    component: LoginPage,
  },
  {
    path: '/create',
    name: 'create',
    component: CreatePage,
  },
  {
    path: '/chat/:id',
    name: 'chat',
    component: ChatPage,
  },
  {
    path: '/profile',
    name: 'profile',
    component: ProfilePage,
  },
  {
    path: '/history',
    name: 'history',
    component: HistoryPage,
  },
  {
    path: '/settings/:id',
    name: 'settings',
    component: SettingsPage,
  },
  {
    path: '/memory',
    name: 'memory',
    component: MemoryManagement,
  },
  {
    path: '/calendar',
    name: 'calendar',
    component: EmotionCalendar,
  },
  {
    path: '/notes',
    name: 'notes',
    component: NotesPage,
  },
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
})

/**
 * 全局登录守卫：除 /login 外全部要求登录。
 * 只读 localStorage 里的 token（经 api.ts 的响应式副本），不 import user store，
 * 避免 router → stores → api → router 的循环依赖。
 */
router.beforeEach((to) => {
  const loggedIn = getAccessToken() !== null

  if (to.path !== '/login' && !loggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.path === '/login' && loggedIn) {
    return { path: '/' }
  }
  return true
})

export default router
