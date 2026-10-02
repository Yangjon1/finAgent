import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '../api/client'

export type CurrentUser = { id: string; tenant_id: string; username: string; display_name: string; roles: string[]; permissions: string[] }

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('finagent_token'))
  const user = ref<CurrentUser | null>(null)
  const isAuthenticated = computed(() => Boolean(token.value))

  async function login(username: string, password: string) {
    const response = await api.post('/auth/login', { username, password })
    const accessToken: string = response.data.data.access_token
    token.value = accessToken
    localStorage.setItem('finagent_token', accessToken)
    await fetchMe()
  }

  async function fetchMe() {
    const response = await api.get('/auth/me')
    user.value = response.data.data
  }

  async function hydrate() {
    if (token.value && !user.value) {
      try { await fetchMe() } catch { logout() }
    }
  }

  function hasPermission(permission: string) {
    return Boolean(user.value?.permissions.includes('*') || user.value?.permissions.includes(permission))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('finagent_token')
  }

  return { token, user, isAuthenticated, login, fetchMe, hydrate, hasPermission, logout }
})
