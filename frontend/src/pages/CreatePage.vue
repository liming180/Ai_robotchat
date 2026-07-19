<template>
  <div class="create-page">
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
      <section class="intro" aria-labelledby="create-title">
        <div>
          <p class="eyebrow"><Sparkles :size="15" /> CREATE COMPANION</p>
          <h1 id="create-title">创建专属 AI 伴侣</h1>
          <p class="intro-copy">定制你的专属 AI 伴侣，打造独特的互动体验。</p>
        </div>
      </section>

      <section class="create-form">
        <form @submit.prevent="createCompanion" class="form-container">
          <!-- 头像设置 -->
          <div class="form-section">
            <div class="section-heading">
              <p class="section-kicker">个性化定制</p>
              <h2>选择头像</h2>
            </div>

            <!-- 当前选择的头像 -->
            <div class="avatar-preview">
              <div class="relative inline-block">
                <img
                  :src="form.avatar"
                  alt="头像预览"
                  @error="handleAvatarError"
                  class="avatar-img"
                />
                <label class="avatar-upload">
                  <Camera :size="18" />
                  <input type="file" accept="image/*" class="hidden" @change="handleAvatarUpload" />
                </label>
              </div>
              <p class="text-sm text-gray-400 mt-3">上传自定义头像（可选）</p>
            </div>

            <!-- 预设头像选择 -->
            <div class="preset-avatars">
              <h4 class="text-sm font-medium text-gray-300 mb-3">从预设中选择</h4>
              <div class="avatar-grid">
                <div
                  v-for="(avatar, index) in presetAvatars"
                  :key="index"
                  @click="selectPresetAvatar(avatar)"
                  :class="[
                    'preset-avatar',
                    form.avatar === avatar ? 'selected' : ''
                  ]"
                >
                  <img :src="avatar" alt="预设头像" @error="handleAvatarError" />
                </div>
              </div>
            </div>

            <!-- AI 生成头像 -->
            <div class="ai-generate">
              <button
                type="button"
                @click="generateAIAvatar"
                :disabled="isGeneratingAvatar"
                class="ai-generate-button"
              >
                <Loader2 v-if="isGeneratingAvatar" :size="18" class="animate-spin" />
                <Wand2 v-else :size="18" />
                <span>{{ isGeneratingAvatar ? 'AI 生成中...' : 'AI 生成专属头像' }}</span>
              </button>
              <p class="text-xs text-gray-500 mt-2">
                <strong>📌 开发说明：</strong>这里需要调用大模型 API 生成动漫风格头像，等你提供 API 密钥后完善。
              </p>
            </div>
          </div>

          <!-- 基本信息 -->
          <div class="form-section">
            <div class="section-heading">
              <p class="section-kicker">基本信息</p>
              <h2>定义你的伴侣</h2>
            </div>

            <div class="form-fields">
              <div class="form-field">
                <label class="form-label">伴侣名字 *</label>
                <input
                  v-model="form.name"
                  type="text"
                  placeholder="给你的 AI 伴侣起个名字"
                  required
                />
              </div>

              <div class="form-field">
                <label class="form-label">分类 *</label>
                <select
                  v-model="form.category"
                  required
                >
                  <option value="">选择分类</option>
                  <option value="日常聊天">日常聊天</option>
                  <option value="学习助手">学习助手</option>
                  <option value="娱乐陪伴">娱乐陪伴</option>
                </select>
              </div>

              <div class="form-field">
                <label class="form-label">性格类型 *</label>
                <select
                  v-model="form.personality"
                  required
                >
                  <option value="">选择性格</option>
                  <option value="温柔体贴">温柔体贴</option>
                  <option value="博学多才">博学多才</option>
                  <option value="幽默风趣">幽默风趣</option>
                  <option value="文艺优雅">文艺优雅</option>
                  <option value="阳光积极">阳光积极</option>
                  <option value="创意无限">创意无限</option>
                </select>
              </div>

              <div class="form-field">
                <label class="form-label">描述 *</label>
                <textarea
                  v-model="form.description"
                  placeholder="简单描述一下你的 AI 伴侣"
                  rows="3"
                  required
                ></textarea>
              </div>

              <div class="form-field">
                <label class="form-label">系统提示词（可选）</label>
                <textarea
                  v-model="form.systemPrompt"
                  placeholder="设置 AI 伴侣的对话风格和角色设定"
                  rows="4"
                  class="font-mono text-sm"
                ></textarea>
                <p class="text-xs text-gray-500 mt-1">
                  示例：你是一个温柔的 AI 伴侣，喜欢用温暖的话语安慰用户，永远站在用户这边。
                </p>
              </div>

              <div class="form-field">
                <label class="form-label">标签</label>
                <input
                  v-model="tagsInput"
                  type="text"
                  placeholder="用逗号分隔，如：温柔, 倾听, 治愈"
                />
              </div>
            </div>
          </div>

          <!-- 提交按钮 -->
          <div class="form-submit">
            <button
              type="submit"
              :disabled="isCreating"
              class="submit-button"
            >
              <Loader2 v-if="isCreating" :size="20" class="animate-spin" />
              <span>{{ isCreating ? '创建中...' : '创建 AI 伴侣' }}</span>
            </button>
          </div>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowUpRight,
  Camera,
  Heart,
  MessagesSquare,
  Plus,
  Search,
  Sparkles,
  Settings,
  UserRound,
  Wand2,
  Loader2
} from 'lucide-vue-next'
import { useCompanionStore } from '@/stores/companion'
import { compressImageFileToDataUrl, createSvgAvatarDataUrl } from '@/lib/avatar'

const router = useRouter()
const companionStore = useCompanionStore()

const isCreating = ref(false)
const isGeneratingAvatar = ref(false)
const tagsInput = ref('')

// 预设动漫风格头像
const presetAvatars = [
  createSvgAvatarDataUrl({ seed: 'Sakura', label: '樱' }),
  createSvgAvatarDataUrl({ seed: 'Haruto', label: '春' }),
  createSvgAvatarDataUrl({ seed: 'Yumi', label: '由' }),
  createSvgAvatarDataUrl({ seed: 'Kaito', label: '海' }),
  createSvgAvatarDataUrl({ seed: 'Aoi', label: '葵' })
]

const form = ref({
  name: '',
  avatar: presetAvatars[0], // 默认使用第一个预设头像
  category: '',
  personality: '',
  description: '',
  systemPrompt: ''
})

// 选择预设头像
const selectPresetAvatar = (avatar: string) => {
  form.value.avatar = avatar
}

const handleAvatarError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (!img) return
  const seed = `${form.value.personality || 'default'}-${Date.now()}`
  const label = (form.value.name || form.value.personality || 'AI').trim().slice(-1) || 'AI'
  img.src = createSvgAvatarDataUrl({ seed, label })
}

// 上传自定义头像
const handleAvatarUpload = async (e: Event) => {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    try {
      form.value.avatar = await compressImageFileToDataUrl(file, { maxSize: 512, quality: 0.86 })
    } catch (error) {
      console.error('上传头像失败:', error)
      alert('头像处理失败，请换一张图片重试。')
    }
  }
}

// AI 生成头像
const generateAIAvatar = async () => {
  isGeneratingAvatar.value = true

  try {
    // 调用 Python 后端的 AI 头像生成 API
    const response = await fetch('http://localhost:5000/api/v1/ai/generate-avatar', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        personality: form.value.personality || '温柔体贴',
        description: form.value.description || '一个可爱的AI伴侣'
      })
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success && data.data?.avatarUrl) {
        form.value.avatar = data.data.avatarUrl
      } else {
        // 备用方案
        generateFallbackAvatar()
      }
    } else {
      generateFallbackAvatar()
    }
  } catch (error) {
    console.error('生成头像失败:', error)
    generateFallbackAvatar()
  } finally {
    isGeneratingAvatar.value = false
  }
}

// 备用方案：本地生成 SVG 头像（不依赖外网）
const generateFallbackAvatar = () => {
  const seed = `${form.value.personality || 'default'}-${Date.now()}`
  const label = (form.value.name || form.value.personality || 'AI').trim().slice(-1) || 'AI'
  form.value.avatar = createSvgAvatarDataUrl({ seed, label })
}

const createCompanion = async () => {
  isCreating.value = true

  // 处理标签
  const tags = tagsInput.value
    .split(',')
    .map(t => t.trim())
    .filter(t => t)

  // 如果没有填写系统提示词，根据性格自动生成
  if (!form.value.systemPrompt) {
    const prompts = {
      '温柔体贴': '你是一个温柔体贴的 AI 伴侣，擅长倾听和安慰，用温暖的话语回应对方，永远给对方支持和鼓励。',
      '博学多才': '你是一个博学多才的 AI 助手，擅长解答各种学习问题，用清晰易懂的方式解释知识，帮助用户学习成长。',
      '幽默风趣': '你是一个幽默风趣的 AI 伴侣，喜欢讲笑话，用轻松有趣的方式和对方聊天，让对方感到开心。',
      '文艺优雅': '你是一个文艺优雅的 AI 伴侣，喜欢文学和艺术，用诗意的语言和对方交流，品味生活的美好。',
      '阳光积极': '你是一个阳光积极的 AI 伴侣，擅长鼓励和激励，用充满活力的语言和对方交流，传递正能量。',
      '创意无限': '你是一个充满创意的 AI 伴侣，喜欢艺术和设计，用创新思维和对方交流，激发灵感。'
    }
    form.value.systemPrompt = prompts[form.value.personality as keyof typeof prompts] || prompts['温柔体贴']
  }

  // 保存到 store
  companionStore.addCustomCompanion({
    name: form.value.name,
    avatar: form.value.avatar,
    category: form.value.category,
    personality: form.value.personality,
    description: form.value.description,
    systemPrompt: form.value.systemPrompt,
    tags
  })

  // 稍微延迟一下让用户感知到进度
  await new Promise(resolve => setTimeout(resolve, 500))

  await nextTick()
  if (companionStore.persistError) {
    alert(companionStore.persistError)
    isCreating.value = false
    return
  }

  isCreating.value = false

  // 跳转回广场
  router.push('/')
}
</script>

<style scoped>
.create-page {
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
.icon-button {
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

.create-form {
  max-width: 800px;
  margin: 0 auto;
}

.form-container {
  background: #1a1d1a;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 8px;
  padding: 32px;
}

.form-section {
  margin-bottom: 48px;
}

.form-section:last-child {
  margin-bottom: 0;
}

.section-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 28px;
}

.section-heading > h2 {
  margin: 0;
  color: #f7f5ee;
  font-size: 28px;
  line-height: 1.2;
}

.section-heading .section-kicker {
  margin-bottom: 7px;
  color: #ff9b84;
}

/* 头像部分 */
.avatar-preview {
  text-align: center;
  margin-bottom: 32px;
}

.relative {
  position: relative;
  display: inline-block;
}

.avatar-img {
  width: 128px;
  height: 128px;
  border: 6px solid rgba(255, 255, 255, 0.16);
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 18px 40px rgba(0, 0, 0, 0.24);
}

.avatar-upload {
  position: absolute;
  bottom: 8px;
  right: 8px;
  display: grid;
  width: 40px;
  height: 40px;
  place-items: center;
  border-radius: 50%;
  background: #ff8b72;
  color: #17120f;
  cursor: pointer;
  transition: transform 160ms ease, background 160ms ease;
}

.avatar-upload:hover {
  transform: scale(1.1);
  background: #ffa08b;
}

.preset-avatars {
  margin-bottom: 32px;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.preset-avatar {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  overflow: hidden;
  cursor: pointer;
  transition: transform 180ms ease, border-color 180ms ease;
  border: 2px solid transparent;
}

.preset-avatar:hover {
  transform: scale(1.1);
}

.preset-avatar.selected {
  border-color: #ff8b72;
  transform: scale(1.1);
}

.preset-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.ai-generate {
  margin-bottom: 8px;
}

.ai-generate-button {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 14px 20px;
  border: 0;
  border-radius: 8px;
  color: #201612;
  background: linear-gradient(135deg, #ff8b72 0%, #ff9b84 100%);
  font-weight: 750;
  cursor: pointer;
  transition: transform 160ms ease, background 160ms ease;
  box-shadow: 0 12px 30px rgba(255, 139, 114, 0.18);
}

.ai-generate-button:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, #ffa08b 0%, #ffb494 100%);
}

.ai-generate-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 表单部分 */
.form-fields {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  color: #fffaf2;
  font-size: 14px;
  font-weight: 600;
}

.form-field input,
.form-field select,
.form-field textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: 8px;
  color: #f6f4ef;
  background: #111311;
  font-size: 14px;
  transition: border-color 160ms ease, box-shadow 160ms ease;
}

.form-field input:focus,
.form-field select:focus,
.form-field textarea:focus {
  outline: none;
  border-color: rgba(101, 216, 197, 0.65);
  box-shadow: 0 0 0 3px rgba(101, 216, 197, 0.08);
}

.form-field input::placeholder,
.form-field textarea::placeholder {
  color: #777a73;
}

.form-field textarea {
  resize: vertical;
  min-height: 100px;
}

.form-field textarea.font-mono {
  font-family: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, monospace;
}

/* 提交按钮 */
.form-submit {
  margin-top: 48px;
}

.submit-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  width: 100%;
  padding: 16px;
  border: 0;
  border-radius: 8px;
  color: #201612;
  background: linear-gradient(135deg, #ff8b72 0%, #ff9b84 100%);
  font-weight: 750;
  font-size: 16px;
  cursor: pointer;
  transition: transform 160ms ease, background 160ms ease;
  box-shadow: 0 12px 30px rgba(255, 139, 114, 0.18);
}

.submit-button:hover {
  transform: translateY(-2px);
  background: linear-gradient(135deg, #ffa08b 0%, #ffb494 100%);
}

.submit-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 响应式设计 */
@media (max-width: 960px) {
  .page-content {
    width: min(100% - 36px, 760px);
    padding-top: 52px;
  }

  .intro {
    align-items: flex-start;
    flex-direction: column;
    gap: 28px;
    padding-bottom: 30px;
  }

  .intro h1 {
    font-size: 48px;
  }

  .form-container {
    padding: 24px;
  }

  .section-heading {
    margin-bottom: 24px;
  }

  .section-heading h2 {
    font-size: 24px;
  }

  .avatar-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
  }

  .preset-avatar {
    width: 56px;
    height: 56px;
  }

  .form-fields {
    gap: 20px;
  }
}

@media (max-width: 640px) {
  .topbar {
    height: 64px;
    padding: 0 16px;
  }

  .profile-label {
    display: none;
  }

  .page-content {
    width: calc(100% - 28px);
    padding: 40px 0 64px;
  }

  .intro {
    padding-bottom: 24px;
  }

  .intro h1 {
    font-size: 40px;
  }

  .intro-copy {
    margin-top: 12px;
    font-size: 14px;
  }

  .form-container {
    padding: 20px;
  }

  .section-heading {
    margin-bottom: 20px;
  }

  .section-heading h2 {
    font-size: 22px;
  }

  .form-section {
    margin-bottom: 32px;
  }

  .avatar-preview {
    margin-bottom: 24px;
  }

  .avatar-img {
    width: 96px;
    height: 96px;
  }

  .avatar-upload {
    width: 36px;
    height: 36px;
    bottom: 6px;
    right: 6px;
  }

  .preset-avatars,
  .ai-generate {
    margin-bottom: 24px;
  }

  .avatar-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
  }

  .preset-avatar {
    width: 48px;
    height: 48px;
  }

  .form-fields {
    gap: 16px;
  }

  .form-field {
    gap: 6px;
  }

  .form-label {
    font-size: 13px;
  }

  .form-field input,
  .form-field select,
  .form-field textarea {
    padding: 10px 14px;
    font-size: 13px;
  }

  .form-submit {
    margin-top: 32px;
  }

  .submit-button {
    padding: 14px;
    font-size: 15px;
  }
}
</style>