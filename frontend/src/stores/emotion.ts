import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { EmotionType, EmotionRecord, EmotionStats } from '@/types'
import { aiFetch } from '@/lib/api'
import { useUserStore } from '@/stores/user'

/**
 * 情绪数据归属 = Python AI 服务（SQLite `user_moods`，P0-6 决策）。
 * Python 侧字段是自由文本：mood(中文/英文) + score(1-10) + note，
 * 前端内部统一用 EmotionType + intensity(0-100)，边界处做映射。
 */

const CACHE_KEY = 'ai-emotion-records'

const EMOTION_META: Record<EmotionType, { label: string; icon: string; color: string }> = {
  happy: { label: '快乐', icon: '😊', color: 'from-amber-400 to-yellow-500' },
  sad: { label: '悲伤', icon: '😢', color: 'from-blue-400 to-indigo-500' },
  angry: { label: '愤怒', icon: '😠', color: 'from-red-400 to-rose-500' },
  anxious: { label: '焦虑', icon: '😰', color: 'from-purple-400 to-violet-500' },
  neutral: { label: '平静', icon: '😐', color: 'from-slate-400 to-slate-500' },
}

const EMOTION_LABELS: Record<EmotionType, string> = {
  happy: '开心',
  sad: '难过',
  angry: '生气',
  anxious: '焦虑',
  neutral: '平静',
}

/** Python 里可能是中文（示例数据风格）也可能是英文（模型注释风格），双向兜住 */
const MOOD_ALIASES: Record<string, EmotionType> = {
  happy: 'happy', 开心: 'happy', 快乐: 'happy', 兴奋: 'happy', good: 'happy',
  sad: 'sad', 难过: 'sad', 悲伤: 'sad', 失落: 'sad', tired: 'sad', 疲惫: 'sad',
  angry: 'angry', 生气: 'angry', 愤怒: 'angry', 烦躁: 'angry',
  anxious: 'anxious', 焦虑: 'anxious', 紧张: 'anxious', 担心: 'anxious',
  neutral: 'neutral', calm: 'neutral', 平静: 'neutral', ok: 'neutral', normal: 'neutral',
}

const toEmotionType = (mood?: string | null): EmotionType => {
  const key = (mood || '').trim().toLowerCase()
  return MOOD_ALIASES[key] ?? MOOD_ALIASES[(mood || '').trim()] ?? 'neutral'
}

/** Python `GET /api/v1/mood/{userId}` 的单条结构 */
interface MoodDto {
  id: string | number
  userId: string
  mood?: string | null
  score?: number | null
  note?: string | null
  createdAt?: string | null
}

const toRecord = (dto: MoodDto): EmotionRecord => {
  const score = typeof dto.score === 'number' ? dto.score : 5
  return {
    id: String(dto.id),
    emotion: toEmotionType(dto.mood),
    // score 是 1-10，前端强度按 0-100 展示
    intensity: Math.max(0, Math.min(100, Math.round(score * 10))),
    content: dto.note || '',
    timestamp: dto.createdAt ? new Date(dto.createdAt) : new Date(),
  }
}

export const useEmotionStore = defineStore('emotion', () => {
  const records = ref<EmotionRecord[]>([])
  const currentEmotion = ref<EmotionType>('neutral')
  const loading = ref(false)
  const error = ref('')
  const fromCache = ref(false)

  const readCache = (): EmotionRecord[] => {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return []
    try {
      const list = JSON.parse(raw)
      return Array.isArray(list)
        ? list.map((r: any) => ({
            id: String(r.id),
            emotion: (r.emotion as EmotionType) || 'neutral',
            intensity: Number(r.intensity) || 0,
            content: r.content || '',
            timestamp: new Date(r.timestamp ?? Date.now()),
          }))
        : []
    } catch {
      localStorage.removeItem(CACHE_KEY)
      return []
    }
  }

  const writeCache = () => {
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(records.value.map(r => ({
        ...r,
        timestamp: r.timestamp.toISOString(),
      }))))
    } catch {
      // 缓存失败不影响主流程
    }
  }

  async function loadMoods(days = 30): Promise<void> {
    const userId = useUserStore().userId
    if (!userId) {
      records.value = []
      return
    }

    loading.value = true
    try {
      const data = await aiFetch<{ moods?: MoodDto[] }>(`/api/v1/mood/${userId}?days=${days}`)
      records.value = (data?.moods || []).map(toRecord)
      currentEmotion.value = records.value[0]?.emotion ?? 'neutral'
      error.value = ''
      fromCache.value = false
      writeCache()
    } catch (e) {
      const cached = readCache()
      if (cached.length) {
        records.value = cached
        fromCache.value = true
        error.value = `情绪记录加载失败，正在显示本地缓存：${(e as Error).message}`
      } else {
        error.value = `情绪记录加载失败：${(e as Error).message}`
      }
    } finally {
      loading.value = false
    }
  }

  /** 记录一条心情：写 Python 成功后插入列表 */
  async function recordEmotion(emotion: EmotionType, intensity: number, content = ''): Promise<EmotionRecord> {
    const userId = useUserStore().userId
    if (!userId) throw new Error('未登录，无法记录心情')

    const score = Math.max(1, Math.min(10, intensity / 10))
    const dto = await aiFetch<MoodDto>('/api/v1/mood', {
      method: 'POST',
      body: {
        userId,
        mood: EMOTION_LABELS[emotion],
        score: Number(score.toFixed(1)),
        note: content.trim() || null,
      },
    })

    const record = toRecord(dto)
    record.emotion = emotion
    records.value.unshift(record)
    currentEmotion.value = emotion
    writeCache()
    return record
  }

  // 按天聚合：返回 { 'YYYY-MM-DD': 主导情绪 }
  const getCalendarData = (year: number, month: number): Record<string, EmotionType> => {
    const dayMap: Record<string, Record<EmotionType, number>> = {}
    for (const record of records.value) {
      const d = record.timestamp
      if (d.getFullYear() !== year || d.getMonth() !== month) continue
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
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
    for (const record of records.value) distribution[record.emotion] += 1

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

  /** 二期能力：Python 端无删除端点 */
  function deleteRecord(): never {
    throw new Error('情绪记录删除暂未开放（后端未提供删除接口）')
  }

  return {
    records,
    currentEmotion,
    loading,
    error,
    fromCache,
    emotionMeta: EMOTION_META,
    emotionLabels: EMOTION_LABELS,
    loadMoods,
    recordEmotion,
    getCalendarData,
    getStats,
    deleteRecord,
  }
})
