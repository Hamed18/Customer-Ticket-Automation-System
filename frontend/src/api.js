const BASE_URL = '' // Uses Vite reverse-proxy or direct relative path

export const api = {
  getToken() {
    return localStorage.getItem('token') || ''
  },

  setAuth(data) {
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('user', JSON.stringify({
      user_id: data.user_id,
      username: data.username,
      fullname: data.fullname,
      role: data.role,
      tenant_id: data.tenant_id,
      is_guest: data.is_guest
    }))
  },

  clearAuth() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  },

  getUser() {
    try {
      const u = localStorage.getItem('user')
      return u ? JSON.parse(u) : null
    } catch {
      return null
    }
  },

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }

    const token = this.getToken()
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`
    }

    const config = {
      ...options,
      headers
    }

    try {
      const res = await fetch(`${BASE_URL}${endpoint}`, config)
      if (res.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register') && !endpoint.includes('/auth/guest')) {
        this.clearAuth()
        window.dispatchEvent(new Event('auth:unauthorized'))
        throw new Error('Session expired or unauthorized. Please log in again.')
      }

      const contentType = res.headers.get('content-type')
      const isJson = contentType && contentType.includes('application/json')
      const data = isJson ? await res.json() : await res.text()

      if (!res.ok) {
        const errorDetail = (data && data.detail) || res.statusText || 'Request failed'
        throw new Error(errorDetail)
      }

      return data
    } catch (err) {
      console.error(`API Error on [${options.method || 'GET'}] ${endpoint}:`, err)
      throw err
    }
  },

  // Auth endpoints
  async login(username, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
    this.setAuth(data)
    return data
  },

  async register(registerData) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(registerData)
    })
    this.setAuth(data)
    return data
  },

  async createGuest(fullname = 'Guest User', tenant_id = 'default') {
    const data = await this.request('/auth/guest', {
      method: 'POST',
      body: JSON.stringify({ fullname, tenant_id })
    })
    this.setAuth(data)
    return data
  },

  async getMe() {
    return await this.request('/auth/me')
  },

  async logout() {
    try {
      await this.request('/auth/logout', { method: 'POST' })
    } finally {
      this.clearAuth()
    }
  },

  // Tickets
  async getTickets() {
    return await this.request('/tickets/')
  },

  async getTicket(ticketId) {
    return await this.request(`/tickets/${ticketId}`)
  },

  async createTicket(payload) {
    return await this.request('/tickets/create', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  },

  async approveResponse(payload) {
    return await this.request('/tickets/update/approved_response', {
      method: 'PATCH',
      body: JSON.stringify(payload)
    })
  },

  // Agent execution
  async executeAgent(payload) {
    return await this.request('/agent/execute', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  },

  async resumeAgent(threadId, finalResponse) {
    return await this.request('/agent/resume', {
      method: 'POST',
      body: JSON.stringify({
        thread_id: threadId,
        final_response: finalResponse
      })
    })
  },

  // Threads
  async getThread(ticketId) {
    return await this.request(`/threads/thread?ticket_id=${encodeURIComponent(ticketId)}`)
  },

  // Episodic Memories
  async getMemories(userId = '') {
    const url = userId ? `/memories/?user_id=${encodeURIComponent(userId)}` : '/memories/'
    return await this.request(url)
  },

  // TTL Reaper
  async triggerReaper() {
    return await this.request('/reaper/trigger', { method: 'POST' })
  },

  async getReaperStats() {
    return await this.request('/reaper/stats')
  }
}
