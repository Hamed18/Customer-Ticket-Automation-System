import React, { useState } from 'react'
import { useAuth, SEEDED_ACCOUNTS } from '../context/AuthContext'
import { LogOut, User, Shield, Building, ChevronDown, Sparkles } from '../icons'

export const Navbar = ({ onOpenCreate }) => {
  const { user, isGuest, isAgentOrAdmin, logout, quickLogin } = useAuth()
  const [showSwitchMenu, setShowSwitchMenu] = useState(false)

  return (
    <header className="navbar">
      <div className="navbar-left">
        <div className="brand">
          <span className="brand-icon">🎫</span>
          <span className="brand-text">AI Ticket Ops</span>
          <span className="brand-version">v2.0 React</span>
        </div>

        {user && (
          <div className="tenant-badge" title="Tenant Isolation Scope">
            <Building size={14} />
            <span>Tenant: <strong>{user.tenant_id}</strong></span>
          </div>
        )}
      </div>

      <div className="navbar-right">
        {onOpenCreate && (
          <button className="btn btn-primary" onClick={onOpenCreate}>
            <Sparkles size={16} />
            <span>New Ticket / AI Ask</span>
          </button>
        )}

        {/* Quick Switch Dropdown */}
        <div className="quick-switch-wrapper">
          <button
            className="btn btn-secondary btn-sm switch-btn"
            onClick={() => setShowSwitchMenu(!showSwitchMenu)}
          >
            <span>Switch Role</span>
            <ChevronDown size={14} />
          </button>

          {showSwitchMenu && (
            <div className="dropdown-menu">
              <div className="dropdown-header">Default Seeded Accounts</div>
              {SEEDED_ACCOUNTS.map(acc => (
                <button
                  key={acc.key}
                  className={`dropdown-item ${user?.username === acc.key ? 'active' : ''}`}
                  onClick={async () => {
                    setShowSwitchMenu(false)
                    await quickLogin(acc.key)
                  }}
                >
                  <div className="acc-name">{acc.label}</div>
                  <div className="acc-role">{acc.role} &bull; {acc.tenant}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* User Chip */}
        {user && (
          <div className="user-profile-chip">
            <div className="user-avatar">
              <User size={16} />
            </div>
            <div className="user-meta">
              <div className="user-name">
                {user.fullname || user.username}
                {isGuest && <span className="guest-tag">Guest</span>}
              </div>
              <div className="user-role-line">
                <Shield size={12} />
                <span>{user.role}</span>
              </div>
            </div>
          </div>
        )}

        {/* Logout */}
        <button className="btn btn-icon" onClick={logout} title="Sign Out">
          <LogOut size={18} />
        </button>
      </div>
    </header>
  )
}
