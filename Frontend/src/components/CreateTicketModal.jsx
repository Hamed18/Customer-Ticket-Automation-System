import React, { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import { X, Sparkles, Send, Bot, AlertCircle, CheckCircle2 } from '../icons'

export const CreateTicketModal = ({ onClose, onCreated }) => {
  const { user } = useAuth()
  const [titleQuery, setTitleQuery] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('Technical')
  const [priority, setPriority] = useState('Medium')
  const [mode, setMode] = useState('agent') // 'agent' | 'manual'

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [successResult, setSuccessResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!titleQuery.trim()) return

    setLoading(true)
    setError(null)
    setSuccessResult(null)

    try {
      if (mode === 'agent') {
        // Run AI Agent pipeline
        const result = await api.executeAgent({
          title_query: titleQuery.trim(),
          ticket_description: description.trim()
        })
        setSuccessResult({
          message: 'AI Agent workflow triggered successfully!',
          data: result
        })
      } else {
        // Create manual ticket
        const ticket = await api.createTicket({
          title_query: titleQuery.trim(),
          ticket_description: description.trim(),
          category,
          priority
        })
        setSuccessResult({
          message: `Ticket ${ticket.ticket_id} created successfully!`,
          data: ticket
        })
      }

      if (onCreated) onCreated()
      setTimeout(() => {
        onClose()
      }, 1500)
    } catch (err) {
      setError(err.message || 'Operation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div className="modal-header-info">
            <h2 className="modal-title">New Incident / Support Inquiry</h2>
            <p className="modal-subtitle">
              Submitted under Tenant: <strong>{user?.tenant_id}</strong> &bull; User: <strong>{user?.username}</strong>
            </p>
          </div>
          <button className="btn btn-icon" onClick={onClose}><X size={20} /></button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          {error && (
            <div className="alert-error">
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          {successResult && (
            <div className="alert-success">
              <CheckCircle2 size={18} />
              <span>{successResult.message}</span>
            </div>
          )}

          {/* Mode Selector */}
          <div className="agent-mode-selector">
            <label
              className={`mode-option ${mode === 'agent' ? 'active' : ''}`}
              onClick={() => setMode('agent')}
            >
              <input type="radio" checked={mode === 'agent'} onChange={() => setMode('agent')} />
              <div>
                <strong>🤖 Run LangGraph AI Agent</strong>
                <p>Automated classification, knowledge retrieval, and AI resolution draft.</p>
              </div>
            </label>

            <label
              className={`mode-option ${mode === 'manual' ? 'active' : ''}`}
              onClick={() => setMode('manual')}
            >
              <input type="radio" checked={mode === 'manual'} onChange={() => setMode('manual')} />
              <div>
                <strong>👤 Direct Support Escalation</strong>
                <p>Enqueue directly into agent manual handling queue.</p>
              </div>
            </label>
          </div>

          <div className="form-group">
            <label>Inquiry Summary / Title *</label>
            <input
              type="text"
              required
              placeholder="e.g. Cannot reset account password or payment declined"
              value={titleQuery}
              onChange={(e) => setTitleQuery(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Detailed Description</label>
            <textarea
              rows={4}
              placeholder="Describe what occurred, any error messages, or steps taken..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {mode === 'manual' && (
            <div className="form-row">
              <div className="form-group">
                <label>Category</label>
                <select value={category} onChange={(e) => setCategory(e.target.value)}>
                  <option value="Technical">Technical</option>
                  <option value="Billing">Billing</option>
                  <option value="Refund">Refund</option>
                  <option value="Order">Order</option>
                  <option value="Login">Login</option>
                </select>
              </div>

              <div className="form-group">
                <label>Urgency Priority</label>
                <select value={priority} onChange={(e) => setPriority(e.target.value)}>
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                </select>
              </div>
            </div>
          )}

          <div className="modal-actions">
            <button type="button" className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              <Send size={16} />
              <span>{loading ? 'Processing...' : mode === 'agent' ? 'Execute AI Workflow' : 'Create Ticket'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
