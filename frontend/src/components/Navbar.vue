<template>
  <nav class="topbar">
    <div class="container topbar-inner">
      <button type="button" class="brand" @click="router.push('/')">
        <span class="brand-mark">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path
              d="M20.8 5.6a5.4 5.4 0 0 0-7.6 0L12 6.8l-1.2-1.2a5.4 5.4 0 1 0-7.6 7.6L12 21l8.8-7.8a5.4 5.4 0 0 0 0-7.6Z"
            />
          </svg>
        </span>
        AI 伴侣
      </button>

      <div class="nav">
        <router-link :class="{ 'is-active': isRoute('home') }" to="/">首页</router-link>
        <router-link :class="{ 'is-active': isRoute('square') }" to="/square">伴侣广场</router-link>
        <router-link :class="{ 'is-active': isRoute('history') }" to="/history">聊天记录</router-link>
        <router-link :class="{ 'is-active': isRoute('memory') }" to="/memory">记忆</router-link>
        <router-link :class="{ 'is-active': isRoute('calendar') }" to="/calendar">情绪</router-link>
        <router-link :class="{ 'is-active': isRoute('notes') }" to="/notes">随笔</router-link>
      </div>

      <div class="topbar-right">
        <template v-if="userStore.isAuthenticated">
          <button
            type="button"
            class="icon-btn"
            title="聊天记录"
            aria-label="聊天记录"
            @click="router.push('/history')"
          >
            <MessagesSquare :size="19" />
          </button>

          <div class="user-wrap">
            <button
              type="button"
              class="user-button"
              :aria-expanded="menuOpen"
              aria-haspopup="menu"
              @click.stop="toggleMenu"
            >
              <AvatarImage
                :src="userStore.user?.avatar"
                :name="userStore.user?.name"
                :seed="userStore.user?.id || 'self'"
                size="sm"
              />
              <span class="user-name">{{ userStore.user?.name || '我' }}</span>
              <ChevronDown :size="14" class="user-caret" />
            </button>

            <CollapseTransition :max-height="220">
              <div v-if="menuOpen" class="user-menu" role="menu" @click.stop>
                <div class="user-menu__head">
                  <p class="user-menu__name">{{ userStore.user?.name || '我' }}</p>
                  <p class="user-menu__mail">{{ userStore.user?.email }}</p>
                </div>
                <button type="button" class="user-menu__item" role="menuitem" @click="go('/profile')">
                  <UserRound :size="16" />
                  我的空间
                </button>
                <button type="button" class="user-menu__item" role="menuitem" @click="go('/notes')">
                  <NotebookPen :size="16" />
                  随笔笔记
                </button>
                <button
                  type="button"
                  class="user-menu__item user-menu__item--danger"
                  role="menuitem"
                  @click="handleLogout"
                >
                  <LogOut :size="16" />
                  退出登录
                </button>
              </div>
            </CollapseTransition>
          </div>
        </template>

        <template v-else>
          <button type="button" class="ghost-btn" @click="router.push('/login')">登录</button>
          <button type="button" class="primary-btn" @click="router.push('/login')">
            立即开始
            <ArrowRight :size="16" />
          </button>
        </template>

        <button
          type="button"
          class="icon-btn nav-toggle"
          aria-label="打开菜单"
          :aria-expanded="mobileOpen"
          @click.stop="mobileOpen = !mobileOpen"
        >
          <Menu :size="19" />
        </button>
      </div>
    </div>

    <!-- 移动端菜单 -->
    <CollapseTransition :max-height="360">
      <div v-if="mobileOpen" class="mobile-menu" @click.stop>
        <router-link class="mobile-menu__item" to="/" @click="mobileOpen = false">首页</router-link>
        <router-link class="mobile-menu__item" to="/square" @click="mobileOpen = false">伴侣广场</router-link>
        <router-link class="mobile-menu__item" to="/history" @click="mobileOpen = false">聊天记录</router-link>
        <router-link class="mobile-menu__item" to="/memory" @click="mobileOpen = false">记忆管理</router-link>
        <router-link class="mobile-menu__item" to="/calendar" @click="mobileOpen = false">情绪日历</router-link>
        <router-link class="mobile-menu__item" to="/notes" @click="mobileOpen = false">随笔笔记</router-link>
        <router-link class="mobile-menu__item" to="/profile" @click="mobileOpen = false">我的空间</router-link>

        <template v-if="userStore.isAuthenticated">
          <button type="button" class="mobile-menu__item mobile-menu__item--danger" @click="handleLogout">
            退出登录
          </button>
        </template>
        <template v-else>
          <button
            type="button"
            class="mobile-menu__item"
            @click="router.push('/login'); mobileOpen = false"
          >
            登录 / 注册
          </button>
        </template>
      </div>
    </CollapseTransition>
  </nav>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRight,
  ChevronDown,
  LogOut,
  Menu,
  MessagesSquare,
  NotebookPen,
  UserRound,
} from 'lucide-vue-next'
import { useUserStore } from '@/stores/user'
import CollapseTransition from '@/components/ui/CollapseTransition.vue'
import AvatarImage from '@/components/ui/AvatarImage.vue'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

const menuOpen = ref(false)
const mobileOpen = ref(false)
// 头像兜底由 AvatarImage 组件统一处理（按用户名/seed 生成），这里不再需要

/** 当前路由名，用来标 is-active */
const currentName = computed(() => String(route.name ?? ''))
const isRoute = (name: string) => currentName.value === name

/** 头像失败兜底已收进 AvatarImage 组件，此处不再需要 */

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const go = (path: string) => {
  menuOpen.value = false
  mobileOpen.value = false
  router.push(path)
}

const handleLogout = () => {
  userStore.logout()
  menuOpen.value = false
  mobileOpen.value = false
  // 登出后必须回 /login：若 push('/') 且当前就在 '/'，vue-router 视为重复导航不触发守卫，
  // 会停在受保护页的未登录态。
  router.push('/login')
}

/** 点空白处关闭用户菜单（菜单内部已 stop 冒泡） */
const handleClickOutside = () => {
  menuOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* ---------- 顶栏 ---------- */
.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  border-bottom: 1px solid var(--line);
  background: rgba(17, 19, 17, 0.88);
  backdrop-filter: blur(18px);
}

.topbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-6);
  height: var(--topbar-h);
  width: min(var(--container), calc(100% - var(--gutter) * 2));
  margin: 0 auto;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0;
  border: 0;
  color: var(--text-strong);
  background: transparent;
  font-size: var(--fs-16);
  font-weight: 720;
  white-space: nowrap;
  cursor: pointer;
}

.brand-mark {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border-radius: 50%;
  color: #17120f;
  background: var(--primary);
  box-shadow: 0 8px 24px rgba(255, 139, 114, 0.22);
}

.brand-mark svg {
  width: 17px;
  height: 17px;
}

/* ---------- 导航 ---------- */
.nav {
  display: flex;
  align-items: center;
  gap: 2px;
}

.nav a {
  display: inline-flex;
  align-items: center;
  height: 34px;
  padding: 0 13px;
  border-radius: var(--radius-sm);
  color: var(--muted);
  font-size: var(--fs-13);
  white-space: nowrap;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.nav a:hover {
  color: var(--text-strong);
  background: rgba(255, 255, 255, 0.05);
}

.nav a.is-active {
  color: var(--text-strong);
  background: rgba(255, 255, 255, 0.07);
  font-weight: 650;
}

/* ---------- 右侧 ---------- */
.topbar-right {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.icon-btn {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  color: var(--muted);
  background: transparent;
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.icon-btn:hover {
  color: #fff;
  background: rgba(255, 255, 255, 0.07);
}

.nav-toggle {
  display: none;
}

.ghost-btn {
  height: 36px;
  padding: 0 16px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: var(--radius);
  color: var(--text);
  background: transparent;
  font-size: var(--fs-13);
  font-weight: 650;
  cursor: pointer;
  transition: border-color var(--dur) var(--ease);
}

.ghost-btn:hover {
  border-color: var(--line-strong);
}

.primary-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 36px;
  padding: 0 16px;
  border: 0;
  border-radius: var(--radius);
  color: var(--on-primary);
  background: var(--primary);
  font-size: var(--fs-13);
  font-weight: 700;
  cursor: pointer;
  box-shadow: var(--shadow-primary);
  transition: background var(--dur) var(--ease);
}

.primary-btn:hover {
  background: var(--primary-hover);
}

/* ---------- 用户菜单 ---------- */
.user-wrap {
  position: relative;
}

.user-button {
  display: flex;
  align-items: center;
  gap: 9px;
  height: 40px;
  padding: 4px 12px 4px 4px;
  border: 1px solid var(--line);
  border-radius: var(--radius-pill);
  color: var(--bone-dim);
  background: transparent;
  cursor: pointer;
  transition: border-color var(--dur) var(--ease);
}

.user-button:hover {
  border-color: rgba(255, 139, 114, 0.45);
}

.user-avatar {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  overflow: hidden;
  border-radius: 50%;
  background: #282b27;
}

.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-name {
  font-size: var(--fs-13);
  max-width: 8em;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-caret {
  color: var(--muted-faint);
}

.user-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  z-index: 50;
  min-width: 208px;
  padding: 5px;
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
  box-shadow: var(--shadow-lift);
}

.user-menu__head {
  padding: 9px 10px 11px;
  border-bottom: 1px solid var(--line);
}

.user-menu__name {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-13);
  font-weight: 650;
}

.user-menu__mail {
  margin: 2px 0 0;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-menu__item {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 9px 10px;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--text);
  background: transparent;
  font-size: var(--fs-13);
  text-align: left;
  cursor: pointer;
  transition: background var(--dur) var(--ease);
}

.user-menu__item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.user-menu__item--danger {
  color: var(--primary);
}

.user-menu__item--danger:hover {
  background: var(--danger-soft);
}

/* ---------- 移动端 ---------- */
.mobile-menu {
  display: none;
  flex-direction: column;
  gap: 2px;
  padding: var(--sp-3) var(--gutter) var(--sp-4);
  border-top: 1px solid var(--line);
}

.mobile-menu__item {
  display: flex;
  align-items: center;
  min-height: 42px;
  padding: 0 12px;
  border: 0;
  border-radius: var(--radius-sm);
  color: var(--text);
  background: transparent;
  font-size: var(--fs-14);
  text-align: left;
  cursor: pointer;
}

.mobile-menu__item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.mobile-menu__item--danger {
  color: var(--primary);
}

@media (max-width: 1024px) {
  .nav {
    display: none;
  }

  .nav-toggle {
    display: grid;
  }

  .mobile-menu {
    display: flex;
  }
}

@media (max-width: 760px) {
  .ghost-btn {
    display: none;
  }

  .primary-btn {
    height: 34px;
    padding: 0 12px;
  }

  .user-name,
  .user-caret {
    display: none;
  }

  .user-button {
    padding: 4px;
    border-color: transparent;
  }
}
</style>
