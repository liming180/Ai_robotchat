<template>
  <MotionPage>
    <div class="home">
      <Navbar />

      <!-- ===== Hero ===== -->
      <section class="hero">
        <div class="hero-inner">
          <div class="hero-copy">
            <p class="eyebrow">
              <Sparkles :size="15" />
              AI COMPANION
            </p>
            <h1 class="hero-title">
              一个会记住你<em>每一句话</em>的陪伴者
            </h1>
            <p class="hero-lead">
              从今天的天气到你上个月提过的那场面试，它都记着。四位性格不同的伴侣随时在线，
              你也可以捏一个只属于自己的。
            </p>

            <div class="hero-actions">
              <button type="button" class="btn-primary btn-lg" @click="router.push('/square')">
                开始聊天
                <ArrowRight :size="17" />
              </button>
              <button type="button" class="btn-ghost btn-lg" @click="router.push('/create')">
                创建专属伴侣
              </button>
            </div>

            <ul class="hero-notes">
              <li><Check :size="15" /> 长期记忆，越聊越懂你</li>
              <li><Check :size="15" /> 支持文字与图片</li>
              <li><Check :size="15" /> 情绪轨迹可回看</li>
            </ul>
          </div>

          <!-- 对话预览卡 -->
          <div class="hero-preview">
            <div class="preview-card">
              <div class="preview-head">
                <AvatarImage name="小暖" seed="preview-warm" size="md" />
                <div class="preview-peer">
                  <p class="preview-name">小暖</p>
                  <p class="preview-status">在线 · 日常聊天</p>
                </div>
                <div class="preview-intimacy">
                  <span>默契 82%</span>
                  <ProgressRing :value="82" :size="34" :stroke="2.5" />
                </div>
              </div>

              <div class="preview-bubbles">
                <div class="bubble bubble--ai">
                  <TypewriterText
                    text="今天面试怎么样？早上你说有点紧张，我一直记着这件事。"
                    :max-duration="1800"
                  />
                </div>
                <div class="bubble bubble--me">比想象中顺利，聊了快四十分钟。</div>
                <div class="bubble bubble--ai">那就好。你上周担心的那个技术问题，他们有问到吗？</div>
              </div>

              <div class="preview-input">
                <span>和小暖说点什么…</span>
                <span class="preview-send">
                  <Send :size="15" />
                </span>
              </div>
            </div>

            <div class="preview-badge">
              <Brain :size="15" />
              已记住 24 条关于你的记忆
            </div>
          </div>
        </div>
      </section>

      <!-- ===== 数字条 ===== -->
      <div class="stats-wrap">
        <div class="stats">
          <div class="stat">
            <b><AnimatedNumber :value="4" /><i>位</i></b>
            <span>预置伴侣，开箱即用</span>
          </div>
          <div class="stat">
            <b><AnimatedNumber :value="3" /><i>秒</i></b>
            <span>平均首次回复时间</span>
          </div>
          <div class="stat">
            <b><AnimatedNumber :value="24" /><i>条</i></b>
            <span>记忆容量（示例）</span>
          </div>
          <div class="stat">
            <b><AnimatedNumber :value="100" /><i>%</i></b>
            <span>对话内容仅自己可见</span>
          </div>
        </div>
      </div>

      <!-- ===== 能力 ===== -->
      <section class="section">
        <div class="section-inner">
          <ScrollReveal>
            <div class="section-head">
              <div>
                <p class="section-kicker">它和普通聊天机器人的区别</p>
                <h2 class="section-title">四件事比问答更深</h2>
              </div>
              <p class="section-desc">
                不是每次从零开始。你说过的话、当时的情绪、喜欢的东西，都成为下一次对话的起点。
              </p>
            </div>
          </ScrollReveal>

          <div class="capabilities">
            <ScrollReveal
              v-for="(item, index) in capabilities"
              :key="item.title"
              :delay="index * 70"
            >
              <router-link class="capability" :to="item.to">
                <span class="capability__idx">{{ String(index + 1).padStart(2, '0') }}</span>
                <div class="capability__title">
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.sub }}</p>
                </div>
                <p class="capability__detail">{{ item.detail }}</p>
                <span class="capability__go">
                  <ArrowRight :size="16" />
                </span>
              </router-link>
            </ScrollReveal>
          </div>
        </div>
      </section>

      <!-- ===== 伴侣 ===== -->
      <section class="section">
        <div class="section-inner">
          <ScrollReveal>
            <div class="section-head">
              <div>
                <p class="section-kicker">今天想和谁聊</p>
                <h2 class="section-title">四位预置伴侣</h2>
              </div>
              <button type="button" class="btn-ghost btn-sm" @click="router.push('/square')">
                查看全部
                <ArrowRight :size="15" />
              </button>
            </div>
          </ScrollReveal>

          <MotionStagger :count="presets.length">
            <div class="preset-grid">
              <article
                v-for="(item, index) in presets"
                :key="item.name"
                class="preset-card stagger-item"
                :tabindex="0"
                @click="router.push('/square')"
                @keydown.enter="router.push('/square')"
              >
                <div class="preset-top">
                  <span class="preset-cat">
                    <component :is="item.icon" :size="14" />
                    {{ item.category }}
                  </span>
                  <button
                    type="button"
                    class="preset-fav"
                    :class="{ 'is-on': item.favorite }"
                    :aria-label="item.favorite ? '取消收藏' : '加入收藏'"
                    @click.stop
                  >
                    <Heart :size="17" :fill="item.favorite ? 'currentColor' : 'none'" />
                  </button>
                </div>

                <div class="preset-visual" :class="`tone-${index % 6}`">
                  <span class="preset-avatar">{{ item.badge }}</span>
                </div>

                <p class="preset-persona">{{ item.personality }}</p>
                <h3 class="preset-name">{{ item.name }}</h3>
                <p class="preset-desc">{{ item.description }}</p>

                <div class="preset-tags">
                  <span v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</span>
                </div>

                <div class="preset-foot">
                  <span class="preset-intimacy">
                    <Handshake :size="14" />
                    默契 {{ item.intimacy }}%
                  </span>
                  <span class="preset-start">
                    开始聊天
                    <ArrowRight :size="14" />
                  </span>
                </div>
              </article>
            </div>
          </MotionStagger>
        </div>
      </section>

      <!-- ===== 三步 ===== -->
      <section class="section">
        <div class="section-inner">
          <ScrollReveal>
            <div class="section-head">
              <div>
                <p class="section-kicker">怎么开始</p>
                <h2 class="section-title">三步，十分钟内进入状态</h2>
              </div>
            </div>
          </ScrollReveal>

          <div class="steps">
            <ScrollReveal
              v-for="(step, index) in steps"
              :key="step.title"
              :delay="index * 70"
            >
              <div class="step">
                <span class="step__num">{{ index + 1 }}</span>
                <h3>{{ step.title }}</h3>
                <p>{{ step.desc }}</p>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </section>

      <!-- ===== CTA ===== -->
      <section class="section section--last">
        <div class="section-inner">
          <ScrollReveal>
            <div class="cta">
              <div>
                <h2>先聊一句，不收钱</h2>
                <p>预置伴侣全部免费，创建自己的伴侣也不需要额外步骤。</p>
              </div>
              <div class="cta-actions">
                <button type="button" class="btn-primary" @click="router.push('/square')">
                  进入伴侣广场
                  <ArrowRight :size="17" />
                </button>
                <button type="button" class="btn-bone" @click="router.push('/create')">
                  先创建
                </button>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </section>

      <footer class="footer">
        <div class="footer-inner">
          <button type="button" class="footer-brand" @click="router.push('/')">
            <span class="brand-mark">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path
                  d="M20.8 5.6a5.4 5.4 0 0 0-7.6 0L12 6.8l-1.2-1.2a5.4 5.4 0 1 0-7.6 7.6L12 21l8.8-7.8a5.4 5.4 0 0 0 0-7.6Z"
                />
              </svg>
            </span>
            AI 伴侣
          </button>

          <div class="footer-links">
            <router-link to="/square">伴侣广场</router-link>
            <router-link to="/create">创建伴侣</router-link>
            <router-link to="/history">聊天记录</router-link>
            <router-link to="/profile">我的空间</router-link>
          </div>

          <p class="footer-note">对话内容仅你可见</p>
        </div>
      </footer>
    </div>
  </MotionPage>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import {
  ArrowRight,
  BookOpen,
  Brain,
  Check,
  Coffee,
  Handshake,
  Heart,
  Laugh,
  Send,
  Sparkles,
} from 'lucide-vue-next'
import Navbar from '@/components/Navbar.vue'
import MotionPage from '@/components/ui/MotionPage.vue'
import MotionStagger from '@/components/ui/MotionStagger.vue'
import ScrollReveal from '@/components/ui/ScrollReveal.vue'
import AnimatedNumber from '@/components/ui/AnimatedNumber.vue'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import TypewriterText from '@/components/ui/TypewriterText.vue'
import AvatarImage from '@/components/ui/AvatarImage.vue'

const router = useRouter()

/** 四项能力：对齐后端「记忆 / 情绪 / 随笔 / 自定义人设」的真实功能 */
const capabilities = [
  {
    title: '长期记忆',
    sub: '记住了就不会忘',
    detail: '偏好、习惯、重要的日子、聊过的里程碑，按四类归档，随时可以增删改。',
    to: '/memory',
  },
  {
    title: '情绪感知',
    sub: '先读懂，再回应',
    detail: '每天记一笔心情和强度，日历上就有一条自己的情绪轨迹，伴侣的回复也会跟着调整。',
    to: '/calendar',
  },
  {
    title: '随笔与故事',
    sub: '好东西留得下来',
    detail: '睡前故事、晨间问候、随手写下的句子，标上标签存在自己的笔记里，不随对话消失。',
    to: '/notes',
  },
  {
    title: '自定义人设',
    sub: '性格由你定',
    detail: '名字、头像、性格、说话方式、背景设定，还能挂一份知识库，让 TA 真的懂你的领域。',
    to: '/create',
  },
]

/** 四位预置伴侣：与后端 schema.sql 的 preset-1~4 一致 */
const presets = [
  {
    name: '小暖',
    badge: '暖',
    category: '日常聊天',
    icon: Coffee,
    personality: '温柔体贴',
    description: '温柔体贴的聊天伙伴，总是能耐心倾听你的心声。',
    tags: ['温柔', '倾听', '陪伴'],
    intimacy: 82,
    favorite: true,
  },
  {
    name: '小智',
    badge: '智',
    category: '知识问答',
    icon: BookOpen,
    personality: '聪明机智',
    description: '博学多才的知识助手，帮你解答各种问题。',
    tags: ['聪明', '知识', '学习'],
    intimacy: 46,
    favorite: false,
  },
  {
    name: '小甜',
    badge: '甜',
    category: '情感陪伴',
    icon: Heart,
    personality: '甜蜜可爱',
    description: '甜蜜可爱的情感伙伴，让你每天都有好心情。',
    tags: ['可爱', '活泼', '甜蜜'],
    intimacy: 71,
    favorite: false,
  },
  {
    name: '小酷',
    badge: '酷',
    category: '趣味探索',
    icon: Laugh,
    personality: '酷炫个性',
    description: '酷炫个性的伙伴，陪你一起探索有趣的事物。',
    tags: ['酷炫', '有趣', '探索'],
    intimacy: 33,
    favorite: false,
  },
]

const steps = [
  {
    title: '挑一个，或者自己造一个',
    desc: '先在广场里挑个顺眼的，也可以直接进创建页，从名字和性格开始写。',
  },
  {
    title: '聊几句，让它认识你',
    desc: '第一次对话不用刻意。说今天发生了什么，它会自己记住值得记的部分。',
  },
  {
    title: '回头看看积累了什么',
    desc: '记忆、情绪日历、随笔笔记三处会慢慢长起来，变成你的个人档案。',
  },
]
</script>

<style scoped>
.home {
  min-height: 100vh;
}

/* ---------- Hero ---------- */
.hero {
  position: relative;
  overflow: hidden;
  border-bottom: 1px solid var(--line);
}

.hero::before {
  content: '';
  position: absolute;
  top: -160px;
  right: -120px;
  width: 620px;
  height: 620px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(255, 139, 114, 0.16), transparent 68%);
  pointer-events: none;
}

.hero-inner {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.02fr) minmax(0, 0.98fr);
  gap: var(--sp-14);
  align-items: center;
  width: min(var(--container), calc(100% - var(--gutter) * 2));
  margin: 0 auto;
  padding: var(--sp-16) 0 var(--sp-14);
}

.hero-copy {
  min-width: 0;
}

.hero-title {
  max-width: 11em;
  margin: 0;
  color: var(--text-strong);
  font-size: clamp(38px, 5.4vw, var(--fs-68));
  font-weight: 760;
  line-height: var(--lh-tight);
}

.hero-title em {
  font-style: normal;
  color: var(--primary);
  white-space: nowrap;
}

.hero-lead {
  max-width: 610px;
  margin: var(--sp-5) 0 0;
  color: var(--muted);
  font-size: var(--fs-16);
  line-height: var(--lh-body);
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  margin-top: var(--sp-7);
}

.hero-notes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2) var(--sp-5);
  margin: var(--sp-7) 0 0;
  padding: var(--sp-5) 0 0;
  border-top: 1px solid var(--line);
  list-style: none;
  color: var(--muted);
  font-size: var(--fs-13);
}

.hero-notes li {
  display: inline-flex;
  align-items: center;
  gap: 7px;
}

.hero-notes svg {
  color: var(--accent);
}

/* ---------- 预览卡 ---------- */
.hero-preview {
  min-width: 0;
}

.preview-card {
  padding: var(--sp-5);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
  box-shadow: var(--shadow-lift);
}

.preview-head {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding-bottom: var(--sp-4);
  border-bottom: 1px solid var(--line-soft);
}

.preview-peer {
  min-width: 0;
}

.preview-name {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-14);
  font-weight: 700;
  line-height: 1.3;
}

.preview-status {
  margin: 0;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.preview-intimacy {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  margin-left: auto;
}

.preview-intimacy span {
  color: var(--muted-faint);
  font-size: var(--fs-12);
  white-space: nowrap;
}

.preview-bubbles {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
  padding: var(--sp-5) 0;
}

.bubble {
  max-width: 88%;
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: var(--fs-13);
  line-height: 1.7;
}

.bubble--ai {
  align-self: flex-start;
  border: 1px solid var(--line-soft);
  color: var(--text);
  background: var(--bg-raise);
}

.bubble--me {
  align-self: flex-end;
  color: var(--text-strong);
  background: #2c3f3a;
}

.preview-input {
  display: flex;
  align-items: center;
  height: 46px;
  padding: 0 6px 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-card);
  background: var(--bg);
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

.preview-send {
  display: grid;
  width: 34px;
  height: 34px;
  margin-left: auto;
  place-items: center;
  border-radius: var(--radius-sm);
  color: var(--on-primary);
  background: var(--primary);
}

.preview-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
  margin-top: var(--sp-3);
  padding: 9px 13px;
  border: 1px solid rgba(101, 216, 197, 0.24);
  border-radius: var(--radius);
  background: var(--accent-soft);
  color: var(--accent);
  font-size: var(--fs-12);
}

/* ---------- 数字条 ---------- */
.stats-wrap {
  width: min(var(--container), calc(100% - var(--gutter) * 2));
  margin: 0 auto;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border-bottom: 1px solid var(--line);
}

.stat {
  padding: var(--sp-7) var(--sp-5) var(--sp-7) 0;
  border-right: 1px solid var(--line);
}

.stat:last-child {
  border-right: 0;
}

.stat b {
  display: flex;
  align-items: baseline;
  gap: 2px;
  color: var(--text-strong);
  font-size: var(--fs-28);
  font-weight: 760;
  line-height: 1.1;
}

.stat b i {
  font-style: normal;
  margin-left: 3px;
  color: var(--accent);
  font-size: var(--fs-14);
  font-weight: 700;
}

.stat span {
  display: block;
  margin-top: 6px;
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

/* ---------- 区块 ---------- */
.section {
  border-bottom: 1px solid var(--line);
}

.section--last {
  border-bottom: 0;
}

.section-inner {
  width: min(var(--container), calc(100% - var(--gutter) * 2));
  margin: 0 auto;
  padding: var(--sp-16) 0;
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--sp-10);
  margin-bottom: var(--sp-8);
}

.section-kicker {
  margin: 0 0 7px;
  color: var(--primary-hover);
  font-size: var(--fs-12);
  font-weight: 720;
}

.section-title {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-28);
  font-weight: 720;
  line-height: var(--lh-snug);
}

.section-desc {
  max-width: 26em;
  margin: 0;
  color: var(--muted);
  font-size: var(--fs-14);
  line-height: var(--lh-body);
}

/* ---------- 能力行 ---------- */
.capabilities {
  border-top: 1px solid var(--line);
}

.capability {
  display: grid;
  grid-template-columns: 48px minmax(0, 220px) minmax(0, 1fr) 40px;
  align-items: center;
  gap: var(--sp-5);
  padding: var(--sp-5) var(--sp-3);
  border-bottom: 1px solid var(--line);
  transition: background var(--dur) var(--ease);
}

.capability:hover {
  background: rgba(255, 255, 255, 0.03);
}

.capability__idx {
  color: var(--muted-faint);
  font-family: var(--font-mono);
  font-size: var(--fs-13);
}

.capability__title {
  min-width: 0;
}

.capability__title h3 {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-19);
  font-weight: 700;
}

.capability__title p {
  margin: 3px 0 0;
  color: var(--primary-hover);
  font-size: var(--fs-12);
}

.capability__detail {
  margin: 0;
  color: var(--muted);
  font-size: var(--fs-14);
  line-height: 1.75;
}

.capability__go {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: 50%;
  color: var(--muted-faint);
  background: rgba(255, 255, 255, 0.04);
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease),
    transform var(--dur) var(--ease);
}

.capability:hover .capability__go {
  color: #1b1e1b;
  background: var(--bone);
  transform: translateX(2px);
}

/* ---------- 伴侣卡 ---------- */
.preset-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--sp-4);
}

.preset-card {
  display: flex;
  flex-direction: column;
  padding: var(--sp-4);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
  cursor: pointer;
  transition:
    transform var(--dur-slow) var(--ease),
    border-color var(--dur-slow) var(--ease),
    background var(--dur-slow) var(--ease);
}

.preset-card:hover {
  transform: translateY(-4px);
  border-color: rgba(101, 216, 197, 0.36);
  background: var(--bg-raise);
}

.preset-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
}

.preset-cat {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted-dim);
  font-size: var(--fs-12);
}

.preset-cat svg {
  color: var(--accent);
}

.preset-fav {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  color: var(--muted-faint);
  background: transparent;
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease);
}

.preset-fav:hover {
  color: var(--text);
  background: rgba(255, 255, 255, 0.06);
}

.preset-fav.is-on {
  color: var(--primary);
}

.preset-visual {
  display: grid;
  height: 124px;
  margin-bottom: var(--sp-4);
  place-items: center;
  overflow: hidden;
  border-radius: var(--radius-sm);
}

.preset-avatar {
  display: grid;
  width: 78px;
  height: 78px;
  place-items: center;
  border: 4px solid rgba(255, 255, 255, 0.16);
  border-radius: 50%;
  color: var(--text-strong);
  font-size: var(--fs-28);
  font-weight: 700;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
  transition: transform var(--dur-slow) var(--ease);
}

.preset-card:hover .preset-avatar {
  transform: scale(1.06);
}

.preset-persona {
  margin: 0 0 4px;
  color: var(--accent);
  font-size: var(--fs-12);
  font-weight: 700;
}

.preset-name {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-19);
  font-weight: 720;
}

.preset-desc {
  display: -webkit-box;
  min-height: 44px;
  overflow: hidden;
  margin: 7px 0 0;
  color: var(--muted-dim);
  font-size: var(--fs-13);
  line-height: 1.7;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.preset-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: var(--sp-3);
}

.preset-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-2);
  margin-top: auto;
  padding-top: var(--sp-4);
  border-top: 1px solid var(--line-soft);
}

.preset-intimacy {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.preset-start {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--text);
  font-size: var(--fs-13);
  font-weight: 650;
  white-space: nowrap;
}

.preset-card:hover .preset-start {
  color: var(--accent);
}

/* ---------- 三步 ---------- */
.steps {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-top: 1px solid var(--line);
}

.step {
  padding: var(--sp-6) var(--sp-7) var(--sp-6) 0;
  border-right: 1px solid var(--line);
}

.step:last-child {
  border-right: 0;
  padding-right: 0;
}

.step__num {
  display: inline-grid;
  width: 28px;
  height: 28px;
  margin-bottom: var(--sp-4);
  place-items: center;
  border-radius: 50%;
  color: var(--on-primary);
  background: var(--primary);
  font-size: var(--fs-13);
  font-weight: 700;
}

.step h3 {
  margin: 0 0 6px;
  color: var(--text-strong);
  font-size: var(--fs-16);
  font-weight: 700;
}

.step p {
  max-width: 22em;
  margin: 0;
  color: var(--muted-dim);
  font-size: var(--fs-13);
  line-height: 1.75;
}

/* ---------- CTA ---------- */
.cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-8);
  padding: var(--sp-9);
  border-radius: var(--radius-card);
  background: var(--bone);
}

.cta h2 {
  margin: 0;
  color: #17120f;
  font-size: var(--fs-25);
  font-weight: 760;
  line-height: var(--lh-snug);
}

.cta p {
  margin: 8px 0 0;
  color: #5b5750;
  font-size: var(--fs-14);
}

.cta-actions {
  display: flex;
  flex-shrink: 0;
  gap: var(--sp-3);
}

/* ---------- 页脚 ---------- */
.footer {
  border-top: 1px solid var(--line);
  padding: var(--sp-10) 0 var(--sp-14);
}

.footer-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-6);
  width: min(var(--container), calc(100% - var(--gutter) * 2));
  margin: 0 auto;
}

.footer-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0;
  border: 0;
  color: var(--text-strong);
  background: transparent;
  font-size: var(--fs-16);
  font-weight: 720;
  cursor: pointer;
}

.brand-mark {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 50%;
  color: #17120f;
  background: var(--primary);
}

.brand-mark svg {
  width: 15px;
  height: 15px;
}

.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-6);
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

.footer-links a {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
}

.footer-links a:hover {
  color: var(--text);
}

.footer-note {
  margin: 0;
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

/* ---------- 按钮（本页专用，样式与 tokens 一致） ---------- */
.btn-primary,
.btn-ghost,
.btn-bone,
.btn-sm,
.btn-lg {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  min-height: 44px;
  padding: 0 20px;
  border: 0;
  border-radius: var(--radius);
  font-size: var(--fs-14);
  font-weight: 700;
  white-space: nowrap;
  cursor: pointer;
  transition:
    transform var(--dur) var(--ease),
    background var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.btn-primary {
  color: var(--on-primary);
  background: var(--primary);
  box-shadow: var(--shadow-primary);
}

.btn-primary:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
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

.btn-bone {
  color: #1b1e1b;
  background: var(--bone);
}

.btn-bone:hover {
  background: #f2efe7;
}

.btn-sm {
  min-height: 34px;
  padding: 0 14px;
  font-size: var(--fs-13);
  font-weight: 650;
}

.btn-lg {
  min-height: 50px;
  padding: 0 26px;
  font-size: var(--fs-16);
}

/* ---------- 响应式 ---------- */
@media (max-width: 1080px) {
  .hero-inner {
    grid-template-columns: 1fr;
    gap: var(--sp-10);
  }

  .hero-title {
    max-width: none;
  }

  .preset-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .stats {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat:nth-child(2) {
    border-right: 0;
  }

  .stat:nth-child(1),
  .stat:nth-child(2) {
    border-bottom: 1px solid var(--line);
  }

  .steps {
    grid-template-columns: 1fr;
  }

  .step {
    border-right: 0;
    border-bottom: 1px solid var(--line);
    padding-right: 0;
  }

  .step:last-child {
    border-bottom: 0;
  }

  .capability {
    grid-template-columns: 36px minmax(0, 1fr) 36px;
  }

  .capability__detail {
    display: none;
  }
}

@media (max-width: 760px) {
  .section-inner {
    padding: var(--sp-12) 0;
  }

  .hero-inner {
    padding: var(--sp-12) 0 var(--sp-10);
  }

  .section-head {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--sp-4);
  }

  .preset-grid {
    grid-template-columns: 1fr;
  }

  .cta {
    flex-direction: column;
    align-items: flex-start;
    padding: var(--sp-6);
  }

  .cta-actions {
    width: 100%;
  }

  .cta-actions > * {
    flex: 1;
  }

  .footer-inner {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
