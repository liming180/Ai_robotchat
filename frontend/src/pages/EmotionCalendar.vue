<template>
  <div class="min-h-screen relative overflow-hidden">
    <!-- 背景装饰 -->
    <div class="fixed inset-0 -z-10">
      <div class="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-pink-600/10 to-transparent"></div>
    </div>

    <!-- 顶部导航 -->
    <nav class="sticky top-0 z-50 backdrop-blur-xl bg-slate-900/80 border-b border-white/10">
      <div class="max-w-4xl mx-auto px-6 py-4">
        <div class="flex items-center gap-4">
          <button @click="$router.back()" class="p-2 rounded-xl hover:bg-white/5 transition-colors">
            <svg class="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
            </svg>
          </button>
          <h1 class="text-2xl font-bold text-white">情绪日历</h1>
        </div>
      </div>
    </nav>

    <div class="max-w-4xl mx-auto px-6 py-8 space-y-6">
      <p v-if="error" class="px-4 py-3 rounded-xl border border-amber-500/30 bg-amber-500/10 text-sm text-amber-300" role="alert">
        {{ error }}
      </p>

      <!-- 记录此刻心情（极简：选情绪 + 一句话 + 强度） -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-6">
        <h3 class="text-lg font-semibold text-white mb-4">记录此刻心情</h3>
        <div class="flex flex-wrap gap-2 mb-4">
          <button
            v-for="(meta, type) in emotionMeta"
            :key="type"
            type="button"
            @click="draftEmotion = type"
            class="px-3 py-2 rounded-xl border text-sm transition-all"
            :class="draftEmotion === type
              ? 'border-pink-500/60 bg-pink-500/15 text-white'
              : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10'"
          >
            {{ meta.icon }} {{ meta.label }}
          </button>
        </div>
        <div class="flex flex-col sm:flex-row gap-3">
          <input
            v-model="draftNote"
            placeholder="一句话描述此刻（可选）"
            maxlength="200"
            class="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:border-pink-500/40"
            @keydown.enter.prevent="submitMood"
          />
          <div class="flex items-center gap-2 text-sm text-slate-400">
            <span>强度</span>
            <input v-model.number="draftIntensity" type="range" min="10" max="100" step="10" class="w-28 accent-pink-500" />
            <span class="w-9 text-right text-slate-300">{{ draftIntensity }}%</span>
          </div>
          <button
            type="button"
            @click="submitMood"
            :disabled="saving"
            class="px-5 py-2 bg-gradient-to-r from-pink-500 to-purple-600 rounded-xl text-white font-medium hover:from-pink-400 hover:to-purple-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ saving ? '记录中...' : '记录' }}
          </button>
        </div>
        <p v-if="saveError" class="mt-3 text-sm text-red-300" role="alert">{{ saveError }}</p>
      </div>

      <!-- 统计卡片 -->
      <div class="grid grid-cols-3 gap-4">
        <div class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 text-center hover:border-pink-500/30 transition-all">
          <div class="text-3xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
            {{ emotionStats.total }}
          </div>
          <div class="text-slate-400 text-sm mt-2">总记录</div>
        </div>
        <div class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 text-center hover:border-pink-500/30 transition-all">
          <div class="text-3xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
            {{ emotionStats.total ? emotionMeta[emotionStats.dominant].label : '—' }}
          </div>
          <div class="text-slate-400 text-sm mt-2">主导情绪</div>
        </div>
        <div class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 text-center hover:border-pink-500/30 transition-all">
          <div class="text-3xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
            {{ recordedKinds }}
          </div>
          <div class="text-slate-400 text-sm mt-2">情绪种类</div>
        </div>
      </div>

      <!-- 日历网格 -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-6">
        <h3 class="text-lg font-semibold text-white mb-4">{{ year }}年{{ month + 1 }}月</h3>
        <div class="grid grid-cols-7 gap-2">
          <!-- 星期标题 -->
          <div v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day"
               class="text-center text-xs font-medium text-slate-400 py-2">
            {{ day }}
          </div>
          <!-- 日期格子 -->
          <div v-for="(day, idx) in calendarDays" :key="`${idx}-${day.date || 'blank'}`"
               class="aspect-square rounded-xl border border-white/10 flex items-center justify-center transition-all"
               :class="[
                 day.emotion === 'happy' ? 'bg-gradient-to-br from-amber-500/20 to-yellow-500/20' :
                 day.emotion === 'sad' ? 'bg-gradient-to-br from-blue-500/20 to-indigo-500/20' :
                 day.emotion === 'angry' ? 'bg-gradient-to-br from-red-500/20 to-rose-500/20' :
                 day.emotion === 'anxious' ? 'bg-gradient-to-br from-purple-500/20 to-violet-500/20' :
                 'bg-slate-800/20',
                 day.hasRecord ? 'border-white/20' : 'border-transparent'
               ]">
            <div v-if="day.day" class="text-center">
              <div class="text-sm font-medium text-white">{{ day.day }}</div>
              <div v-if="day.emotion" class="text-xs mt-1">
                {{ emotionMeta[day.emotion].icon }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近情绪记录 -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-6">
        <h3 class="text-lg font-semibold text-white mb-4">最近情绪记录</h3>
        <div v-if="emotionHistory.length" class="space-y-3">
          <div v-for="record in emotionHistory.slice(0, 5)" :key="record.id"
               class="flex items-center gap-3 p-3 rounded-xl bg-white/5">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center"
                 :class="`bg-gradient-to-br ${emotionMeta[record.emotion].color} text-white`">
              {{ emotionMeta[record.emotion].icon }}
            </div>
            <div class="flex-1">
              <div class="text-sm text-white">{{ record.content || emotionMeta[record.emotion].label }}</div>
              <div class="text-xs text-slate-400 mt-1">
                {{ formatDate(record.timestamp) }} · 强度 {{ record.intensity }}%
              </div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-slate-500">
          <svg class="w-16 h-16 mx-auto mb-3 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          <p>暂无情绪记录，在上方记录一条试试</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
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

const emotionStats = computed(() => getEmotionStats())
const recordedKinds = computed(() =>
  Object.values(emotionStats.value.distribution).filter(count => count > 0).length
)

// 日历固定展示当前年月（原版硬编码 2026年7月，与真实记录永远对不上）
const now = new Date()
const year = now.getFullYear()
const month = now.getMonth()

// ── 极简记录入口 ──
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
  } catch (e) {
    saveError.value = `记录失败：${(e as Error).message}`
  } finally {
    saving.value = false
  }
}

// 生成日历数据
const calendarDays = computed(() => {
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const daysInMonth = lastDay.getDate()
  const startDayOfWeek = firstDay.getDay()

  const calendar: any[] = []
  for (let i = 0; i < startDayOfWeek; i++) {
    calendar.push({ day: '', hasRecord: false })
  }

  const calendarData = getEmotionCalendarData(year, month)
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    calendar.push({
      day,
      date: dateStr,
      emotion: calendarData[dateStr],
      hasRecord: !!calendarData[dateStr],
    })
  }
  return calendar
})

const formatDate = (date: Date) => {
  const diff = Date.now() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric' })
}

onMounted(() => {
  // 拉最近 30 天，覆盖整月日历的需求
  load(30)
})
</script>
