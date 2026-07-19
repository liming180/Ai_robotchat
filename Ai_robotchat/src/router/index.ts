import { createRouter, createWebHistory } from 'vue-router'
import ChatPage from '@/pages/ChatPage.vue'
import SquarePage from '@/pages/SquarePage.vue'
import CreatePage from '@/pages/CreatePage.vue'
import ProfilePage from '@/pages/ProfilePage.vue'
import HomePage from '@/pages/HomePage.vue'
import LoginPage from '@/pages/LoginPage.vue'
import HistoryPage from '@/pages/HistoryPage.vue'
import SettingsPage from '@/pages/SettingsPage.vue'

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
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
