import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { SceneType, SceneSettings } from '@/types'

const STORAGE_KEY = 'ai-scene-settings'

export const SCENE_META: Record<SceneType, { label: string; icon: string; description: string }> = {
  bedtime_story: { label: '睡前故事', icon: '🌙', description: '夜晚陪伴入眠' },
  morning_greeting: { label: '晨间问候', icon: '☀️', description: '清晨温柔唤醒' },
  pomodoro: { label: '番茄钟', icon: '🍅', description: '专注时贴心陪伴' },
  weather: { label: '天气提醒', icon: '🌦️', description: '根据天气给建议' },
}

const DEFAULT_SETTINGS: SceneSettings = {
  bedtime_story: { enabled: true, time: '22:00' },
  morning_greeting: { enabled: true, time: '08:00' },
  pomodoro: { enabled: false },
  weather: { enabled: false },
}

const loadSettings = (): SceneSettings => {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) return { ...DEFAULT_SETTINGS, ...JSON.parse(saved) }
  } catch (error) {
    console.error('Failed to load scene settings:', error)
  }
  return { ...DEFAULT_SETTINGS }
}

export function useSceneService() {
  const sceneSettings = ref<SceneSettings>(loadSettings())
  const currentScene = ref<SceneType | null>(null)
  let timer: ReturnType<typeof setInterval> | null = null

  // 根据当前小时推断推荐场景
  const inferScene = (): SceneType | null => {
    const hour = new Date().getHours()
    if (hour >= 22 || hour < 6) return 'bedtime_story'
    if (hour >= 6 && hour < 9) return 'morning_greeting'
    return null
  }

  const recommendedScene = computed<SceneType | null>(() => inferScene())

  const setScene = (type: SceneType | null) => {
    currentScene.value = type
  }

  const updateSettings = (type: SceneType, patch: Partial<{ enabled: boolean; time: string }>) => {
    sceneSettings.value = {
      ...sceneSettings.value,
      [type]: { ...sceneSettings.value[type], ...patch },
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sceneSettings.value))
    } catch (error) {
      console.error('Failed to save scene settings:', error)
    }
  }

  const getSceneRecommendations = (): SceneType[] => {
    const list: SceneType[] = []
    const inferred = inferScene()
    if (inferred) list.push(inferred)
    for (const key of Object.keys(sceneSettings.value) as SceneType[]) {
      if (sceneSettings.value[key]?.enabled && !list.includes(key)) list.push(key)
    }
    return list
  }

  const checkSceneTriggers = () => {
    const inferred = inferScene()
    if (inferred && sceneSettings.value[inferred]?.enabled) {
      currentScene.value = inferred
    }
  }

  onMounted(() => {
    checkSceneTriggers()
    timer = setInterval(checkSceneTriggers, 60000)
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })

  return {
    sceneSettings,
    currentScene,
    recommendedScene,
    sceneMeta: SCENE_META,
    setScene,
    updateSettings,
    getSceneRecommendations,
  }
}
