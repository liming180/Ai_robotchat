<template>
  <div class="profile">
    <Navbar />

    <main class="profile-main">
      <!-- 页头 -->
      <header class="page-head">
        <p class="eyebrow">
          <Sparkles :size="15" />
          PERSONAL SPACE
        </p>

        <div class="page-head__row">
          <div>
            <h1 class="page-title">我的空间</h1>

            <div class="account">
              <button
                type="button"
                class="account__avatar"
                aria-label="更换头像"
                @click="openEditProfile"
              >
                <AvatarImage
                  :src="userStore.user?.avatar"
                  :name="userStore.user?.name"
                  :seed="userStore.user?.id || 'self'"
                  size="xl"
                />
                <span class="account__avatar-mask">
                  <Camera :size="16" />
                </span>
              </button>

              <div class="account__copy">
                <p class="account__name">
                  {{ userStore.user?.name || '我的账号' }}
                  <button type="button" class="account__edit" @click="openEditProfile">
                    <Pencil :size="13" />
                    编辑
                  </button>
                </p>
                <p class="account__meta">{{ userStore.user?.email || '未登录' }}</p>
              </div>
            </div>
          </div>

          <button type="button" class="btn btn-ghost" @click="handleLogout">
            <LogOut :size="16" />
            退出登录
          </button>
        </div>
      </header>

      <!-- 数字 -->
      <div class="stats">
        <div class="stat">
          <span>AI 伴侣</span>
          <strong><AnimatedNumber :value="companionStore.allCompanions.length" /></strong>
        </div>
        <div class="stat">
          <span>会话</span>
          <strong><AnimatedNumber :value="chatStore.conversations.length" /></strong>
        </div>
        <div class="stat">
          <span>收藏</span>
          <strong><AnimatedNumber :value="favoriteCompanions.length" /></strong>
        </div>
        <div class="stat">
          <span>累计对话</span>
          <strong>
            <AnimatedNumber :value="totalMessages" /><i>条</i>
          </strong>
        </div>
      </div>

      <div class="profile-grid">
        <!-- ===== 左：功能列表 ===== -->
        <div class="menu-list">
          <router-link class="menu-item" to="/history">
            <span class="menu-item__ico"><MessagesSquare :size="16" /></span>
            <span class="menu-item__copy">
              <b>聊天记录</b>
              <small>按时间倒序，接着上次继续</small>
            </span>
            <span class="menu-item__num">{{ chatStore.conversations.length }}</span>
            <ArrowRight :size="16" class="menu-item__chev" />
          </router-link>

          <router-link class="menu-item" to="/memory">
            <span class="menu-item__ico"><Brain :size="16" /></span>
            <span class="menu-item__copy">
              <b>记忆管理</b>
              <small>它记住的关于你的事，可改可删</small>
            </span>
            <ArrowRight :size="16" class="menu-item__chev" />
          </router-link>

          <router-link class="menu-item" to="/calendar">
            <span class="menu-item__ico"><CalendarHeart :size="16" /></span>
            <span class="menu-item__copy">
              <b>情绪日历</b>
              <small>查看心情变化轨迹</small>
            </span>
            <ArrowRight :size="16" class="menu-item__chev" />
          </router-link>

          <router-link class="menu-item" to="/notes">
            <span class="menu-item__ico"><NotebookPen :size="16" /></span>
            <span class="menu-item__copy">
              <b>随笔笔记</b>
              <small>AI 生成的故事和你自己写的，都在这里</small>
            </span>
            <ArrowRight :size="16" class="menu-item__chev" />
          </router-link>

          <router-link class="menu-item" to="/square">
            <span class="menu-item__ico"><Heart :size="16" /></span>
            <span class="menu-item__copy">
              <b>我的收藏</b>
              <small>
                {{ favoriteCompanions.length ? favoriteCompanions.map((c) => c.name).join('、') : '还没有收藏' }}
              </small>
            </span>
            <span class="menu-item__num">{{ favoriteCompanions.length }}</span>
            <ArrowRight :size="16" class="menu-item__chev" />
          </router-link>

          <router-link class="menu-item" to="/create">
            <span class="menu-item__ico"><Plus :size="16" /></span>
            <span class="menu-item__copy">
              <b>创建伴侣</b>
              <small>名字、头像、性格、知识库，全都自己定</small>
            </span>
            <ArrowRight :size="16" class="menu-item__chev" />
          </router-link>
        </div>

        <!-- ===== 右：收藏 + 数据 ===== -->
        <aside class="profile-aside">
          <section class="side-card">
            <h2>收藏的伙伴</h2>

            <div v-if="favoriteCompanions.length" class="fav-list">
              <button
                v-for="companion in favoriteCompanions"
                :key="companion.id"
                type="button"
                class="fav-row"
                @click="startChat(companion.id)"
              >
                <AvatarImage
                  :src="companion.avatar"
                  :name="companion.name"
                  :seed="companion.id"
                  size="sm"
                />
                <span class="fav-row__copy">
                  <span class="fav-row__name">{{ companion.name }}</span>
                  <span class="fav-row__meta">默契 {{ companion.intimacy }}%</span>
                </span>
                <ArrowUpRight :size="14" class="fav-row__go" />
              </button>
            </div>

            <p v-else class="side-empty">还没有收藏。去广场挑一个吧。</p>

            <router-link class="side-more" to="/square">
              去广场挑一个
              <ArrowRight :size="14" />
            </router-link>
          </section>

          <section class="side-card">
            <h2>偏好设置</h2>

            <div class="setting">
              <div class="setting__copy">
                <b>知识库增强</b>
                <small>新对话默认打开 RAG</small>
              </div>
              <ToggleSwitch v-model="prefs.rag" size="sm" label="知识库增强" />
            </div>

            <div class="setting">
              <div class="setting__copy">
                <b>自动记忆</b>
                <small>从对话里自动提取值得记的事</small>
              </div>
              <ToggleSwitch v-model="prefs.memory" size="sm" label="自动记忆" />
            </div>

            <div class="setting">
              <div class="setting__copy">
                <b>情绪感知</b>
                <small>回复时参考你的情绪记录</small>
              </div>
              <ToggleSwitch v-model="prefs.emotion" size="sm" label="情绪感知" />
            </div>

            <p class="setting-note">
              开关只作用于本机，暂未同步到服务端。
            </p>
          </section>

          <section class="side-card">
            <h2>数据</h2>

            <div class="data-links">
              <button type="button" class="data-link" @click="clearLocalCache">
                <Eraser :size="15" />
                清除本地缓存
              </button>
              <button type="button" class="data-link data-link--danger" @click="handleLogout">
                <LogOut :size="15" />
                退出登录
              </button>
            </div>

            <p class="setting-note">
              清除缓存只清本机副本，不会删除账号里的数据，也不会退出登录。
            </p>
          </section>
        </aside>
      </div>
    </main>

    <!-- ===== 编辑资料对话框 ===== -->
    <ModalDialog
      v-model="showEditProfile"
      title="编辑个人资料"
      description="昵称与头像会显示在顶栏、侧栏和聊天页。"
      :width="460"
      :close-on-backdrop="!savingProfile"
      :close-on-esc="!savingProfile"
      @close="resetEditForm"
    >
      <div class="edit-avatar">
        <AvatarImage
          :src="draftAvatar || userStore.user?.avatar"
          :name="draftName || userStore.user?.name"
          :seed="userStore.user?.id || 'self'"
          size="xl"
        />

        <div class="edit-avatar__actions">
          <input
            ref="avatarInputRef"
            type="file"
            accept="image/*"
            class="hidden-input"
            @change="handleAvatarPick"
          />

          <button
            type="button"
            class="btn btn-ghost btn-sm"
            :disabled="uploadingAvatar"
            @click="avatarInputRef?.click()"
          >
            <ImagePlus :size="15" />
            {{ uploadingAvatar ? '上传中…' : '上传图片' }}
          </button>

          <button
            type="button"
            class="btn btn-quiet btn-sm"
            :disabled="!draftAvatar"
            @click="draftAvatar = ''"
          >
            恢复默认
          </button>
        </div>
      </div>

      <label class="field">
        <span>昵称</span>
        <input
          v-model="draftName"
          class="input"
          type="text"
          placeholder="怎么称呼你"
          maxlength="20"
          @keydown.enter.prevent="saveProfile"
        />
        <small>{{ draftName.trim().length }} / 20</small>
      </label>

      <label class="field">
        <span>邮箱</span>
        <input class="input" type="email" :value="userStore.user?.email || ''" disabled />
        <small>邮箱是登录凭据，暂不支持修改</small>
      </label>

      <p v-if="profileError" class="form-error" role="alert">{{ profileError }}</p>

      <template #footer>
        <button type="button" class="btn btn-ghost" :disabled="savingProfile" @click="showEditProfile = false">
          取消
        </button>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="!canSaveProfile"
          @click="saveProfile"
        >
          {{ savingProfile ? '保存中…' : '保存' }}
        </button>
      </template>
    </ModalDialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  ArrowUpRight,
  Brain,
  CalendarHeart,
  Camera,
  Eraser,
  Heart,
  ImagePlus,
  LogOut,
  Pencil,
  MessagesSquare,
  NotebookPen,
  Plus,
  Sparkles,
} from 'lucide-vue-next'
import Navbar from '@/components/Navbar.vue'
import AnimatedNumber from '@/components/ui/AnimatedNumber.vue'
import ToggleSwitch from '@/components/ui/ToggleSwitch.vue'
import AvatarImage from '@/components/ui/AvatarImage.vue'
import ModalDialog from '@/components/ui/ModalDialog.vue'
import { useToast } from '@/composables/useToast'
import { useCompanionStore } from '@/stores/companion'
import { useChatStore } from '@/stores/chat'
import { useUserStore } from '@/stores/user'
import { clearBusinessCache, uploadImage } from '@/lib/api'
import { compressImage } from '@/lib/image'

const router = useRouter()
const companionStore = useCompanionStore()
const chatStore = useChatStore()
const userStore = useUserStore()
const toast = useToast()

/** 本机偏好开关（暂存内存，刷新回到默认开） */
const prefs = reactive({
  rag: true,
  memory: true,
  emotion: true,
})

const favoriteCompanions = computed(() => companionStore.favoriteCompanions)

/** 头像首字兜底已收进 AvatarImage 组件，此处不再需要 */

// ── 编辑个人资料 ──
const showEditProfile = ref(false)
const avatarInputRef = ref<HTMLInputElement | null>(null)
const draftName = ref('')
/** 新头像地址（已上传到服务器的 URL）；空字符串表示用默认兜底 */
const draftAvatar = ref('')
const uploadingAvatar = ref(false)
const savingProfile = ref(false)
const profileError = ref('')

const openEditProfile = () => {
  draftName.value = userStore.user?.name || ''
  draftAvatar.value = userStore.user?.avatar || ''
  profileError.value = ''
  showEditProfile.value = true
}

const resetEditForm = () => {
  if (savingProfile.value) return
  profileError.value = ''
  uploadingAvatar.value = false
}

const canSaveProfile = computed(() => {
  if (savingProfile.value || uploadingAvatar.value) return false
  return draftName.value.trim().length > 0
})

/** 选图 → 压缩 → 上传到 Java，拿到 URL 后暂存在 draftAvatar，保存时再落库 */
const handleAvatarPick = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  if (!file.type.startsWith('image/')) {
    profileError.value = '请选择图片文件'
    return
  }

  uploadingAvatar.value = true
  profileError.value = ''

  try {
    // 头像压缩到 512px 就够：显示最大是 92px，2x 足够，还能省一半流量
    const dataUrl = await compressImage(file, 512, 0.9)
    draftAvatar.value = await uploadImage(dataUrl)
  } catch (err) {
    profileError.value = `头像上传失败：${(err as Error).message}`
  } finally {
    uploadingAvatar.value = false
  }
}

const saveProfile = async () => {
  if (!canSaveProfile.value) return

  savingProfile.value = true
  profileError.value = ''

  try {
    await userStore.updateProfile({
      name: draftName.value.trim(),
      avatar: draftAvatar.value,
    })
    showEditProfile.value = false
    toast.success('个人资料已更新')
  } catch (err) {
    profileError.value = `保存失败：${(err as Error).message}`
    toast.error('保存失败，请重试')
  } finally {
    savingProfile.value = false
  }
}

/** 累计对话：所有会话的消息总数 */
const totalMessages = computed(() =>
  chatStore.conversations.reduce((sum, conv) => sum + conv.messages.length, 0),
)

onMounted(() => {
  companionStore.loadCompanions()
  chatStore.loadConversations()
})

/** 头像色调已收进 AvatarImage 组件，此处不再需要 */

const startChat = (companionId: string) => {
  router.push(`/chat/${companionId}`)
}

const handleLogout = () => {
  userStore.logout()
  toast.success('已退出登录')
  router.push('/login')
}

/**
 * 清除本地缓存（不是删除账号数据）。
 *
 * 只清业务缓存 key（会话/情绪/记忆/笔记等前端副本），**保留 token 与主题偏好**：
 * 用户清完仍是登录状态，刷新后各页面会重新从服务器拉取。
 */
const clearLocalCache = () => {
  if (
    !confirm(
      '清除本地缓存？\n\n这只清除本机浏览器里的副本，不会删除账号里的任何数据，也不会退出登录。',
    )
  ) {
    return
  }
  clearBusinessCache()
  toast.success('本地缓存已清除，正在重新加载')
  setTimeout(() => location.reload(), 600)
}
</script>

<style scoped>
.profile {
  min-height: 100vh;
}

.profile-main {
  width: min(1100px, calc(100% - var(--gutter) * 2));
  margin: 0 auto;
  padding: var(--sp-14) 0 var(--sp-24);
}

/* ---------- 页头 ---------- */
.eyebrow {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0 0 13px;
  color: var(--accent);
  font-size: var(--fs-12);
  font-weight: 750;
}

.page-head {
  padding-bottom: var(--sp-6);
}

.page-head__row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--sp-8);
}

.page-title {
  margin: 0;
  color: var(--text-strong);
  font-size: clamp(30px, 4vw, var(--fs-34));
  font-weight: 760;
  line-height: var(--lh-tight);
}

.account {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  margin-top: var(--sp-5);
}

.account__copy {
  min-width: 0;
}

.account__name {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-19);
  font-weight: 720;
}

.account__meta {
  margin: 2px 0 0;
  color: var(--muted);
  font-size: var(--fs-13);
}

.account__avatar {
  position: relative;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  overflow: hidden;
}

/* 悬停时压一层半透明遮罩 + 相机图标，提示「可以换」 */
.account__avatar-mask {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: #fff;
  background: rgba(9, 11, 9, 0.6);
  opacity: 0;
  transition: opacity var(--dur) var(--ease);
}

.account__avatar:hover .account__avatar-mask,
.account__avatar:focus-visible .account__avatar-mask {
  opacity: 1;
}

.account__name {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
}

.account__edit {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  min-height: 24px;
  padding: 0;
  border: 0;
  color: var(--accent);
  background: transparent;
  font-size: var(--fs-12);
  font-weight: 500;
  cursor: pointer;
}

.account__edit:hover {
  text-decoration: underline;
}

/* ---------- 编辑资料对话框 ---------- */
.edit-avatar {
  display: flex;
  align-items: center;
  gap: var(--sp-5);
  margin-bottom: var(--sp-5);
  padding-bottom: var(--sp-5);
  border-bottom: 1px solid var(--line);
}

.edit-avatar__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
}

.btn-sm {
  min-height: 34px;
  padding: 0 12px;
  font-size: var(--fs-12);
}

.btn-quiet {
  color: var(--muted);
  background: transparent;
}

.btn-quiet:hover:not(:disabled) {
  color: var(--text);
  background: rgba(255, 255, 255, 0.05);
}

.btn-quiet:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.field {
  display: block;
}

.field + .field {
  margin-top: var(--sp-4);
}

.field > span {
  display: block;
  margin-bottom: var(--sp-2);
  color: var(--text);
  font-size: var(--fs-13);
  font-weight: 650;
}

.field > small {
  display: block;
  margin-top: 7px;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.input {
  width: 100%;
  min-height: 44px;
  padding: 11px 14px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-card);
  color: var(--text);
  background: var(--bg);
  font-size: var(--fs-14);
  transition:
    border-color var(--dur) var(--ease),
    box-shadow var(--dur) var(--ease);
}

.input::placeholder {
  color: var(--muted-faint);
}

.input:focus {
  outline: none;
  border-color: var(--accent-line);
  box-shadow: var(--ring-accent);
}

.input:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.hidden-input {
  display: none;
}

.form-error {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-top: var(--sp-4);
  padding: 10px 12px;
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--danger-soft);
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

/* ---------- 数字条 ---------- */
.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.stat {
  padding: var(--sp-5) var(--sp-5) var(--sp-5) 0;
  border-right: 1px solid var(--line);
}

.stat:last-child {
  border-right: 0;
}

.stat span {
  display: block;
  color: var(--muted);
  font-size: var(--fs-13);
}

.stat strong {
  display: flex;
  align-items: baseline;
  gap: 3px;
  margin-top: 6px;
  color: var(--text-strong);
  font-size: var(--fs-28);
  font-weight: 760;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.stat strong i {
  font-style: normal;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  font-weight: 400;
}

/* ---------- 布局 ---------- */
.profile-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: var(--sp-8);
  align-items: start;
  padding-top: var(--sp-8);
}

/* ---------- 功能列表 ---------- */
.menu-list {
  border-top: 1px solid var(--line);
}

.menu-item {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4) 0;
  border-bottom: 1px solid var(--line);
  transition: padding-left var(--dur) var(--ease);
}

.menu-item:hover {
  padding-left: 4px;
}

.menu-item__ico {
  display: grid;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: var(--bg-soft);
  transition:
    color var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.menu-item:hover .menu-item__ico {
  color: var(--accent);
  border-color: var(--line-strong);
}

.menu-item__copy {
  min-width: 0;
  flex: 1;
}

.menu-item__copy b {
  display: block;
  color: var(--text);
  font-size: var(--fs-14);
  font-weight: 500;
}

.menu-item__copy small {
  display: block;
  margin-top: 2px;
  overflow: hidden;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.menu-item__num {
  flex-shrink: 0;
  color: var(--muted);
  font-size: var(--fs-13);
  font-variant-numeric: tabular-nums;
}

.menu-item__chev {
  flex-shrink: 0;
  color: var(--muted-faint);
  transition:
    transform var(--dur) var(--ease),
    color var(--dur) var(--ease);
}

.menu-item:hover .menu-item__chev {
  color: var(--accent);
  transform: translateX(2px);
}

/* ---------- 右栏 ---------- */
.side-card {
  padding: var(--sp-5);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

.side-card + .side-card {
  margin-top: var(--sp-3);
}

.side-card h2 {
  margin: 0 0 var(--sp-4);
  color: var(--text-strong);
  font-size: var(--fs-13);
  font-weight: 650;
}

/* 收藏 */
.fav-list {
  display: flex;
  flex-direction: column;
}

.fav-row {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  width: 100%;
  padding: 9px 0;
  border: 0;
  border-bottom: 1px solid var(--line);
  background: transparent;
  text-align: left;
  cursor: pointer;
}

.fav-row:last-of-type {
  border-bottom: 0;
}

.fav-row__copy {
  min-width: 0;
  flex: 1;
}

.fav-row__name {
  display: block;
  color: var(--text);
  font-size: var(--fs-13);
  font-weight: 500;
}

.fav-row__meta {
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.fav-row__go {
  flex-shrink: 0;
  color: var(--muted-faint);
  transition: color var(--dur) var(--ease);
}

.fav-row:hover .fav-row__go {
  color: var(--accent);
}

.side-empty {
  margin: 0;
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

.side-more {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  min-height: 24px;
  margin-top: var(--sp-3);
  color: var(--accent);
  font-size: var(--fs-13);
}

.side-more:hover {
  text-decoration: underline;
}

/* 设置 */
.setting {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  padding: 11px 0;
  border-bottom: 1px solid var(--line);
}

.setting:last-of-type {
  border-bottom: 0;
  padding-bottom: 0;
}

.setting__copy {
  min-width: 0;
}

.setting__copy b {
  display: block;
  color: var(--text);
  font-size: var(--fs-13);
  font-weight: 500;
}

.setting__copy small {
  display: block;
  margin-top: 2px;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.setting-note {
  margin: var(--sp-4) 0 0;
  padding-top: var(--sp-3);
  border-top: 1px solid var(--line);
  color: var(--muted-faint);
  font-size: var(--fs-12);
  line-height: 1.7;
}

/* 数据 */
.data-links {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
}

.data-link {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0;
  border: 0;
  color: var(--muted);
  background: transparent;
  font-size: var(--fs-13);
  text-align: left;
  cursor: pointer;
  transition: color var(--dur) var(--ease);
}

.data-link:hover {
  color: var(--text);
}

.data-link--danger {
  color: var(--primary);
}

.data-link--danger:hover {
  color: var(--primary-hover);
}

/* ---------- 按钮 ---------- */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 40px;
  padding: 0 16px;
  border: 0;
  border-radius: var(--radius);
  font-size: var(--fs-13);
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.btn-ghost {
  border: 1px solid rgba(255, 255, 255, 0.16);
  color: var(--text);
  background: transparent;
}

.btn-ghost:hover {
  border-color: var(--line-strong);
  background: rgba(255, 255, 255, 0.04);
}

/* ---------- 响应式 ---------- */
@media (max-width: 1024px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }

  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stat:nth-child(2) {
    border-right: 0;
  }

  .stat:nth-child(1),
  .stat:nth-child(2) {
    border-bottom: 1px solid var(--line);
  }

  .page-head__row {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--sp-4);
  }
}

@media (max-width: 760px) {
  .profile-main {
    padding: var(--sp-10) 0 var(--sp-16);
  }

  .account {
    flex-wrap: wrap;
  }
}
</style>
