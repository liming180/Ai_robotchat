<template>
  <div class="square-page">
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
      <section class="intro" aria-labelledby="square-title">
        <div>
          <p class="eyebrow"><Sparkles :size="15" /> COMPANION SQUARE</p>
          <h1 id="square-title">今天，想和谁聊聊？</h1>
          <p class="intro-copy">每一位伙伴都有自己的性格与专长。选一个懂你此刻心情的人，开始一段轻松的对话。</p>
        </div>
        <button class="create-button" type="button" @click="router.push('/create')">
          <Plus :size="19" />
          <span>创建专属伴侣</span>
        </button>
      </section>

      <section class="discovery-tools" aria-label="搜索和筛选">
        <label class="search-box">
          <Search :size="20" />
          <input v-model.trim="searchQuery" type="search" placeholder="搜索名字、性格或标签" aria-label="搜索 AI 伴侣" />
          <button v-if="searchQuery" type="button" title="清空搜索" aria-label="清空搜索" @click="searchQuery = ''">
            <X :size="17" />
          </button>
          <kbd>⌘ K</kbd>
        </label>

        <div class="category-tabs" role="tablist" aria-label="伴侣分类">
          <button
            v-for="category in categories"
            :key="category"
            type="button"
            role="tab"
            :aria-selected="selectedCategory === category"
            :class="{ active: selectedCategory === category }"
            @click="selectedCategory = category"
          >
            {{ category }}
          </button>
        </div>
      </section>

      <section v-if="favoriteCompanions.length && !searchQuery && selectedCategory === '全部'" class="favorites-section">
        <div class="section-heading">
          <div>
            <p class="section-kicker">常伴左右</p>
            <h2>我的收藏</h2>
          </div>
          <span>{{ favoriteCompanions.length }} 位伙伴</span>
        </div>

        <div class="favorite-grid">
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

      <section class="all-section">
        <div class="section-heading">
          <div>
            <p class="section-kicker">{{ resultKicker }}</p>
            <h2>{{ resultTitle }}</h2>
          </div>
          <span>{{ filteredCompanions.length }} 个结果</span>
        </div>

        <div v-if="filteredCompanions.length" class="companion-grid">
          <article
            v-for="(companion, index) in filteredCompanions"
            :key="companion.id"
            class="companion-card"
            tabindex="0"
            @click="startChat(companion.id)"
            @keydown.enter="startChat(companion.id)"
          >
            <div class="card-topline">
              <span class="category-icon" :class="`category-${categoryKey(companion.category)}`">
                <component :is="categoryIcon(companion.category)" :size="16" />
              </span>
              <button
                type="button"
                :title="companion.isFavorite ? '取消收藏' : '加入收藏'"
                :aria-label="companion.isFavorite ? '取消收藏' : '加入收藏'"
                :class="['favorite-button', { active: companion.isFavorite }]"
                @click.stop="toggleFavorite(companion.id)"
              >
                <Heart :size="19" :fill="companion.isFavorite ? 'currentColor' : 'none'" />
              </button>
            </div>

            <div class="avatar-wrap" :class="`avatar-tone-${index % 6}`">
              <img
                :src="companion.avatar"
                :alt="companion.name"
                :data-seed="companion.id"
                :data-label="companion.name"
                @error="handleCompanionAvatarError"
              />
            </div>

            <div class="card-copy">
              <p class="personality">{{ companion.personality }}</p>
              <h3>{{ companion.name }}</h3>
              <p class="description">{{ companion.description }}</p>
            </div>

            <div class="tag-row">
              <span v-for="tag in companion.tags.slice(0, 3)" :key="tag">{{ tag }}</span>
            </div>

            <div class="card-footer">
              <div class="mini-intimacy">
                <HeartHandshake :size="16" />
                <span>默契 {{ companion.intimacy }}%</span>
              </div>
              <span class="start-chat">开始聊天 <ArrowRight :size="17" /></span>
            </div>
          </article>
        </div>

        <div v-else class="empty-state">
          <span><SearchX :size="28" /></span>
          <h3>暂时没有找到合适的伙伴</h3>
          <p>换一个关键词，或者看看其他分类。</p>
          <button type="button" @click="resetFilters">查看全部伴侣</button>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  Coffee,
  Heart,
  HeartHandshake,
  Laugh,
  MessagesSquare,
  Plus,
  Search,
  SearchX,
  Sparkles,
  UserRound,
  X,
} from 'lucide-vue-next'
import { useCompanionStore } from '@/stores/companion'
import { createSvgAvatarDataUrl } from '@/lib/avatar'

const router = useRouter()
const companionStore = useCompanionStore()

const searchQuery = ref('')
const selectedCategory = ref('全部')
const categories = ['全部', '日常聊天', '学习助手', '娱乐陪伴']

const filteredCompanions = computed(() => {
  const categoryMatches = selectedCategory.value === '全部'
    ? companionStore.allCompanions
    : companionStore.filterByCategory(selectedCategory.value)

  const query = searchQuery.value.toLocaleLowerCase()
  if (!query) return categoryMatches

  return categoryMatches.filter(companion =>
    companion.name.toLocaleLowerCase().includes(query)
    || companion.description.toLocaleLowerCase().includes(query)
    || companion.personality.toLocaleLowerCase().includes(query)
    || companion.tags.some(tag => tag.toLocaleLowerCase().includes(query))
  )
})

const favoriteCompanions = computed(() => companionStore.favoriteCompanions)
const resultKicker = computed(() => searchQuery.value ? '搜索结果' : '认识新朋友')
const resultTitle = computed(() => selectedCategory.value === '全部' ? '发现更多伙伴' : selectedCategory.value)

const categoryIcon = (category: string) => {
  if (category === '学习助手') return BookOpen
  if (category === '娱乐陪伴') return Laugh
  return Coffee
}

const categoryKey = (category: string) => {
  if (category === '学习助手') return 'study'
  if (category === '娱乐陪伴') return 'fun'
  return 'daily'
}

const startChat = (companionId: string) => router.push(`/chat/${companionId}`)
const toggleFavorite = (id: string) => companionStore.toggleFavorite(id)

const resetFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = '全部'
}

const handleCompanionAvatarError = (event: Event) => {
  const img = event.target as HTMLImageElement
  if (!img) return
  const seed = img.dataset.seed || String(Date.now())
  const name = img.dataset.label || 'AI'
  img.src = createSvgAvatarDataUrl({ seed, label: name.trim().slice(-1) || 'AI' })
}
</script>

<style scoped>
.square-page {
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

.create-button {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 9px;
  min-height: 48px;
  padding: 0 20px;
  border: 0;
  border-radius: 7px;
  color: #201612;
  background: #ff8b72;
  font-weight: 750;
  cursor: pointer;
  box-shadow: 0 12px 30px rgba(255, 139, 114, 0.18);
  transition: transform 160ms ease, background 160ms ease;
}

.create-button:hover { transform: translateY(-2px); background: #ffa08b; }

.discovery-tools {
  display: flex;
  align-items: center;
  gap: 18px;
  padding: 18px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.search-box {
  display: flex;
  flex: 1 1 420px;
  align-items: center;
  gap: 11px;
  height: 48px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 7px;
  color: #7c7f78;
  background: #1a1d1a;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.search-box:focus-within { border-color: rgba(101, 216, 197, 0.65); box-shadow: 0 0 0 3px rgba(101, 216, 197, 0.08); }
.search-box input { min-width: 0; flex: 1; border: 0; outline: 0; color: #f6f4ef; background: transparent; font-size: 14px; }
.search-box input::placeholder { color: #777a73; }
.search-box button { display: grid; padding: 4px; border: 0; place-items: center; color: #8d8f89; background: transparent; cursor: pointer; }
.search-box kbd { padding: 2px 7px; border: 1px solid rgba(255,255,255,.1); border-radius: 4px; color: #777a73; font: 11px/18px inherit; background: rgba(255,255,255,.035); }

.category-tabs { display: flex; flex: 0 0 auto; gap: 5px; padding: 4px; border-radius: 7px; background: #1a1d1a; }
.category-tabs button { min-height: 38px; padding: 0 15px; border: 0; border-radius: 5px; color: #9d9e98; background: transparent; font-size: 13px; cursor: pointer; white-space: nowrap; }
.category-tabs button:hover { color: #f3f1eb; }
.category-tabs button.active { color: #171917; background: #e8e5dc; font-weight: 720; }

.favorites-section,
.all-section { padding-top: 54px; }

.section-heading { display: flex; align-items: end; justify-content: space-between; gap: 24px; margin-bottom: 20px; }
.section-heading h2 { margin: 0; color: #f7f5ee; font-size: 25px; line-height: 1.2; }
.section-heading .section-kicker { margin-bottom: 7px; color: #ff9b84; }
.section-heading > span { color: #777a73; font-size: 13px; }

.favorite-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
.favorite-card { display: grid; min-height: 240px; grid-template-columns: 176px 1fr; overflow: hidden; border: 1px solid rgba(255,255,255,.1); border-radius: 8px; background: #1b1e1b; cursor: pointer; transition: transform 180ms ease, border-color 180ms ease, background 180ms ease; }
.favorite-card:hover { transform: translateY(-3px); border-color: rgba(255,255,255,.22); background: #20231f; }
.favorite-visual { position: relative; display: grid; min-height: 240px; place-items: center; background: #355f58; }
.tone-1 .favorite-visual { background: #6c4e58; }
.tone-2 .favorite-visual { background: #756536; }
.favorite-visual::after { position: absolute; inset: 12px; border: 1px solid rgba(255,255,255,.16); border-radius: 50%; content: ''; }
.favorite-visual img { position: relative; z-index: 1; width: 112px; height: 112px; border: 6px solid rgba(255,255,255,.16); border-radius: 50%; object-fit: cover; box-shadow: 0 18px 40px rgba(0,0,0,.24); }
.online-dot { position: absolute; z-index: 2; right: 42px; bottom: 63px; width: 13px; height: 13px; border: 3px solid #355f58; border-radius: 50%; background: #83e8b0; }
.tone-1 .online-dot { border-color: #6c4e58; }
.tone-2 .online-dot { border-color: #756536; }
.favorite-content { display: flex; min-width: 0; flex-direction: column; padding: 24px; }
.favorite-meta { display: flex; align-items: center; justify-content: space-between; color: #94968f; font-size: 12px; }
.favorite-meta button { display: grid; padding: 4px; place-items: center; color: #ff8b72; }
.favorite-content h3 { margin: 18px 0 8px; color: #fffaf2; font-size: 27px; }
.favorite-content > p { display: -webkit-box; overflow: hidden; margin: 0; color: #aaa9a2; font-size: 13px; line-height: 1.7; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.favorite-footer { display: flex; align-items: end; justify-content: space-between; gap: 18px; margin-top: auto; padding-top: 20px; }
.intimacy { flex: 1; color: #858881; font-size: 11px; }
.intimacy > div { height: 3px; margin-top: 7px; overflow: hidden; background: #343832; }
.intimacy i { display: block; height: 100%; background: #65d8c5; }
.chat-arrow { display: grid; width: 36px; height: 36px; flex: 0 0 auto; place-items: center; border-radius: 50%; color: #1b1e1b; background: #e8e5dc; }

.companion-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; }
.companion-card { display: flex; min-height: 410px; flex-direction: column; padding: 18px; border: 1px solid rgba(255,255,255,.09); border-radius: 8px; background: #1a1d1a; cursor: pointer; transition: transform 180ms ease, border-color 180ms ease, background 180ms ease; }
.companion-card:hover { transform: translateY(-4px); border-color: rgba(101,216,197,.36); background: #1e211e; }
.card-topline { display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; }
.category-icon { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 50%; color: #58cdb9; background: rgba(88,205,185,.12); }
.category-icon.category-study { color: #e8bd61; background: rgba(232,189,97,.12); }
.category-icon.category-fun { color: #ff8b72; background: rgba(255,139,114,.12); }
.favorite-button { display: grid; width: 36px; height: 36px; place-items: center; border-radius: 50%; color: #686c66; }
.favorite-button:hover { color: #d3d1ca; background: rgba(255,255,255,.05); }
.favorite-button.active { color: #ff8b72; }
.avatar-wrap { display: grid; height: 132px; place-items: center; overflow: hidden; border-radius: 6px; background: #294640; }
.avatar-tone-1 { background: #57434b; }
.avatar-tone-2 { background: #554e31; }
.avatar-tone-3 { background: #3e475b; }
.avatar-tone-4 { background: #4d3d56; }
.avatar-tone-5 { background: #42543c; }
.avatar-wrap img { width: 92px; height: 92px; border: 4px solid rgba(255,255,255,.16); border-radius: 50%; object-fit: cover; box-shadow: 0 12px 28px rgba(0,0,0,.22); transition: transform 200ms ease; }
.companion-card:hover .avatar-wrap img { transform: scale(1.05); }
.card-copy { padding-top: 19px; }
.personality { margin: 0 0 4px; color: #65d8c5; font-size: 11px; font-weight: 720; }
.card-copy h3 { margin: 0; color: #fffaf2; font-size: 22px; }
.description { display: -webkit-box; min-height: 44px; overflow: hidden; margin: 8px 0 0; color: #9b9d96; font-size: 13px; line-height: 1.7; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.tag-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 14px; }
.tag-row span { padding: 4px 8px; border: 1px solid rgba(255,255,255,.09); border-radius: 4px; color: #a7a8a1; font-size: 11px; }
.card-footer { display: flex; align-items: center; justify-content: space-between; gap: 10px; margin-top: auto; padding-top: 18px; border-top: 1px solid rgba(255,255,255,.07); color: #777a73; font-size: 12px; }
.mini-intimacy,
.start-chat { display: flex; align-items: center; gap: 6px; }
.start-chat { color: #e7e4dc; font-weight: 650; }
.companion-card:hover .start-chat { color: #65d8c5; }

.empty-state { display: grid; min-height: 330px; place-items: center; align-content: center; padding: 48px; border: 1px dashed rgba(255,255,255,.14); border-radius: 8px; text-align: center; }
.empty-state > span { display: grid; width: 58px; height: 58px; place-items: center; border-radius: 50%; color: #65d8c5; background: rgba(101,216,197,.1); }
.empty-state h3 { margin: 18px 0 7px; font-size: 19px; }
.empty-state p { margin: 0; color: #8d8f89; font-size: 14px; }
.empty-state button { margin-top: 22px; padding: 10px 16px; border: 1px solid rgba(255,255,255,.16); border-radius: 6px; color: #f3f0e9; background: transparent; cursor: pointer; }

@media (max-width: 960px) {
  .page-content { width: min(100% - 36px, 760px); padding-top: 52px; }
  .intro { align-items: flex-start; flex-direction: column; gap: 28px; }
  .discovery-tools { align-items: stretch; flex-direction: column; }
  .search-box { flex-basis: auto; }
  .category-tabs { overflow-x: auto; }
  .favorite-grid,
  .companion-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .favorite-card { grid-template-columns: 138px 1fr; }
}

@media (max-width: 640px) {
  .topbar { height: 64px; padding: 0 16px; }
  .profile-label,
  .search-box kbd { display: none; }
  .profile-button { padding-right: 5px; }
  .page-content { width: calc(100% - 28px); padding: 40px 0 64px; }
  .intro { padding-bottom: 30px; }
  .intro h1 { font-size: 40px; }
  .intro-copy { margin-top: 15px; font-size: 14px; }
  .create-button { width: 100%; justify-content: center; }
  .category-tabs button { padding: 0 12px; }
  .favorites-section,
  .all-section { padding-top: 42px; }
  .favorite-grid,
  .companion-grid { grid-template-columns: 1fr; }
  .favorite-card { min-height: 220px; grid-template-columns: 118px 1fr; }
  .favorite-visual { min-height: 220px; }
  .favorite-visual img { width: 82px; height: 82px; }
  .favorite-visual::after { inset: 10px; }
  .online-dot { right: 25px; bottom: 64px; }
  .favorite-content { padding: 20px 16px; }
  .favorite-content h3 { margin-top: 13px; font-size: 23px; }
  .companion-card { min-height: 390px; }
}
</style>
