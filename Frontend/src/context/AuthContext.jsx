import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api'

const AuthContext = createContext(null)

export const SEEDED_ACCOUNTS = [
  { key: 'admin', label: 'Admin (Hamed)', role: 'Lead Support Agent', tenant: 'default', desc: 'Lead Support Agent' },
  { key: 'ramya', label: 'Ramya', role: 'Support Specialist', tenant: 'default', desc: 'Support Specialist' },
  { key: 'sandy', label: 'Sandy', role: 'Tier 2 Support', tenant: 'default', desc: 'Tier 2 Support' },
  { key: 'customer1', label: 'Customer 1', role: 'Customer', tenant: 'default', desc: 'Tenant default Customer' },
  { key: 'acme_user', label: 'Acme User', role: 'Customer', tenant: 'tenant_acme', desc: 'Isolated Tenant Customer' }
]

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => api.getUser())
  const [token, setToken] = useState(() => api.getToken())
  const [loading, setLoading] = useState(false)
  const [authError, setAuthError] = useState(null)

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null)
      setToken('')
    }
    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [])

  const login = async (username, password) => {
    setLoading(true)
    setAuthError(null)
    try {
      const data = await api.login(username, password)
      setUser({
        user_id: data.user_id,
        username: data.username,
        fullname: data.fullname,
        role: data.role,
        tenant_id: data.tenant_id,
        is_guest: data.is_guest
      })
      setToken(data.access_token)
      return data
    } catch (err) {
      setAuthError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const register = async (regData) => {
    setLoading(true)
    setAuthError(null)
    try {
      const data = await api.register(regData)
      setUser({
        user_id: data.user_id,
        username: data.username,
        fullname: data.fullname,
        role: data.role,
        tenant_id: data.tenant_id,
        is_guest: data.is_guest
      })
      setToken(data.access_token)
      return data
    } catch (err) {
      setAuthError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const loginAsGuest = async (fullname = 'Guest Visitor', tenant_id = 'default') => {
    setLoading(true)
    setAuthError(null)
    try {
      const data = await api.createGuest(fullname, tenant_id)
      setUser({
        user_id: data.user_id,
        username: data.username,
        fullname: data.fullname,
        role: data.role,
        tenant_id: data.tenant_id,
        is_guest: true
      })
      setToken(data.access_token)
      return data
    } catch (err) {
      setAuthError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const quickLogin = async (accountKey) => {
    const passwords = {
      admin: 'admin123',
      sai: 'sai123',
      ramya: 'ramya123',
      sandy: 'sandy123',
      customer1: 'customer123',
      acme_user: 'acme123'
    }
    const pwd = passwords[accountKey]
    if (pwd) {
      return await login(accountKey, pwd)
    }
  }

  const logout = async () => {
    setLoading(true)
    try {
      await api.logout()
    } catch {
      // clear anyway
    } finally {
      setUser(null)
      setToken('')
      setLoading(false)
    }
  }

  const isAgentOrAdmin = user && [
    'Lead Support Agent',
    'Support Specialist',
    'Tier 2 Support',
    'Admin',
    'agent',
    'admin'
  ].includes(user.role)

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isGuest: !!user?.is_guest,
        isAgentOrAdmin,
        loading,
        authError,
        setAuthError,
        login,
        register,
        loginAsGuest,
        quickLogin,
        logout
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
