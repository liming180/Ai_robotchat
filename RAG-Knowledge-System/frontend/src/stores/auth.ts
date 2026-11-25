import { defineStore } from 'pinia'

import { api, clearToken, getToken, getUser, setToken, setUser } from '@/lib/api'
import type { AuthUser } from '@/lib/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: getToken(),
    user: getUser() as AuthUser | null,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
    userEmail: (state) => state.user?.email || '',
    userInitial: (state) => (state.user?.name || state.user?.email || '?').slice(0, 1).toUpperCase(),
  },
  actions: {
    async login(email: string, password: string) {
      // 账号即主应用账号：8002 /api/v1/auth/login 转发 Java 8081 校验并签发 JWT
      const data = await api.login(email, password)
      setToken(data.accessToken)
      setUser(data.user || { id: '', email })
      this.token = data.accessToken
      this.user = data.user || { id: '', email }
    },
    logout() {
      clearToken()
      setUser(null)
      this.token = ''
      this.user = null
    },
    /** 401 拦截器里已清 token，这里只负责让 store 跟上磁盘状态 */
    syncFromStorage() {
      this.token = getToken()
      this.user = getUser()
    },
  },
})