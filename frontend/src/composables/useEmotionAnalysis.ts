import { computed } from 'vue'
import { useEmotionStore } from '@/stores/emotion'
import type { EmotionType, EmotionRecord } from '@/types'

// 各情绪对应的共情建议文案
const SUGGESTIONS: Record<EmotionType, string[]> = {
  happy: ['继续分享你的快乐吧！', '有什么开心的事情，我想多听听 ✨', '你的好心情也感染到我了～'],
  sad: ['我理解你的感受，慢慢说，我在这里 💙', '需要聊些什么来缓解心情吗？', '抱抱你，一切都会好起来的'],
  angry: ['深呼吸，先冷静一下', '有什么让你不开心的事情，说出来会好些', '我陪着你，不急，慢慢来'],
  anxious: ['别担心，一切都会好起来的', '想聊聊让你焦虑的事情吗？', '试着放慢呼吸，我就在身边'],
  neutral: ['今天过得怎么样？', '有什么想分享的吗？', '我在这里，随时陪你聊聊'],
}

export function useEmotionAnalysis() {
  const emotionStore = useEmotionStore()

  const currentEmotion = computed(() => emotionStore.currentEmotion)
  const emotionHistory = computed<EmotionRecord[]>(() => emotionStore.records)
  const emotionSuggestions = computed<string[]>(() => SUGGESTIONS[emotionStore.currentEmotion])

  const analyzeEmotion = (text: string) => {
    const { emotion, intensity } = emotionStore.analyzeText(text)
    emotionStore.recordEmotion(emotion, intensity, text)
    return emotion
  }

  const getEmotionSuggestions = (emotion: EmotionType) => SUGGESTIONS[emotion] || []

  const getEmotionCalendarData = (year: number, month: number) =>
    emotionStore.getCalendarData(year, month)

  const getEmotionStats = () => emotionStore.getStats()

  return {
    currentEmotion,
    emotionHistory,
    emotionSuggestions,
    emotionMeta: emotionStore.emotionMeta,
    analyzeEmotion,
    getEmotionSuggestions,
    getEmotionCalendarData,
    getEmotionStats,
  }
}
