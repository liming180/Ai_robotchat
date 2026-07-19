import { defineStore } from 'pinia'
import { ref, computed, onMounted, watch } from 'vue'
import type { Companion } from '@/types'
import { createSvgAvatarDataUrl, isQuotaExceededError } from '@/lib/avatar'

// 序列化和反序列化 Date 对象
const serializeCompanion = (companion: Companion) => ({
  ...companion,
  createdAt: companion.createdAt.toISOString()
})

const deserializeCompanion = (data: any): Companion => ({
  ...data,
  createdAt: new Date(data.createdAt)
})

export const useCompanionStore = defineStore('companion', () => {
  // 预设伴侣数据
  const defaultCompanions: Companion[] = [
    {
      id: '1',
      name: '小暖',
      avatar: createSvgAvatarDataUrl({ seed: 'Warm', label: '暖' }),
      description: '一个温柔体贴的聊天伙伴，总是能给你温暖的安慰',
      category: '日常聊天',
      personality: '温柔体贴',
      systemPrompt: '你是一个温柔体贴的AI伴侣，擅长倾听和安慰，用温暖的语言回应对方。',
      isFavorite: true,
      intimacy: 0,
      createdAt: new Date(),
      tags: ['温柔', '倾听', '治愈']
    },
    {
      id: '2',
      name: '小智',
      avatar: createSvgAvatarDataUrl({ seed: 'Smart', label: '智' }),
      description: '知识渊博的学习助手，帮你解答各种问题',
      category: '学习助手',
      personality: '博学多才',
      systemPrompt: '你是一个博学多才的AI助手，擅长解答各种学习问题，用清晰易懂的方式解释知识。',
      isFavorite: false,
      intimacy: 0,
      createdAt: new Date(),
      tags: ['学习', '知识', '理性']
    },
    {
      id: '3',
      name: '小乐',
      avatar: createSvgAvatarDataUrl({ seed: 'Happy', label: '乐' }),
      description: '幽默风趣的开心果，总能让你开怀大笑',
      category: '娱乐陪伴',
      personality: '幽默风趣',
      systemPrompt: '你是一个幽默风趣的AI伴侣，喜欢讲笑话，用轻松有趣的方式和对方聊天。',
      isFavorite: false,
      intimacy: 0,
      createdAt: new Date(),
      tags: ['幽默', '开心', '有趣']
    },
    {
      id: '4',
      name: '小雅',
      avatar: createSvgAvatarDataUrl({ seed: 'Elegant', label: '雅' }),
      description: '文艺优雅的聊天伙伴，陪你品味生活',
      category: '日常聊天',
      personality: '文艺优雅',
      systemPrompt: '你是一个文艺优雅的AI伴侣，喜欢文学和艺术，用诗意的语言和对方交流。',
      isFavorite: true,
      intimacy: 0,
      createdAt: new Date(),
      tags: ['文艺', '优雅', '诗意']
    },
    {
      id: '5',
      name: '小健',
      avatar: createSvgAvatarDataUrl({ seed: 'Healthy', label: '健' }),
      description: '阳光健康的运动伙伴，激励你积极向上',
      category: '日常聊天',
      personality: '阳光积极',
      systemPrompt: '你是一个阳光积极的AI伴侣，擅长鼓励和激励，用充满活力的语言和对方交流。',
      isFavorite: false,
      intimacy: 0,
      createdAt: new Date(),
      tags: ['阳光', '积极', '运动']
    },
    {
      id: '6',
      name: '小美',
      avatar: createSvgAvatarDataUrl({ seed: 'Creative', label: '美' }),
      description: '充满创意的艺术伙伴，帮你激发灵感',
      category: '娱乐陪伴',
      personality: '创意无限',
      systemPrompt: '你是一个充满创意的AI伴侣，喜欢艺术和设计，用创新思维和对方交流。',
      isFavorite: false,
      intimacy: 0,
      createdAt: new Date(),
      tags: ['创意', '艺术', '灵感']
    }
  ]

  // 伴侣数据
  const companions = ref<Companion[]>([...defaultCompanions])
  const customCompanions = ref<Companion[]>([])
  const persistError = ref<string>('')

  // 从 localStorage 加载数据
  onMounted(() => {
    const savedCustomCompanions = localStorage.getItem('ai_companion_custom')
    const savedCompanions = localStorage.getItem('ai_companion_main')

    if (savedCustomCompanions) {
      try {
        const parsed = JSON.parse(savedCustomCompanions)
        customCompanions.value = parsed.map(deserializeCompanion)
      } catch (error) {
        console.error('Failed to load custom companions:', error)
      }
    }

    if (savedCompanions) {
      try {
        const parsed = JSON.parse(savedCompanions)
        // 合并默认数据和保存的数据，保持默认伴侣存在
        const savedMap = new Map(parsed.map((c: Companion) => [c.id, c]))
        companions.value = defaultCompanions.map(defaultC => {
          const saved = savedMap.get(defaultC.id)
          if (saved) {
            return deserializeCompanion(saved)
          }
          return defaultC
        })
      } catch (error) {
        console.error('Failed to load companions:', error)
      }
    }
  })

  // 保存数据到 localStorage
  watch([companions, customCompanions], ([newCompanions, newCustom]) => {
    try {
      persistError.value = ''
      localStorage.setItem('ai_companion_main', JSON.stringify(newCompanions.map(serializeCompanion)))
      localStorage.setItem('ai_companion_custom', JSON.stringify(newCustom.map(serializeCompanion)))
    } catch (error) {
      if (isQuotaExceededError(error)) {
        persistError.value = '本地存储空间不足，保存失败。请更换更小的图片、清理聊天记录或清空缓存后重试。'
      } else {
        persistError.value = '保存失败，请稍后重试。'
      }
      console.error('Failed to save companions:', error)
    }
  }, { deep: true })

  // 所有伴侣（预设 + 自定义）
  const allCompanions = computed(() => [...companions.value, ...customCompanions.value])

  // 收藏的伴侣
  const favoriteCompanions = computed(() =>
    allCompanions.value.filter(c => c.isFavorite)
  )

  // 根据分类筛选
  const filterByCategory = (category: string) => {
    if (category === '全部') return allCompanions.value
    return allCompanions.value.filter(c => c.category === category)
  }

  // 搜索伴侣
  const searchCompanions = (query: string) => {
    const lowerQuery = query.toLowerCase()
    return allCompanions.value.filter(c =>
      c.name.toLowerCase().includes(lowerQuery) ||
      c.description.toLowerCase().includes(lowerQuery) ||
      c.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
    )
  }

  // 获取单个伴侣
  const getCompanionById = (id: string) =>
    allCompanions.value.find(c => c.id === id)

  // 切换收藏
  const toggleFavorite = (id: string) => {
    const companion = allCompanions.value.find(c => c.id === id)
    if (companion) {
      companion.isFavorite = !companion.isFavorite
    }
  }

  // 添加自定义伴侣
  const addCustomCompanion = (companion: Omit<Companion, 'id' | 'createdAt' | 'isFavorite' | 'intimacy'>) => {
    const newCompanion: Companion = {
      ...companion,
      id: Date.now().toString(),
      isFavorite: false,
      intimacy: 0,
      createdAt: new Date()
    }
    customCompanions.value.push(newCompanion)
  }

  // 增加亲密度
  const increaseIntimacy = (id: string, amount: number = 5) => {
    const companion = allCompanions.value.find(c => c.id === id)
    if (companion) {
      companion.intimacy = Math.min(100, companion.intimacy + amount)
    }
  }

  // 更新伴侣信息
  const updateCompanion = (id: string, updates: Partial<Companion>) => {
    // 先在customCompanions找
    let index = customCompanions.value.findIndex(c => c.id === id)
    if (index !== -1) {
      customCompanions.value[index] = {
        ...customCompanions.value[index],
        ...updates
      }
    } else {
      // 在预设companions中找
      index = companions.value.findIndex(c => c.id === id)
      if (index !== -1) {
        companions.value[index] = {
          ...companions.value[index],
          ...updates
        }
      }
    }
  }

  return {
    companions,
    customCompanions,
    allCompanions,
    favoriteCompanions,
    persistError,
    filterByCategory,
    searchCompanions,
    getCompanionById,
    toggleFavorite,
    addCustomCompanion,
    updateCompanion,
    increaseIntimacy
  }
})
