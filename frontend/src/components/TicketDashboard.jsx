import React, { useState, useEffect, useMemo } from 'react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import {
  Search,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Bot,
  Building,
  User,
  ExternalLink
} from '../icons'

export const TicketDashboard = ({ onSelectTicket, onOpenCreate }) => {
  const { user, isAgentOrAdmin } = useAuth()
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Filters
  const [statusFilter, setStatusFilter] = useState('All')
  const [priorityFilter, setPriorityFilter] = useState('All')
  const [searchQuery, setSearchQuery] = useState('')

  const fetchTickets = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getTickets()
      setTickets(Array.isArray(data) ? data : [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTickets()
  }, [user])

  // KPIs
  const stats = useMemo(() => {
    const total = tickets.length
    const resolved = tickets.filter(t => t.status === 'Resolved').length
    const humanReview = tickets.filter(t => t.status === 'Human Review').length
    const aiProcessing = tickets.filter(t => t.status === 'AI Processing').length
    const manual = tickets.filter(t => t.status === 'Manual Handling').length
    return { total, resolved, humanReview, aiProcessing, manual }
  }, [tickets])

  // Filtered & Searched Tickets
  const filteredTickets = useMemo(() => {
    return tickets.filter(t => {
      if (statusFilter !== 'All' && t.status !== statusFilter) return false
      if (priorityFilter !== 'All' && t.priority !== priorityFilter) return false
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase()
        const matchId = t.ticket_id?.toLowerCase().includes(query)
        const matchTitle = t.title_query?.toLowerCase().includes(query)
        const matchCat = t.category?.toLowerCase().includes(query)
        const matchUser = t.username?.toLowerCase().includes(query)
        if (!matchId && !matchTitle && !matchCat && !matchUser) return false
      }
      return true
    })
  }, [tickets, statusFilter, priorityFilter, searchQuery])

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'Resolved': return 'badge badge-success'
      case 'Human Review': return 'badge badge-warning'
      case 'AI Processing': return 'badge badge-info'
      case 'Manual Handling': return 'badge badge-danger'
      default: return 'badge badge-neutral'
    }
  }

  const getPriorityBadgeClass = (priority) => {
    switch (priority) {
      case 'High': return 'priority-badge priority-high'
      case 'Medium': return 'priority-badge priority-medium'
      case 'Low': return 'priority-badge priority-low'
      default: return 'priority-badge'
    }
  }

  return (
    <div className="dashboard-container">
      {/* Scope banner */}
      <div className="scope-banner">
        <div className="scope-info">
          <Building size={16} />
          <span>Active Tenant Scope: <strong>{user?.tenant_id}</strong></span>
          <span className="bullet">&bull;</span>
          <span>Access Level: <strong>{user?.role}</strong></span>
          <span className="bullet">&bull;</span>
          <span className="scope-note">
            {isAgentOrAdmin
              ? 'Displaying all tickets within current tenant.'
              : 'Strictly isolated to your user tickets.'}
          </span>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={fetchTickets} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card" onClick={() => setStatusFilter('All')}>
          <div className="kpi-header">
            <span className="kpi-title">Total Tickets</span>
            <span className="kpi-icon icon-purple"><Bot size={20} /></span>
          </div>
          <div className="kpi-value">{stats.total}</div>
          <div className="kpi-subtitle">In current tenant scope</div>
        </div>

        <div className="kpi-card" onClick={() => setStatusFilter('Resolved')}>
          <div className="kpi-header">
            <span className="kpi-title">Resolved</span>
            <span className="kpi-icon icon-green"><CheckCircle2 size={20} /></span>
          </div>
          <div className="kpi-value">{stats.resolved}</div>
          <div className="kpi-subtitle">Automated & Approved</div>
        </div>

        <div className="kpi-card" onClick={() => setStatusFilter('Human Review')}>
          <div className="kpi-header">
            <span className="kpi-title">Human Review</span>
            <span className="kpi-icon icon-yellow"><Clock size={20} /></span>
          </div>
          <div className="kpi-value">{stats.humanReview}</div>
          <div className="kpi-subtitle">HITL Pending Approval</div>
        </div>

        <div className="kpi-card" onClick={() => setStatusFilter('Manual Handling')}>
          <div className="kpi-header">
            <span className="kpi-title">Manual Handling</span>
            <span className="kpi-icon icon-red"><AlertTriangle size={20} /></span>
          </div>
          <div className="kpi-value">{stats.manual}</div>
          <div className="kpi-subtitle">High Urgency Escalated</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="filter-bar">
        <div className="search-box">
          <Search size={18} />
          <input
            type="text"
            placeholder="Search tickets by ID, subject, category..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <div className="status-tabs">
            {['All', 'Resolved', 'Human Review', 'AI Processing', 'Manual Handling'].map(st => (
              <button
                key={st}
                className={`tab-btn ${statusFilter === st ? 'active' : ''}`}
                onClick={() => setStatusFilter(st)}
              >
                {st}
              </button>
            ))}
          </div>

          <select
            className="priority-select"
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="All">All Priorities</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
      </div>

      {/* Tickets List */}
      <div className="tickets-wrapper">
        {loading && tickets.length === 0 ? (
          <div className="loading-state">
            <RefreshCw size={28} className="spin" />
            <p>Loading tickets from backend...</p>
          </div>
        ) : error ? (
          <div className="error-state">
            <AlertTriangle size={28} />
            <p>{error}</p>
            <button className="btn btn-secondary btn-sm" onClick={fetchTickets}>Retry</button>
          </div>
        ) : filteredTickets.length === 0 ? (
          <div className="empty-state">
            <Bot size={36} />
            <h3>No tickets found</h3>
            <p>Try adjusting your search criteria or create a new ticket to run the AI agent workflow.</p>
            {onOpenCreate && (
              <button className="btn btn-primary" onClick={onOpenCreate}>Create Ticket</button>
            )}
          </div>
        ) : (
          <div className="table-responsive">
            <table className="tickets-table">
              <thead>
                <tr>
                  <th>Ticket ID</th>
                  <th>Priority</th>
                  <th>Category</th>
                  <th>Inquiry / Subject</th>
                  <th>Customer</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Resolved By</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredTickets.map(ticket => (
                  <tr
                    key={ticket.ticket_id}
                    className="ticket-row"
                    onClick={() => onSelectTicket(ticket)}
                  >
                    <td className="ticket-id-cell">
                      <strong>{ticket.ticket_id}</strong>
                    </td>
                    <td>
                      <span className={getPriorityBadgeClass(ticket.priority)}>
                        {ticket.priority || 'Medium'}
                      </span>
                    </td>
                    <td>
                      <span className="category-tag">{ticket.category || 'General'}</span>
                    </td>
                    <td className="title-cell">
                      <div className="ticket-title">{ticket.title_query}</div>
                      {ticket.intent && <div className="ticket-intent">Intent: {ticket.intent}</div>}
                    </td>
                    <td>
                      <div className="user-cell">
                        <User size={13} />
                        <span>{ticket.username}</span>
                      </div>
                    </td>
                    <td>
                      <span className={getStatusBadgeClass(ticket.status)}>
                        {ticket.status}
                      </span>
                    </td>
                    <td>
                      {ticket.ai_confidence !== null && ticket.ai_confidence !== undefined ? (
                        <div className="confidence-pill">
                          <span
                            className="confidence-fill"
                            style={{
                              width: `${Math.min(100, ticket.ai_confidence)}%`,
                              backgroundColor: ticket.ai_confidence >= 75 ? '#22c55e' : '#f59e0b'
                            }}
                          />
                          <span className="confidence-text">{ticket.ai_confidence}%</span>
                        </div>
                      ) : (
                        <span className="text-muted">&mdash;</span>
                      )}
                    </td>
                    <td>
                      <span className="resolved-by-text">{ticket.resolved_by || '&mdash;'}</span>
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={(e) => {
                          e.stopPropagation()
                          onSelectTicket(ticket)
                        }}
                      >
                        <ExternalLink size={14} />
                        <span>Review</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
