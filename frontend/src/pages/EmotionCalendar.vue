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
            {{ emotionStats.dominant }}
          </div>
          <div class="text-slate-400 text-sm mt-2">主导情绪</div>
        </div>
        <div class="bg-white/5 backdrop-blur-xl rounded-2xl border border-white/10 p-6 text-center hover:border-pink-500/30 transition-all">
          <div class="text-3xl font-bold bg-gradient-to-r from-pink-400 to-purple-400 bg-clip-text text-transparent">
            {{ Object.entries(emotionStats.distribution).length }}
          </div>
          <div class="text-slate-400 text-sm mt-2">情绪种类</div>
        </div>
      </div>

      <!-- 日历网格 -->
      <div class="bg-white/5 backdrop-blur-xl rounded-3xl border border-white/10 p-6">
        <h3 class="text-lg font-semibold text-white mb-4">2026年7月</h3>
        <div class="grid grid-cols-7 gap-2">
          <!-- 星期标题 -->
          <div v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day"
               class="text-center text-xs font-medium text-slate-400 py-2">
            {{ day }}
          </div>
          <!-- 日期格子 -->
          <div v-for="day in calendarDays" :key="day.date"
               class="aspect-square rounded-xl border border-white/10 flex items-center justify-center cursor-pointer hover:bg-white/5 transition-all"
               :class="[
                 day.emotion === 'happy' ? 'bg-gradient-to-br from-amber-500/20 to-yellow-500/20' :
                 day.emotion === 'sad' ? 'bg-gradient-to-br from-blue-500/20 to-indigo-500/20' :
                 day.emotion === 'angry' ? 'bg-gradient-to-br from-red-500/20 to-rose-500/20' :
                 day.emotion === 'anxious' ? 'bg-gradient-to-br from-purple-500/20 to-violet-500/20' :
                 'bg-slate-800/20',
                 day.hasRecord ? 'border-white/20' : 'border-transparent'
               ]">
            <div class="text-center">
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
              <div class="text-sm text-white">{{ record.content }}</div>
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
          <p>暂无情绪记录</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useEmotionAnalysis } from '@/composables/useEmotionAnalysis'
import { createSvgAvatarDataUrl } from '@/lib/avatar'

const router = useRouter()
const { emotionHistory, emotionMeta, getEmotionCalendarData, getEmotionStats } = useEmotionAnalysis()
const emotionStats = computed(() => getEmotionStats())

// 生成日历数据
const calendarDays = computed(() => {
  const year = 2026
  const month = 6 // 0-indexed
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const daysInMonth = lastDay.getDate()
  const startDayOfWeek = firstDay.getDay()

  const calendar: any[] = []

  // 添加空白天
  for (let i = 0; i < startDayOfWeek; i++) {
    calendar.push({ day: '', hasRecord: false })
  }

  // 添加日期
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
  // 初始化时加载日历数据
  getEmotionCalendarData(2026, 6)
})
</script>