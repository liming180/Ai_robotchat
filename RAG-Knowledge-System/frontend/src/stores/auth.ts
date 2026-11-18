import { defineStore } from 'pinia'

import { api, clearToken, getToken, setToken } from '@/lib/api'

const EMAIL_KEY = 'rag_user_email'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: getToken(),
    userEmail: localStorage.getItem(EMAIL_KEY) || '',
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  actions: {
    async login(email: string, password: string) {
      // 账号即主应用账号：8002 /api/v1/auth/login 转发 Java 8081 校验并签发 JWT
      const data = await api.login(email, password)
      setToken(data.accessToken)
      this.token = data.accessToken
      this.userEmail = data.user?.email || email
      localStorage.setItem(EMAIL_KEY, this.userEmail)
    },
    logout() {
      clearToken()
      localStorage.removeItem(EMAIL_KEY)
      this.token = ''
      this.userEmail = ''
    },
  },
})
