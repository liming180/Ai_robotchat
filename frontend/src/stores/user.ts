import { defineStore } from 'pinia'
import { ref, computed, onMounted } from 'vue'

interface User {
  id: string
  email: string
  name: string
  avatar?: string
}

export const useUserStore = defineStore('user', () => {
  // 用户信息
  const user = ref<User | null>(null)
  const isAuthenticated = computed(() => user.value !== null)

  // 初始化时从 localStorage 加载用户信息
  onMounted(() => {
    const savedUser = localStorage.getItem('ai_companion_user')
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (error) {
        console.error('Failed to load user from localStorage:', error)
        localStorage.removeItem('ai_companion_user')
      }
    }
  })

  // 登录
  const login = async (email: string, password: string) => {
    // 模拟登录请求
    await new Promise(resolve => setTimeout(resolve, 800))
    
    // 这里可以替换为真实的 API 请求
    const mockUser: User = {
      id: '1',
      email,
      name: email.split('@')[0] || '用户',
      avatar: `https://api.dicebear.com/7.x/anime/svg?seed=${email}`
    }
    
    user.value = mockUser
    localStorage.setItem('ai_companion_user', JSON.stringify(mockUser))
    
    return true
  }

  // 注册
  const register = async (email: string, name: string, password: string) => {
    // 模拟注册请求
    await new Promise(resolve => setTimeout(resolve, 800))
    
    const mockUser: User = {
      id: Date.now().toString(),
      email,
      name,
      avatar: `https://api.dicebear.com/7.x/anime/svg?seed=${email}`
    }
    
    user.value = mockUser
    localStorage.setItem('ai_companion_user', JSON.stringify(mockUser))
    
    return true
  }

  // 登出
  const logout = () => {
    user.value = null
    localStorage.removeItem('ai_companion_user')
  }

  return {
    user,
    isAuthenticated,
    login,
    register,
    logout
  }
})
