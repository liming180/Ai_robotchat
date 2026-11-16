import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { getAccessToken } from '@/lib/api'
import ChatPage from '@/pages/ChatPage.vue'
import SquarePage from '@/pages/SquarePage.vue'
import CreatePage from '@/pages/CreatePage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import HistoryPage from '@/pages/HistoryPage.vue'
import MemoryManagement from '@/pages/MemoryManagement.vue'
import EmotionCalendar from '@/pages/EmotionCalendar.vue'
import NotesPage from '@/pages/NotesPage.vue'

const routes: RouteRecordRaw[] = [
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
    // 编辑能力已合并到 CreatePage（字段更全，含 tags 与 AI 头像生成）。
    // 用路由级 redirect 而非页面内 push：push 会在历史栈里再压一条，
    // 用户按回退键会回到 /settings 又立刻被 push 回去，形成回退死循环。
    // redirect 是「替换式」跳转，回退键直接跳过来源页，不会被弹回。
    // 此路由仅作为老书签 / 旧历史记录的兜底，业务入口一律直接写 /create?edit=。
    path: '/settings/:id',
    name: 'settings',
    redirect: to => ({ path: '/create', query: { edit: String(to.params.id) } }),
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
