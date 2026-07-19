import { ref } from 'vue'
import type { GameType, SharedTodo, TruthDareCard } from '@/types'

// 真心话/大冒险题库
const TRUTH_DARE_CARDS: TruthDareCard[] = [
  { id: '1', type: 'truth', content: '你最近最开心的一件事是什么？' },
  { id: '2', type: 'truth', content: '你有什么小秘密？' },
  { id: '3', type: 'truth', content: '你最喜欢什么颜色？' },
  { id: '4', type: 'truth', content: '你小时候的梦想是什么？' },
  { id: '5', type: 'truth', content: '你最喜欢的食物是什么？' },
  { id: '6', type: 'dare', content: '学一下动物叫声' },
  { id: '7', type: 'dare', content: '做一个搞笑表情' },
  { id: '8', type: 'dare', content: '唱一句歌' },
  { id: '9', type: 'dare', content: '模仿一个名人' },
  { id: '10', type: 'dare', content: '用方言说一句你好' },
]

// 二选一题库
const WOULD_YOU_RATHER_CARDS = [
  '你更喜欢晴天还是雨天？',
  '你更喜欢猫还是狗？',
  '你更喜欢城市还是乡村？',
  '你更喜欢咖啡还是茶？',
  '你更喜欢早上还是晚上？',
  '你更喜欢甜食还是咸食？',
  '你更喜欢读书还是看电影？',
  '你更喜欢夏天还是冬天？',
  '你更喜欢独处还是聚会？',
  '你更喜欢旅行还是宅家？',
]

export function useGameInteraction() {
  const todos = ref<SharedTodo[]>([])
  const selectedGame = ref<GameType>('truth_dare')
  const currentCard = ref<TruthDareCard | null>(null)

  // 从 localStorage 加载待办
  const loadTodos = () => {
    try {
      const saved = localStorage.getItem('ai-shared-todos')
      if (saved) todos.value = JSON.parse(saved)
    } catch (error) {
      console.error('Failed to load todos:', error)
    }
  }

  // 保存待办到 localStorage
  const saveTodos = () => {
    try {
      localStorage.setItem('ai-shared-todos', JSON.stringify(todos.value))
    } catch (error) {
      console.error('Failed to save todos:', error)
    }
  }

  // 抽取一张卡片
  const drawCard = (gameType: GameType) => {
    selectedGame.value = gameType
    if (gameType === 'truth_dare') {
      currentCard.value = TRUTH_DARE_CARDS[Math.floor(Math.random() * TRUTH_DARE_CARDS.length)]
    } else if (gameType === 'would_you_rather') {
      currentCard.value = {
        id: Date.now().toString(),
        type: 'would_you_rather',
        content: WOULD_YOU_RATHER_CARDS[Math.floor(Math.random() * WOULD_YOU_RATHER_CARDS.length)],
      }
    }
  }

  // 换一张卡片
  const nextCard = () => drawCard(selectedGame.value)

  // 添加待办
  const addTodo = (content: string) => {
    const todo: SharedTodo = {
      id: Date.now().toString(),
      content,
      done: false,
    }
    todos.value.push(todo)
    saveTodos()
  }

  // 切换待办完成状态
  const toggleTodo = (id: string) => {
    const todo = todos.value.find(t => t.id === id)
    if (todo) {
      todo.done = !todo.done
      saveTodos()
    }
  }

  // 删除待办
  const removeTodo = (id: string) => {
    todos.value = todos.value.filter(t => t.id !== id)
    saveTodos()
  }

  // 初始化
  loadTodos()

  return {
    selectedGame,
    currentCard,
    todos,
    drawCard,
    nextCard,
    addTodo,
    toggleTodo,
    removeTodo,
  }
}