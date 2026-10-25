import React, { useState } from 'react'
import { useAuth, SEEDED_ACCOUNTS } from '../context/AuthContext'
import { LogIn, UserPlus, Sparkles, Building, User, Lock, Mail, ShieldAlert } from '../icons'
import { ZipTicketLogo } from './ZipTicketLogo'

export const AuthView = () => {
  const { login, register, loginAsGuest, quickLogin, loading, authError, setAuthError } = useAuth()
  const [mode, setMode] = useState('login') // 'login' | 'register' | 'guest'

  // Login form state
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')

  // Register form state
  const [regForm, setRegForm] = useState({
    username: '',
    fullname: '',
    email: '',
    password: '',
    tenant_id: 'default',
    role: 'Customer'
  })

  // Guest form state
  const [guestName, setGuestName] = useState('Anonymous Guest')
  const [guestTenant, setGuestTenant] = useState('default')

  const handleLoginSubmit = async (e) => {
    e.preventDefault()
    try {
      await login(username, password)
    } catch {
      // Error handled in context
    }
  }

  const handleRegisterSubmit = async (e) => {
    e.preventDefault()
    try {
      await register(regForm)
    } catch {
      // Error handled in context
    }
  }

  const handleGuestSubmit = async (e) => {
    e.preventDefault()
    try {
      await loginAsGuest(guestName, guestTenant)
    } catch {
      // Error handled in context
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <ZipTicketLogo size="lg" />
          <p className="auth-subtitle">AI Incident Resolution Platform &bull; Multi-Tenant Isolated</p>
        </div>

        {/* Tab switcher */}
        <div className="auth-tabs">
          <button
            className={`auth-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => { setMode('login'); setAuthError(null) }}
          >
            <LogIn size={16} />
            <span>Sign In</span>
          </button>
          <button
            className={`auth-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => { setMode('register'); setAuthError(null) }}
          >
            <UserPlus size={16} />
            <span>Register</span>
          </button>
          <button
            className={`auth-tab ${mode === 'guest' ? 'active' : ''}`}
            onClick={() => { setMode('guest'); setAuthError(null) }}
          >
            <Sparkles size={16} />
            <span>Guest Access</span>
          </button>
        </div>

        {/* Error notification */}
        {authError && (
          <div className="alert-error">
            <ShieldAlert size={18} />
            <span>{authError}</span>
          </div>
        )}

        {/* Tab 1: Login */}
        {mode === 'login' && (
          <form onSubmit={handleLoginSubmit} className="auth-form">
            <div className="form-group">
              <label>Username</label>
              <div className="input-with-icon">
                <User size={16} />
                <input
                  type="text"
                  required
                  placeholder="e.g. sai or customer1"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Password</label>
              <div className="input-with-icon">
                <Lock size={16} />
                <input
                  type="password"
                  required
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
              {loading ? 'Authenticating...' : 'Sign In'}
            </button>

            {/* Quick Demo Accounts */}
            <div className="quick-seed-box">
              <div className="quick-seed-title">Or click to login with Default Seeded Accounts:</div>
              <div className="seed-pills">
                {SEEDED_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.key}
                    type="button"
                    className="seed-pill"
                    onClick={() => {
                      setUsername(acc.key)
                      setPassword(acc.key === 'sai' ? 'sai123' : acc.key === 'ramya' ? 'ramya123' : acc.key === 'sandy' ? 'sandy123' : `${acc.key}123`)
                    }}
                  >
                    <strong>{acc.key}</strong>
                    <span className="pill-role">({acc.role})</span>
                  </button>
                ))}
              </div>
            </div>
          </form>
        )}

        {/* Tab 2: Register */}
        {mode === 'register' && (
          <form onSubmit={handleRegisterSubmit} className="auth-form">
            <div className="form-row">
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. john_doe"
                  value={regForm.username}
                  onChange={(e) => setRegForm({ ...regForm, username: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. John Doe"
                  value={regForm.fullname}
                  onChange={(e) => setRegForm({ ...regForm, fullname: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Email Address</label>
              <div className="input-with-icon">
                <Mail size={16} />
                <input
                  type="email"
                  required
                  placeholder="user@example.com"
                  value={regForm.email}
                  onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Password</label>
              <div className="input-with-icon">
                <Lock size={16} />
                <input
                  type="password"
                  required
                  placeholder="At least 6 characters"
                  value={regForm.password}
                  onChange={(e) => setRegForm({ ...regForm, password: e.target.value })}
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Tenant ID (Organization)</label>
                <div className="input-with-icon">
                  <Building size={16} />
                  <input
                    type="text"
                    required
                    placeholder="e.g. default or acme_corp"
                    value={regForm.tenant_id}
                    onChange={(e) => setRegForm({ ...regForm, tenant_id: e.target.value })}
                  />
                </div>
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  value={regForm.role}
                  onChange={(e) => setRegForm({ ...regForm, role: e.target.value })}
                >
                  <option value="Customer">Customer</option>
                  <option value="Support Specialist">Support Specialist</option>
                  <option value="Tier 2 Support">Tier 2 Support</option>
                  <option value="Lead Support Agent">Lead Support Agent</option>
                </select>
              </div>
            </div>

            <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>
        )}

        {/* Tab 3: Guest Access */}
        {mode === 'guest' && (
          <form onSubmit={handleGuestSubmit} className="auth-form">
            <div className="guest-banner">
              <Sparkles size={20} className="sparkle-icon" />
              <div>
                <h4>Temporary Guest Session</h4>
                <p>Instant access without registration. Guest sessions are isolated and automatically expire via configured TTL policies.</p>
              </div>
            </div>

            <div className="form-group">
              <label>Display Name</label>
              <input
                type="text"
                placeholder="e.g. Alex"
                value={guestName}
                onChange={(e) => setGuestName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Tenant Identifier</label>
              <input
                type="text"
                placeholder="default"
                value={guestTenant}
                onChange={(e) => setGuestTenant(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-accent btn-block" disabled={loading}>
              {loading ? 'Issuing Guest Session...' : 'Continue as Guest (24h TTL)'}
            </button>
          </form>
        )}

        <div className="auth-footer">
          Developed by Hamed &bull; Powered by FastAPI & LangGraph Multi-Tier Fallback
        </div>
      </div>
    </div>
  )
}
