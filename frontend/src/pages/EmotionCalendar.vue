<template>
  <div class="calendar">
    <Navbar />

    <main class="calendar-main">
      <header class="page-head">
        <div>
          <p class="eyebrow">
            <CalendarHeart :size="15" />
            EMOTION CALENDAR
          </p>
          <h1 class="page-title">情绪日历</h1>
          <p class="page-lead">
            每天记一笔，久了就能看见自己的节奏。伴侣的回应也会参考这里的记录。
          </p>
        </div>
        <p class="page-count">{{ year }} 年 {{ month + 1 }} 月</p>
      </header>

      <div v-if="error" class="alert" role="alert">
        <AlertCircle :size="15" />
        {{ error }}
      </div>

      <div class="summary">
        <div class="summary__item">
          <span>本月记录</span>
          <strong>
            <AnimatedNumber :value="emotionStats.total" />
            <i>天</i>
          </strong>
        </div>
        <div class="summary__item">
          <span>主导情绪</span>
          <strong>
            {{ loading || !emotionStats.total ? '—' : emotionMeta[emotionStats.dominant]?.label }}
          </strong>
        </div>
        <div class="summary__item">
          <span>情绪种类</span>
          <strong>
            <AnimatedNumber :value="recordedKinds" />
            <i>种</i>
          </strong>
        </div>
      </div>

      <div class="calendar-grid">
        <div class="calendar-main-col">
          <div class="cal-card">
            <div class="cal-card__head">
              <h2>{{ year }} 年 {{ month + 1 }} 月</h2>
              <div class="cal-card__nav">
                <button type="button" aria-label="上个月" disabled>
                  <ChevronLeft :size="15" />
                </button>
                <button type="button" aria-label="下个月" disabled>
                  <ChevronRight :size="15" />
                </button>
              </div>
            </div>

            <div class="cal">
              <div class="cal__weekdays">
                <span v-for="day in weekdays" :key="day">{{ day }}</span>
              </div>

              <div class="cal__days">
                <div
                  v-for="(cell, idx) in calendarDays"
                  :key="idx"
                  class="cal__day"
                  :class="{
                    'is-blank': !cell.day,
                    'has-record': cell.hasRecord,
                    'is-today': cell.day === today,
                  }"
                >
                  <span v-if="cell.day" class="cal__num">{{ cell.day }}</span>
                  <span
                    v-if="cell.hasRecord && cell.emotion"
                    class="cal__mark"
                    :style="{ background: emotionColor(cell.emotion) }"
                  />
                </div>
              </div>
            </div>

            <div class="cal-legend">
              <span v-for="(meta, type) in emotionMeta" :key="type">
                <i :style="{ background: emotionColor(type as EmotionType) }" />
                {{ meta.label }}
              </span>
            </div>
          </div>

          <section class="record-card">
            <h2>记录此刻心情</h2>

            <div class="record-emotions">
              <button
                v-for="(meta, type) in emotionMeta"
                :key="type"
                type="button"
                class="record-emotion"
                :class="{ 'is-active': draftEmotion === type }"
                @click="draftEmotion = type as EmotionType"
              >
                <i :style="{ background: emotionColor(type as EmotionType) }" />
                {{ meta.label }}
              </button>
            </div>

            <div class="record-inputs">
              <input
                v-model="draftNote"
                class="input"
                type="text"
                placeholder="一句话描述此刻（可选）"
                maxlength="200"
                @keydown.enter.prevent="submitMood"
              />

              <label class="record-intensity">
                强度
                <input
                  v-model.number="draftIntensity"
                  type="range"
                  min="1"
                  max="100"
                  step="1"
                />
                <b>{{ draftIntensity }}%</b>
              </label>

              <button
                type="button"
                class="btn btn-primary"
                :disabled="saving"
                @click="submitMood"
              >
                {{ saving ? '记录中…' : '记录' }}
              </button>
            </div>

            <p v-if="saveError" class="record-error" role="alert">{{ saveError }}</p>

            <div class="record-foot">
              <span class="small">记录之后会同步给伴侣，它下次会主动问起这件事。</span>
            </div>
          </section>
        </div>

        <aside class="calendar-aside">
          <section class="side-card">
            <h2>本月分布</h2>
            <div class="dist">
              <div v-for="(meta, type) in emotionMeta" :key="type" class="dist__row">
                <span>{{ meta.label }}</span>
                <div class="dist__track">
                  <i
                    :style="{
                      width: `${distPercent(type as EmotionType)}%`,
                      background: emotionColor(type as EmotionType),
                    }"
                  />
                </div>
                <b>{{ emotionStats.distribution[type as EmotionType] || 0 }}</b>
              </div>
            </div>
          </section>

          <section class="side-card">
            <h2>最近记录</h2>

            <div v-if="recentRecords.length" class="recent">
              <div v-for="record in recentRecords" :key="record.id" class="recent__item">
                <span class="recent__date">{{ shortDate(record.timestamp) }}</span>
                <div class="recent__copy">
                  <span class="recent__type">
                    <i :style="{ background: emotionColor(record.emotion) }" />
                    {{ emotionMeta[record.emotion]?.label }} {{ record.intensity }}%
                  </span>
                  <p v-if="record.content" class="recent__note">{{ record.content }}</p>
                </div>
              </div>
            </div>

            <p v-else class="side-empty">还没有记录，从左边记一笔开始。</p>

            <router-link class="side-link" to="/history">看看那几天的对话 →</router-link>
          </section>

          <section class="side-card">
            <h2>怎么用</h2>
            <p>不需要每天记。真正起伏的那几天记一笔，反而更有用——伴侣能据此调整语气。</p>
            <p>记录内容只有你自己能看到。</p>
          </section>
        </aside>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { AlertCircle, CalendarHeart, ChevronLeft, ChevronRight } from 'lucide-vue-next'
import Navbar from '@/components/Navbar.vue'
import AnimatedNumber from '@/components/ui/AnimatedNumber.vue'
import { useToast } from '@/composables/useToast'
import { useEmotionAnalysis } from '@/composables/useEmotionAnalysis'
import type { EmotionType } from '@/types'

const {
  emotionHistory,
  emotionMeta,
  getEmotionCalendarData,
  getEmotionStats,
  load,
  recordEmotion,
  error,
} = useEmotionAnalysis()

const toast = useToast()
const loading = ref(true)

const emotionStats = computed(() => getEmotionStats())
const recordedKinds = computed(
  () => Object.values(emotionStats.value.distribution).filter((count) => count > 0).length,
)

const EMOTION_COLORS: Record<EmotionType, string> = {
  happy: '#c9a227',
  sad: '#5b7fb3',
  angry: '#b0564e',
  anxious: '#8a6fa8',
  neutral: '#a1a1a8',
}

const emotionColor = (type: EmotionType) => EMOTION_COLORS[type] || EMOTION_COLORS.neutral

const now = new Date()
const year = now.getFullYear()
const month = now.getMonth()
const today = now.getDate()

const weekdays = ['一', '二', '三', '四', '五', '六', '日']

const recentRecords = computed(() =>
  [...emotionHistory.value]
    .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
    .slice(0, 5),
)

const distPercent = (type: EmotionType) => {
  const values = Object.values(emotionStats.value.distribution) as number[]
  const max = Math.max(...values, 1)
  const current = emotionStats.value.distribution[type] || 0
  return Math.round((current / max) * 100)
}

const draftEmotion = ref<EmotionType>('happy')
const draftIntensity = ref(60)
const draftNote = ref('')
const saving = ref(false)
const saveError = ref('')

const submitMood = async () => {
  if (saving.value) return
  saving.value = true
  saveError.value = ''
  try {
    await recordEmotion(draftEmotion.value, draftIntensity.value, draftNote.value.trim())
    draftNote.value = ''
    toast.success('心情已记录')
  } catch (e) {
    saveError.value = `记录失败：${(e as Error).message}`
    toast.error('记录失败，请重试')
  } finally {
    saving.value = false
  }
}

const calendarDays = computed(() => {
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const daysInMonth = lastDay.getDate()
  const startOffset = (firstDay.getDay() + 6) % 7

  const calendar: {
    day: number | ''
    date?: string
    emotion?: EmotionType
    hasRecord: boolean
  }[] = []

  for (let i = 0; i < startOffset; i += 1) {
    calendar.push({ day: '', hasRecord: false })
  }

  const calendarData = getEmotionCalendarData(year, month)
  for (let day = 1; day <= daysInMonth; day += 1) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    calendar.push({
      day,
      date: dateStr,
      emotion: calendarData[dateStr] as EmotionType | undefined,
      hasRecord: Boolean(calendarData[dateStr]),
    })
  }

  while (calendar.length % 7 !== 0) {
    calendar.push({ day: '', hasRecord: false })
  }

  return calendar
})

const shortDate = (date: Date) => {
  const d = new Date(date)
  return `${d.getMonth() + 1}-${String(d.getDate()).padStart(2, '0')}`
}

onMounted(async () => {
  loading.value = true
  try {
    await load(30)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.calendar {
  min-height: 100vh;
}

.calendar-main {
  width: min(1100px, calc(100% - var(--gutter) * 2));
  margin: 0 auto;
  padding: var(--sp-14) 0 var(--sp-24);
}

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
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--sp-8);
  padding-bottom: var(--sp-8);
}

.page-title {
  margin: 0;
  color: var(--text-strong);
  font-size: clamp(30px, 4vw, var(--fs-34));
  font-weight: 760;
  line-height: var(--lh-tight);
}

.page-lead {
  margin: var(--sp-3) 0 0;
  max-width: 34em;
  color: var(--muted);
  font-size: var(--fs-14);
  line-height: var(--lh-body);
}

.page-count {
  margin: 0;
  flex-shrink: 0;
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

.summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  margin-bottom: var(--sp-6);
}

.summary__item {
  padding: var(--sp-5) var(--sp-5) var(--sp-5) 0;
  border-right: 1px solid var(--line);
}

.summary__item:last-child {
  border-right: 0;
}

.summary__item span {
  display: block;
  color: var(--muted);
  font-size: var(--fs-13);
}

.summary__item strong {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-top: 6px;
  color: var(--text-strong);
  font-size: var(--fs-28);
  font-weight: 760;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}

.summary__item strong i {
  font-style: normal;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  font-weight: 400;
}

.calendar-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: var(--sp-6);
  align-items: start;
}

.calendar-main-col {
  min-width: 0;
}

.cal-card {
  overflow: hidden;
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

.cal-card__head {
  display: flex;
  align-items: center;
  gap: var(--sp-3);
  padding: var(--sp-4) var(--sp-5);
  border-bottom: 1px solid var(--line);
}

.cal-card__head h2 {
  margin: 0;
  color: var(--text-strong);
  font-size: var(--fs-16);
  font-weight: 700;
}

.cal-card__nav {
  display: flex;
  gap: 2px;
  margin-left: auto;
}

.cal-card__nav button {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: transparent;
}

.cal-card__nav button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.cal {
  padding: var(--sp-4) var(--sp-5) var(--sp-5);
}

.cal__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  margin-bottom: 6px;
}

.cal__weekdays span {
  padding: 4px 0;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  text-align: center;
}

.cal__days {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.cal__day {
  position: relative;
  display: flex;
  min-height: 58px;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  padding: 7px 0 5px;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text);
  font-size: var(--fs-13);
  font-variant-numeric: tabular-nums;
  transition: background var(--dur) var(--ease);
}

.cal__day:hover:not(.is-blank) {
  background: rgba(255, 255, 255, 0.04);
}

.cal__day.is-blank {
  pointer-events: none;
}

.cal__day.has-record {
  border-color: var(--line);
}

.cal__day.is-today {
  border-color: var(--accent-line);
  color: var(--accent);
  font-weight: 700;
}

.cal__num {
  line-height: 1;
}

.cal__mark {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.cal-legend {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-5) var(--sp-4);
  border-top: 1px solid var(--line);
  background: var(--bg);
  color: var(--muted);
  font-size: var(--fs-12);
}

.cal-legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.cal-legend i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.record-card {
  margin-top: var(--sp-4);
  padding: var(--sp-5);
  border: 1px solid var(--line);
  border-radius: var(--radius-card);
  background: var(--bg-soft);
}

.record-card h2 {
  margin: 0 0 var(--sp-4);
  color: var(--text-strong);
  font-size: var(--fs-16);
  font-weight: 700;
}

.record-emotions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2);
  margin-bottom: var(--sp-4);
}

.record-emotion {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  height: 36px;
  padding: 0 14px;
  border: 1px solid var(--line);
  border-radius: var(--radius-sm);
  color: var(--muted);
  background: transparent;
  font-size: var(--fs-13);
  cursor: pointer;
  transition:
    color var(--dur) var(--ease),
    background var(--dur) var(--ease),
    border-color var(--dur) var(--ease);
}

.record-emotion i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.record-emotion:hover {
  color: var(--text-strong);
  border-color: var(--line-strong);
}

.record-emotion.is-active {
  border-color: var(--bone);
  color: #171917;
  background: var(--bone);
  font-weight: 700;
}

.record-inputs {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--sp-3);
}

.input {
  flex: 1 1 240px;
  min-height: 42px;
  padding: 10px 14px;
  border: 1px solid rgba(255, 255, 255, 0.11);
  border-radius: var(--radius-card);
  color: var(--text);
  background: var(--bg);
  font-size: var(--fs-13);
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

.record-intensity {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  color: var(--muted);
  font-size: var(--fs-13);
  white-space: nowrap;
}

input[type='range'] {
  width: 108px;
  height: 24px;
  accent-color: var(--primary);
}

.record-intensity b {
  width: 38px;
  color: var(--text);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.record-error {
  margin: var(--sp-3) 0 0;
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

.record-foot {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  margin-top: var(--sp-4);
  padding-top: var(--sp-3);
  border-top: 1px solid var(--line);
}

.small {
  color: var(--muted-faint);
  font-size: var(--fs-12);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 42px;
  padding: 0 18px;
  border: 0;
  border-radius: var(--radius);
  font-size: var(--fs-13);
  font-weight: 650;
  white-space: nowrap;
  cursor: pointer;
  transition:
    background var(--dur) var(--ease),
    opacity var(--dur) var(--ease);
}

.btn-primary {
  color: var(--on-primary);
  background: var(--primary);
  box-shadow: var(--shadow-primary);
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

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

.side-card p {
  margin: 0;
  color: var(--muted);
  font-size: var(--fs-13);
  line-height: 1.7;
}

.side-card p + p {
  margin-top: var(--sp-3);
}

.dist {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.dist__row {
  display: grid;
  grid-template-columns: 52px 1fr 24px;
  align-items: center;
  gap: var(--sp-3);
  color: var(--muted);
  font-size: var(--fs-12);
}

.dist__track {
  height: 4px;
  overflow: hidden;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.08);
}

.dist__track i {
  display: block;
  height: 100%;
  border-radius: 2px;
  transition: width var(--dur-slow) var(--ease);
}

.dist__row b {
  color: var(--text);
  font-size: var(--fs-12);
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.recent {
  display: flex;
  flex-direction: column;
}

.recent__item {
  display: flex;
  gap: var(--sp-3);
  padding: var(--sp-3) 0;
  border-bottom: 1px solid var(--line);
}

.recent__item:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.recent__date {
  flex-shrink: 0;
  padding-top: 2px;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  font-variant-numeric: tabular-nums;
}

.recent__copy {
  min-width: 0;
}

.recent__type {
  display: flex;
  align-items: center;
  gap: 5px;
  color: var(--text);
  font-size: var(--fs-13);
}

.recent__type i {
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  border-radius: 50%;
}

.recent__note {
  display: -webkit-box;
  overflow: hidden;
  margin: 2px 0 0;
  color: var(--muted-faint);
  font-size: var(--fs-12);
  line-height: 1.6;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.side-empty {
  margin: 0;
  color: var(--muted-faint);
  font-size: var(--fs-13);
}

.side-link {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  margin-top: var(--sp-4);
  color: var(--accent);
  font-size: var(--fs-13);
}

.side-link:hover {
  text-decoration: underline;
}

.alert {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--sp-4);
  padding: 11px 14px;
  border: 1px solid var(--primary-line);
  border-radius: var(--radius);
  background: var(--danger-soft);
  color: var(--primary-hover);
  font-size: var(--fs-13);
}

@media (max-width: 1024px) {
  .calendar-grid {
    grid-template-columns: 1fr;
  }

  .page-head {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--sp-3);
  }
}

@media (max-width: 760px) {
  .calendar-main {
    padding: var(--sp-10) 0 var(--sp-16);
  }

  .summary {
    grid-template-columns: 1fr;
  }

  .summary__item {
    border-right: 0;
    border-bottom: 1px solid var(--line);
    padding: var(--sp-4) 0;
  }

  .summary__item:last-child {
    border-bottom: 0;
  }

  .cal__day {
    min-height: 50px;
    font-size: var(--fs-12);
  }

  .record-inputs .btn {
    width: 100%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .dist__track i {
    transition: none;
  }
}
</style>
