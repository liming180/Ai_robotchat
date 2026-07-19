<template>
  <div class="profile-page">
    <header class="topbar">
      <button class="brand" type="button" @click="router.push('/')" aria-label="返回首页">
        <span class="brand-mark"><Heart :size="19" fill="currentColor" /></span>
        <span>AI 伴侣</span>
      </button>

      <div class="topbar-actions">
        <button class="icon-button" type="button" title="聊天记录" aria-label="聊天记录" @click="router.push('/history')">
          <MessagesSquare :size="20" />
        </button>
        <button class="profile-button" type="button" @click="router.push('/profile')">
          <span class="profile-avatar"><UserRound :size="18" /></span>
          <span class="profile-label">我的空间</span>
        </button>
      </div>
    </header>

    <main class="page-content">
      <section class="intro" aria-labelledby="profile-title">
        <div>
          <p class="eyebrow"><Sparkles :size="15" /> PERSONAL SPACE</p>
          <h1 id="profile-title">我的空间</h1>
          <p class="intro-copy">在这里查看你的 AI 伴侣、对话记录和收藏的伙伴。</p>
        </div>
      </section>

      <!-- 统计数据 -->
      <section class="stats-section">
        <div class="stat-cards">
          <div class="stat-card">
            <div class="stat-value">{{ companionStore.allCompanions.length }}</div>
            <div class="stat-label">AI 伴侣</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ chatStore.conversations.length }}</div>
            <div class="stat-label">对话</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ totalMessages }}</div>
            <div class="stat-label">消息</div>
          </div>
        </div>
      </section>

      <section class="menu-section">
        <div class="menu-grid">
          <button @click="$router.push('/history')" class="menu-item">
            <div class="menu-icon">
              <MessagesSquare :size="20" />
            </div>
            <div class="menu-content">
              <h3>聊天历史</h3>
              <p>查看历史对话</p>
            </div>
          </button>

          <button @click="$router.push('/')" class="menu-item">
            <div class="menu-icon">
              <Heart :size="20" fill="currentColor" />
            </div>
            <div class="menu-content">
              <h3>我的收藏</h3>
              <p>管理收藏的伴侣</p>
            </div>
          </button>

          <button @click="$router.push('/create')" class="menu-item">
            <div class="menu-icon">
              <Plus :size="20" />
            </div>
            <div class="menu-content">
              <h3>创建伴侣</h3>
              <p>自定义专属 AI</p>
            </div>
          </button>

          <button @click="showSettings = true" class="menu-item">
            <div class="menu-icon">
              <Settings :size="20" />
            </div>
            <div class="menu-content">
              <h3>设置</h3>
              <p>通用设置</p>
            </div>
          </button>
        </div>
      </section>

      <section class="favorites-section">
        <div class="section-heading">
          <div>
            <p class="section-kicker">常伴左右</p>
            <h2>我的收藏</h2>
          </div>
          <span>{{ favoriteCompanions.length }} 位伙伴</span>
        </div>

        <div v-if="favoriteCompanions.length" class="favorite-grid">
          <article
            v-for="(companion, index) in favoriteCompanions"
            :key="companion.id"
            class="favorite-card"
            :class="`tone-${index % 3}`"
            tabindex="0"
            @click="startChat(companion.id)"
            @keydown.enter="startChat(companion.id)"
          >
            <div class="favorite-visual">
              <img
                :src="companion.avatar"
                :alt="companion.name"
                :data-seed="companion.id"
                :data-label="companion.name"
                @error="handleCompanionAvatarError"
              />
              <span class="online-dot" title="随时可以聊天"></span>
            </div>
            <div class="favorite-content">
              <div class="favorite-meta">
                <span>{{ companion.category }}</span>
                <button
                  type="button"
                  title="取消收藏"
                  aria-label="取消收藏"
                  @click.stop="toggleFavorite(companion.id)"
                >
                  <Heart :size="18" fill="currentColor" />
                </button>
              </div>
              <h3>{{ companion.name }}</h3>
              <p>{{ companion.description }}</p>
              <div class="favorite-footer">
                <div class="intimacy">
                  <span>默契值 {{ companion.intimacy }}%</span>
                  <div><i :style="{ width: `${Math.max(companion.intimacy, 6)}%` }"></i></div>
                </div>
                <span class="chat-arrow"><ArrowUpRight :size="19" /></span>
              </div>
            </div>
          </article>
        </div>
      </section>

      <!-- 设置弹窗 -->
      <div v-if="showSettings" class="fixed inset-0 z-50 flex items-center justify-center p-6">
        <div class="absolute inset-0 bg-black/60" @click="showSettings = false"></div>
        <div class="relative bg-slate-900 border border-white/10 rounded-3xl p-8 max-w-md w-full shadow-2xl">
          <h3 class="text-xl font-bold text-white mb-6">设置</h3>
          <div class="space-y-4">
            <button
              @click="clearAllData" class="w-full p-4 border border-red-500/50 text-red-400 rounded-xl hover:bg-red-500/10 transition-colors flex items-center justify-center gap-3">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
              清除所有数据
            </button>
            <button
              @click="showSettings = false" class="w-full p-4 bg-white/5 border border-white/10 text-slate-300 rounded-xl hover:bg-white/10 transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowUpRight,
  Heart,
  MessagesSquare,
  Plus,
  Search,
  Sparkles,
  Settings,
  UserRound,
} from 'lucide-vue-next'
import { useCompanionStore } from '@/stores/companion'
import { useChatStore } from '@/stores/chat'
import { createSvgAvatarDataUrl } from '@/lib/avatar'

const router = useRouter()
const companionStore = useCompanionStore()
const chatStore = useChatStore()

const showSettings = ref(false)
const favoriteCompanions = computed(() => companionStore.favoriteCompanions)

const totalMessages = computed(() => {
  return chatStore.conversations.reduce((acc, conv) => acc + conv.messages.length, 0)
})

const startChat = (companionId: string) => {
  router.push(`/chat/${companionId}`)
}

const toggleFavorite = (id: string) => companionStore.toggleFavorite(id)

const handleCompanionAvatarError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (!img) return
  const seed = img.dataset.seed || String(Date.now())
  const name = img.dataset.label || 'AI'
  const label = name.trim().slice(-1) || 'AI'
  img.src = createSvgAvatarDataUrl({ seed, label })
}

const clearAllData = () => {
  if (confirm('确定要清除所有数据吗？这将删除所有对话和自定义伴侣。')) {
    // 清除 localStorage
    localStorage.clear()
    // 刷新页面来重置所有状态
    location.reload()
  }
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  color: #f6f4ef;
  background:
    radial-gradient(circle at 13% 8%, rgba(45, 212, 191, 0.07), transparent 26rem),
    radial-gradient(circle at 88% 24%, rgba(251, 113, 133, 0.07), transparent 28rem),
    #111311;
}

.topbar {
  position: sticky;
  z-index: 20;
  top: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 72px;
  padding: 0 max(24px, calc((100vw - 1240px) / 2));
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(17, 19, 17, 0.88);
  backdrop-filter: blur(18px);
}

.brand,
.profile-button,
.icon-button,
.favorite-button,
.favorite-meta button {
  border: 0;
  color: inherit;
  background: transparent;
  cursor: pointer;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 0;
  color: #fffaf2;
  font-size: 17px;
  font-weight: 720;
}

.brand-mark {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 50%;
  color: #17120f;
  background: #ff8b72;
  box-shadow: 0 8px 24px rgba(255, 139, 114, 0.22);
}

.topbar-actions,
.profile-button {
  display: flex;
  align-items: center;
}

.topbar-actions { gap: 8px; }

.icon-button {
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 50%;
  color: #aaa9a2;
}

.icon-button:hover { color: white; background: rgba(255, 255, 255, 0.07); }

.profile-button {
  gap: 9px;
  padding: 5px 12px 5px 5px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  color: #dbd8d0;
}

.profile-button:hover { border-color: rgba(255, 139, 114, 0.45); }
.profile-avatar { display: grid; width: 30px; height: 30px; place-items: center; border-radius: 50%; background: #282b27; }
.profile-label { font-size: 13px; }

.page-content {
  width: min(1240px, calc(100% - 48px));
  margin: 0 auto;
  padding: 72px 0 96px;
}

.intro {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 48px;
  padding-bottom: 38px;
}

.eyebrow,
.section-kicker {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0 0 13px;
  color: #65d8c5;
  font-size: 11px;
  font-weight: 750;
  letter-spacing: 0;
}

.intro h1 {
  max-width: 760px;
  margin: 0;
  color: #fffaf2;
  font-size: clamp(40px, 5.2vw, 68px);
  font-weight: 760;
  line-height: 1.08;
  letter-spacing: 0;
}

.intro-copy {
  max-width: 610px;
  margin: 20px 0 0;
  color: #aaa9a2;
  font-size: 16px;
  line-height: 1.8;
}

.stats-section {
  padding-top: 54px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.stat-card {
  display: flex;
  min-height: 140px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 8px;
  background: #1a1d1a;
  cursor: pointer;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  border-color: rgba(101, 216, 197, 0.36);
  background: #1e211e;
}

.stat-value {
  font-size: 48px;
  font-weight: 760;
  background: linear-gradient(135deg, #ff8b72 0%, #65d8c5 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.stat-label {
  margin-top: 8px;
  color: #777a73;
  font-size: 13px;
}

.menu-section {
  padding-top: 54px;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 8px;
  background: #1a1d1a;
  cursor: pointer;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
}

.menu-item:hover {
  transform: translateY(-3px);
  border-color: rgba(255, 139, 114, 0.45);
  background: #1e211e;
}

.menu-icon {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 12px;
  color: #ff8b72;
  background: rgba(255, 139, 114, 0.12);
}

.menu-content {
  flex: 1;
  min-width: 0;
}

.menu-content h3 {
  margin: 0 0 4px;
  color: #fffaf2;
  font-size: 18px;
  font-weight: 600;
}

.menu-content p {
  margin: 0;
  color: #9b9d96;
  font-size: 13px;
}

.favorites-section {
  padding-top: 54px;
}

.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
}

.section-heading h2 {
  margin: 0;
  color: #f7f5ee;
  font-size: 25px;
  line-height: 1.2;
}

.section-heading .section-kicker {
  margin-bottom: 7px;
  color: #ff9b84;
}

.section-heading > span {
  color: #777a73;
  font-size: 13px;
}

.favorite-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.favorite-card {
  display: grid;
  min-height: 240px;
  grid-template-columns: 176px 1fr;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: #1b1e1b;
  cursor: pointer;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease;
}

.favorite-card:hover {
  transform: translateY(-3px);
  border-color: rgba(255, 255, 255, 0.22);
  background: #20231f;
}

.favorite-visual {
  position: relative;
  display: grid;
  min-height: 240px;
  place-items: center;
  background: #355f58;
}

.tone-1 .favorite-visual {
  background: #6c4e58;
}

.tone-2 .favorite-visual {
  background: #756536;
}

.favorite-visual::after {
  position: absolute;
  inset: 12px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 50%;
  content: '';
}

.favorite-visual img {
  position: relative;
  z-index: 1;
  width: 112px;
  height: 112px;
  border: 6px solid rgba(255, 255, 255, 0.16);
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.24);
}

.online-dot {
  position: absolute;
  z-index: 2;
  right: 42px;
  bottom: 63px;
  width: 13px;
  height: 13px;
  border: 3px solid #355f58;
  border-radius: 50%;
  background: #83e8b0;
}

.tone-1 .online-dot {
  border-color: #6c4e58;
}

.tone-2 .online-dot {
  border-color: #756536;
}

.favorite-content {
  display: flex;
  min-width: 0;
  flex-direction: column;
  padding: 24px;
}

.favorite-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #94968f;
  font-size: 12px;
}

.favorite-meta button {
  display: grid;
  padding: 4px;
  place-items: center;
  color: #ff8b72;
}

.favorite-content h3 {
  margin: 18px 0 8px;
  color: #fffaf2;
  font-size: 27px;
}

.favorite-content > p {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: #aaa9a2;
  font-size: 13px;
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.favorite-footer {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
  margin-top: auto;
  padding-top: 20px;
}

.intimacy {
  flex: 1;
  color: #858881;
  font-size: 11px;
}

.intimacy > div {
  height: 3px;
  margin-top: 7px;
  overflow: hidden;
  background: #343832;
}

.intimacy i {
  display: block;
  height: 100%;
  background: #65d8c5;
}

.chat-arrow {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  color: #1b1e1b;
  background: #e8e5dc;
}

@media (max-width: 960px) {
  .page-content {
    width: min(100% - 36px, 760px);
    padding-top: 52px;
  }

  .intro {
    align-items: flex-start;
    flex-direction: column;
    gap: 28px;
  }

  .stat-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .menu-grid,
  .favorite-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .topbar {
    height: 64px;
    padding: 0 16px;
  }

  .profile-label,
  .search-box kbd {
    display: none;
  }

  .profile-button {
    padding-right: 5px;
  }

  .page-content {
    width: calc(100% - 28px);
    padding: 40px 0 64px;
  }

  .intro {
    padding-bottom: 30px;
  }

  .intro h1 {
    font-size: 40px;
  }

  .intro-copy {
    margin-top: 15px;
    font-size: 14px;
  }

  .stats-section,
  .menu-section,
  .favorites-section {
    padding-top: 42px;
  }

  .stat-cards,
  .menu-grid,
  .favorite-grid {
    grid-template-columns: 1fr;
  }

  .favorite-card {
    min-height: 220px;
    grid-template-columns: 118px 1fr;
  }

  .favorite-visual {
    min-height: 220px;
  }

  .favorite-visual img {
    width: 82px;
    height: 82px;
  }

  .favorite-visual::after {
    inset: 10px;
  }

  .online-dot {
    right: 25px;
    bottom: 64px;
  }

  .favorite-content {
    padding: 20px 16px;
  }

  .favorite-content h3 {
    margin-top: 13px;
    font-size: 23px;
  }
}
</style>