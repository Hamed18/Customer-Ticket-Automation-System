import React, { useState, useEffect } from 'react'
import { api } from '../api'
import { useAuth } from '../context/AuthContext'
import {
  X,
  Bot,
  User,
  CheckCircle,
  FileText,
  Sparkles,
  Shield,
  Send,
  AlertCircle
} from '../icons'

export const TicketDetailsModal = ({ ticket, onClose, onUpdated }) => {
  const { user, isAgentOrAdmin } = useAuth()
  const [thread, setThread] = useState(null)
  const [loadingThread, setLoadingThread] = useState(false)

  // Edit / Approve response state
  const [editedResponse, setEditedResponse] = useState(
    ticket?.final_response || ticket?.ai_response || ''
  )
  const [submitting, setSubmitting] = useState(false)
  const [actionMessage, setActionMessage] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)

  useEffect(() => {
    if (!ticket) return
    setEditedResponse(ticket.final_response || ticket.ai_response || '')
    fetchThread()
  }, [ticket])

  const fetchThread = async () => {
    if (!ticket?.ticket_id) return
    setLoadingThread(true)
    try {
      const data = await api.getThread(ticket.ticket_id)
      setThread(data)
    } catch {
      // Thread may not exist if manual handling or fully completed
      setThread(null)
    } finally {
      setLoadingThread(false)
    }
  }

  const handleApprove = async () => {
    if (!editedResponse.trim()) {
      setErrorMsg('Please enter a response before approving.')
      return
    }

    setSubmitting(true)
    setErrorMsg(null)
    setActionMessage(null)

    try {
      if (thread?.thread_id) {
        // Resume LangGraph state machine with approved response
        await api.resumeAgent(thread.thread_id, editedResponse)
        setActionMessage('Response approved and LangGraph workflow resumed successfully!')
      } else {
        // Direct approval update
        await api.approveResponse({
          ticket_id: ticket.ticket_id,
          final_response: editedResponse,
          status: 'Resolved',
          resolution_state: 'Closed',
          resolved_by: isAgentOrAdmin ? 'AI+Human' : 'Human'
        })
        setActionMessage('Ticket successfully updated and resolved!')
      }

      if (onUpdated) onUpdated()
      setTimeout(() => {
        onClose()
      }, 1200)
    } catch (err) {
      setErrorMsg(err.message || 'Failed to approve response')
    } finally {
      setSubmitting(false)
    }
  }

  if (!ticket) return null

  const isHumanReview = ticket.status === 'Human Review'
  const isResolved = ticket.status === 'Resolved'

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card modal-lg" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="modal-header">
          <div className="modal-header-info">
            <div className="ticket-id-tag">🎫 {ticket.ticket_id}</div>
            <h2 className="modal-title">{ticket.title_query}</h2>
            <div className="modal-meta-line">
              <span>Tenant: <strong>{ticket.tenant_id}</strong></span>
              <span className="bullet">&bull;</span>
              <span>Customer: <strong>{ticket.username}</strong></span>
              <span className="bullet">&bull;</span>
              <span>Category: <strong>{ticket.category || 'General'}</strong></span>
              <span className="bullet">&bull;</span>
              <span>Priority: <strong>{ticket.priority}</strong></span>
            </div>
          </div>
          <button className="btn btn-icon" onClick={onClose}><X size={20} /></button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {actionMessage && (
            <div className="alert-success">
              <CheckCircle size={18} />
              <span>{actionMessage}</span>
            </div>
          )}

          {errorMsg && (
            <div className="alert-error">
              <AlertCircle size={18} />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Status & Confidence Banner */}
          <div className="detail-banner">
            <div className="banner-item">
              <span className="banner-label">Current Status</span>
              <span className={`badge badge-lg ${
                ticket.status === 'Resolved' ? 'badge-success' :
                ticket.status === 'Human Review' ? 'badge-warning' :
                ticket.status === 'AI Processing' ? 'badge-info' : 'badge-danger'
              }`}>
                {ticket.status}
              </span>
            </div>

            <div className="banner-item">
              <span className="banner-label">Resolution State</span>
              <strong className="text-highlight">{ticket.resolution_state || 'Open'}</strong>
            </div>

            <div className="banner-item">
              <span className="banner-label">AI Confidence</span>
              <strong className={ticket.ai_confidence >= 75 ? 'text-green' : 'text-yellow'}>
                {ticket.ai_confidence !== null ? `${ticket.ai_confidence}%` : 'N/A'}
              </strong>
            </div>

            <div className="banner-item">
              <span className="banner-label">Resolved By</span>
              <strong>{ticket.resolved_by || 'Pending'}</strong>
            </div>
          </div>

          {/* Customer Description */}
          <div className="detail-section">
            <h4 className="section-title">
              <User size={16} />
              <span>Customer Inquiry Description</span>
            </h4>
            <div className="bubble bubble-user">
              <p>{ticket.ticket_description || ticket.title_query}</p>
            </div>
          </div>

          {/* AI Draft & Retrieval */}
          {ticket.ai_response && (
            <div className="detail-section">
              <h4 className="section-title">
                <Bot size={16} />
                <span>AI Generated Draft Response</span>
                {ticket.ai_confidence < 75 && (
                  <span className="badge badge-warning badge-sm">Low Confidence &mdash; Review Required</span>
                )}
              </h4>
              <div className="bubble bubble-ai">
                <p>{ticket.ai_response}</p>
              </div>
            </div>
          )}

          {/* Retrieved Knowledge Base Chunks */}
          {ticket.retrieved_documents && ticket.retrieved_documents.length > 0 && (
            <div className="detail-section">
              <h4 className="section-title">
                <FileText size={16} />
                <span>Retrieved Knowledge Base Context ({ticket.retrieved_documents.length} docs)</span>
              </h4>
              <div className="retrieved-docs-list">
                {ticket.retrieved_documents.map((doc, idx) => (
                  <div key={idx} className="doc-item">
                    <span className="doc-num">#{idx + 1}</span>
                    <span className="doc-text">{typeof doc === 'string' ? doc : JSON.stringify(doc)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Active LangGraph Thread Tracker */}
          {thread && (
            <div className="detail-section thread-card">
              <h4 className="section-title">
                <Sparkles size={16} />
                <span>LangGraph State Machine Thread</span>
              </h4>
              <div className="thread-meta">
                <div>Thread ID: <code>{thread.thread_id}</code></div>
                <div>Current Node: <span className="badge badge-info">{thread.current_node}</span></div>
                <div>Status: <span className="badge badge-warning">{thread.status}</span></div>
                {thread.interrupt_reason && (
                  <div className="interrupt-reason">Interrupt Reason: {thread.interrupt_reason}</div>
                )}
              </div>
            </div>
          )}

          {/* HITL Review & Approval Section */}
          <div className="detail-section approval-box">
            <h4 className="section-title">
              <Shield size={16} />
              <span>{isResolved ? 'Final Approved Response' : 'Human-in-the-Loop Review & Approval'}</span>
            </h4>

            {isResolved ? (
              <div className="bubble bubble-resolved">
                <p>{ticket.final_response || ticket.ai_response}</p>
              </div>
            ) : (
              <div>
                <p className="approval-instruction">
                  Review the drafted AI response below. You can modify or refine the response before sending it to the user and resuming the LangGraph workflow.
                </p>
                <textarea
                  className="approval-textarea"
                  rows={5}
                  value={editedResponse}
                  onChange={(e) => setEditedResponse(e.target.value)}
                  placeholder="Review or edit response here..."
                />

                <div className="approval-actions">
                  <button
                    className="btn btn-primary"
                    onClick={handleApprove}
                    disabled={submitting}
                  >
                    <Send size={16} />
                    <span>{submitting ? 'Approving & Resuming...' : 'Approve & Deliver Response'}</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
