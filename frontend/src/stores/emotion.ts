import { defineStore } from 'pinia'
import { ref, onMounted, watch } from 'vue'
import type { EmotionType, EmotionRecord, EmotionStats } from '@/types'
import { isQuotaExceededError } from '@/lib/avatar'

const STORAGE_KEY = 'ai-emotion-records'

// 情绪关键词词典（客户端启发式分析，便于将来替换为后端接口）
const EMOTION_KEYWORDS: Record<EmotionType, string[]> = {
  happy: ['开心', '高兴', '快乐', '幸福', '兴奋', '嘻嘻', '哈哈', '好耶', '棒', '太好了', '喜欢', '😄', '😊', '😍', '🥰', '❤'],
  sad: ['难过', '伤心', '悲伤', '郁闷', '失落', '心痛', '难受', '想哭', '哭', '孤独', '😢', '😭', '💔'],
  angry: ['生气', '愤怒', '气死', '烦死', '讨厌', '烦躁', '可恶', '抓狂', '😠', '😡', '怒'],
  anxious: ['焦虑', '紧张', '担心', '害怕', '不安', '压力', '焦急', '恐惧', '心慌', '😰', '😨'],
  neutral: [],
}

const EMOTION_META: Record<EmotionType, { label: string; icon: string; color: string }> = {
  happy: { label: '快乐', icon: '😊', color: 'from-amber-400 to-yellow-500' },
  sad: { label: '悲伤', icon: '😢', color: 'from-blue-400 to-indigo-500' },
  angry: { label: '愤怒', icon: '😠', color: 'from-red-400 to-rose-500' },
  anxious: { label: '焦虑', icon: '😰', color: 'from-purple-400 to-violet-500' },
  neutral: { label: '平静', icon: '😐', color: 'from-slate-400 to-slate-500' },
}

const serialize = (r: EmotionRecord) => ({ ...r, timestamp: r.timestamp.toISOString() })
const deserialize = (d: any): EmotionRecord => ({ ...d, timestamp: new Date(d.timestamp) })

export const useEmotionStore = defineStore('emotion', () => {
  const records = ref<EmotionRecord[]>([])
  const currentEmotion = ref<EmotionType>('neutral')
  const persistError = ref<string>('')

  onMounted(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        records.value = JSON.parse(saved).map(deserialize)
      } catch (error) {
        console.error('Failed to load emotion records:', error)
      }
    }
  })

  watch(records, (newVal) => {
    try {
      persistError.value = ''
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newVal.map(serialize)))
    } catch (error) {
      if (isQuotaExceededError(error)) {
        persistError.value = '本地存储空间不足，情绪记录保存失败。请清理部分数据后重试。'
      } else {
        persistError.value = '情绪记录保存失败，请稍后重试。'
      }
      console.error('Failed to save emotion records:', error)
    }
  }, { deep: true })

  // 客户端关键词启发式情绪分析
  const analyzeText = (text: string): { emotion: EmotionType; intensity: number } => {
    const lower = text.toLowerCase()
    const scores: Record<EmotionType, number> = { happy: 0, sad: 0, angry: 0, anxious: 0, neutral: 0 }

    for (const emotion of Object.keys(EMOTION_KEYWORDS) as EmotionType[]) {
      for (const kw of EMOTION_KEYWORDS[emotion]) {
        if (lower.includes(kw.toLowerCase())) scores[emotion] += 1
      }
    }
    // 感叹号增强情绪强度
    const exclamations = (text.match(/!/g) || []).length
    if (exclamations) scores.neutral += 0

    let best: EmotionType = 'neutral'
    let bestScore = 0
    for (const emotion of Object.keys(scores) as EmotionType[]) {
      if (scores[emotion] > bestScore) {
        bestScore = scores[emotion]
        best = emotion
      }
    }

    const intensity = best === 'neutral'
      ? 30
      : Math.min(100, 50 + bestScore * 15 + exclamations * 5)
    return { emotion: best, intensity }
  }

  const recordEmotion = (emotion: EmotionType, intensity: number, content: string) => {
    records.value.unshift({
      id: Date.now().toString(),
      emotion,
      intensity,
      content: content.slice(0, 200),
      timestamp: new Date(),
    })
    currentEmotion.value = emotion
  }

  // 分析并记录一条情绪
  const analyzeAndRecord = (text: string) => {
    const { emotion, intensity } = analyzeText(text)
    recordEmotion(emotion, intensity, text)
    return emotion
  }

  // 按天聚合：返回 { 'YYYY-MM-DD': 主导情绪 }
  const getCalendarData = (year: number, month: number): Record<string, EmotionType> => {
    const monthRecords = records.value.filter(r => {
      const d = r.timestamp
      return d.getFullYear() === year && d.getMonth() === month
    })
    // 按天聚合情绪频次
    const dayMap: Record<string, Record<EmotionType, number>> = {}
    for (const record of monthRecords) {
      const key = record.timestamp.toISOString().slice(0, 10)
      if (!dayMap[key]) dayMap[key] = { happy: 0, sad: 0, angry: 0, anxious: 0, neutral: 0 }
      dayMap[key][record.emotion] += 1
    }
    const result: Record<string, EmotionType> = {}
    for (const [day, counts] of Object.entries(dayMap)) {
      let best: EmotionType = 'neutral'
      let bestCount = -1
      for (const emotion of Object.keys(counts) as EmotionType[]) {
        if (counts[emotion] > bestCount) {
          bestCount = counts[emotion]
          best = emotion
        }
      }
      result[day] = best
    }
    return result
  }

  const getStats = (): EmotionStats => {
    const distribution: Record<EmotionType, number> = { happy: 0, sad: 0, angry: 0, anxious: 0, neutral: 0 }
    for (const record of records.value) {
      distribution[record.emotion] += 1
    }
    let dominant: EmotionType = 'neutral'
    let dominantCount = -1
    for (const emotion of Object.keys(distribution) as EmotionType[]) {
      if (distribution[emotion] > dominantCount) {
        dominantCount = distribution[emotion]
        dominant = emotion
      }
    }
    return { total: records.value.length, dominant, distribution }
  }

  const deleteRecord = (id: string) => {
    records.value = records.value.filter(r => r.id !== id)
  }

  return {
    records,
    currentEmotion,
    persistError,
    emotionMeta: EMOTION_META,
    analyzeText,
    recordEmotion,
    analyzeAndRecord,
    getCalendarData,
    getStats,
    deleteRecord,
  }
})
