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
  const [activeTab, setActiveTab] = useState('details') // 'details' | 'chat' | 'notes'
  const [thread, setThread] = useState(null)
  const [memories, setMemories] = useState([])
  const [loadingMemories, setLoadingMemories] = useState(false)

  // Persistent Messages (PostgreSQL)
  const [messages, setMessages] = useState([])
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [sendingMsg, setSendingMsg] = useState(false)

  // Persistent Internal Notes (PostgreSQL)
  const [notes, setNotes] = useState([])
  const [loadingNotes, setLoadingNotes] = useState(false)
  const [noteInput, setNoteInput] = useState('')
  const [addingNote, setAddingNote] = useState(false)

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
    fetchMemories()
    fetchMessages()
    if (isAgentOrAdmin) {
      fetchNotes()
    }
  }, [ticket])

  const fetchThread = async () => {
    if (!ticket?.ticket_id) return
    try {
      const data = await api.getThread(ticket.ticket_id)
      setThread(data)
    } catch {
      setThread(null)
    }
  }

  const fetchMemories = async () => {
    if (!ticket?.user_id) return
    setLoadingMemories(true)
    try {
      const data = await api.getMemories(ticket.user_id)
      setMemories(Array.isArray(data) ? data : [])
    } catch {
      setMemories([])
    } finally {
      setLoadingMemories(false)
    }
  }

  const fetchMessages = async () => {
    if (!ticket?.ticket_id) return
    setLoadingMessages(true)
    try {
      const data = await api.getTicketMessages(ticket.ticket_id)
      setMessages(Array.isArray(data) ? data : [])
    } catch (err) {
      console.warn('Could not load messages from DB:', err)
      setMessages([])
    } finally {
      setLoadingMessages(false)
    }
  }

  const fetchNotes = async () => {
    if (!ticket?.ticket_id) return
    setLoadingNotes(true)
    try {
      const data = await api.getTicketNotes(ticket.ticket_id)
      setNotes(Array.isArray(data) ? data : [])
    } catch (err) {
      console.warn('Could not load notes from DB:', err)
      setNotes([])
    } finally {
      setLoadingNotes(false)
    }
  }

  const handleSendMessage = async (e) => {
    e.preventDefault()
    if (!chatInput.trim() || sendingMsg) return
    setSendingMsg(true)
    try {
      const msg = await api.sendTicketMessage(ticket.ticket_id, chatInput.trim())
      setMessages(prev => [...prev, msg])
      setChatInput('')
    } catch (err) {
      setErrorMsg(`Failed to send message: ${err.message}`)
    } finally {
      setSendingMsg(false)
    }
  }

  const handleAddNote = async (e) => {
    e.preventDefault()
    if (!noteInput.trim() || addingNote) return
    setAddingNote(true)
    try {
      const note = await api.addTicketNote(ticket.ticket_id, noteInput.trim())
      setNotes(prev => [note, ...prev])
      setNoteInput('')
    } catch (err) {
      setErrorMsg(`Failed to save note: ${err.message}`)
    } finally {
      setAddingNote(false)
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
        await api.resumeAgent(thread.thread_id, editedResponse)
        setActionMessage('Response approved and LangGraph workflow resumed successfully! (Episodic memory recorded)')
      } else {
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
      }, 1500)
    } catch (err) {
      setErrorMsg(err.message || 'Failed to approve response')
    } finally {
      setSubmitting(false)
    }
  }

  if (!ticket) return null

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

        {/* Tab Navigation */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border-color)', padding: '0 24px', gap: '8px', background: 'rgba(15,23,42,0.3)' }}>
          <button
            className={`auth-tab ${activeTab === 'details' ? 'active' : ''}`}
            onClick={() => setActiveTab('details')}
            style={{ borderRadius: '6px 6px 0 0', padding: '10px 16px' }}
          >
            📋 Incident & AI Review
          </button>
          <button
            className={`auth-tab ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
            style={{ borderRadius: '6px 6px 0 0', padding: '10px 16px' }}
          >
            💬 Persistent Chat ({messages.length})
          </button>
          {isAgentOrAdmin && (
            <button
              className={`auth-tab ${activeTab === 'notes' ? 'active' : ''}`}
              onClick={() => setActiveTab('notes')}
              style={{ borderRadius: '6px 6px 0 0', padding: '10px 16px' }}
            >
              📝 Staff Notes ({notes.length})
            </button>
          )}
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

          {/* TAB 1: DETAILS & HITL APPROVAL */}
          {activeTab === 'details' && (
            <>
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

              {/* Episodic Memories for this customer */}
              <div className="detail-section">
                <h4 className="section-title">
                  <Sparkles size={16} />
                  <span>User Episodic Memory & Prior Interactions ({memories.length})</span>
                </h4>
                {loadingMemories ? (
                  <p className="text-muted">Loading interaction memories from database...</p>
                ) : memories.length === 0 ? (
                  <div className="doc-item">
                    <span className="text-muted">No prior episodic memories recorded for this customer in tenant {ticket.tenant_id}.</span>
                  </div>
                ) : (
                  <div className="retrieved-docs-list">
                    {memories.map((m, idx) => (
                      <div key={m.memory_id || idx} className="doc-item" style={{ borderLeft: '3px solid #6366f1' }}>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', width: '100%' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                            <span className="badge badge-info badge-sm">{m.memory_type}</span>
                            <span className="text-muted">{m.created_at ? new Date(m.created_at).toLocaleString() : ''}</span>
                          </div>
                          <span className="doc-text" style={{ marginTop: '4px' }}>{m.summary}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
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
            </>
          )}

          {/* TAB 2: PERSISTENT MULTI-TURN CHAT (DATABASE-BACKED) */}
          {activeTab === 'chat' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: 'rgba(99,102,241,0.08)', padding: '10px 14px', borderRadius: '8px', fontSize: '12px', color: '#c7d2fe' }}>
                🔒 <strong>Database-Backed Conversation:</strong> All messages are stored permanently in the PostgreSQL database. When any user or admin logs in from any browser, phone, or device, this conversation is completely restored.
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', minHeight: '260px', maxHeight: '420px', overflowY: 'auto', paddingRight: '4px' }}>
                {/* Initial Query */}
                <div className="bubble bubble-user" style={{ maxWidth: '85%' }}>
                  <div style={{ fontSize: '11px', opacity: 0.8, marginBottom: '4px' }}>
                    <strong>{ticket.username}</strong> (Customer Inquiry) &bull; {ticket.created_at ? new Date(ticket.created_at).toLocaleTimeString() : ''}
                  </div>
                  <p>{ticket.ticket_description || ticket.title_query}</p>
                </div>

                {/* AI initial response if available */}
                {ticket.ai_response && (
                  <div className="bubble bubble-ai" style={{ maxWidth: '85%', marginLeft: 'auto' }}>
                    <div style={{ fontSize: '11px', opacity: 0.8, marginBottom: '4px' }}>
                      <strong>🤖 AI Assistant</strong> &bull; Initial Draft
                    </div>
                    <p>{ticket.ai_response}</p>
                  </div>
                )}

                {/* DB-stored messages */}
                {messages.map((m) => {
                  const isMe = m.sender_id === user?.user_id
                  return (
                    <div
                      key={m.message_id}
                      className={isMe ? 'bubble bubble-user' : 'bubble bubble-ai'}
                      style={{
                        maxWidth: '85%',
                        marginLeft: isMe ? 'auto' : '0',
                        marginRight: isMe ? '0' : 'auto',
                        borderLeft: isMe ? '4px solid #3b82f6' : '4px solid #10b981'
                      }}
                    >
                      <div style={{ fontSize: '11px', opacity: 0.8, marginBottom: '4px', display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
                        <span><strong>{m.sender_name}</strong> ({m.sender_role})</span>
                        <span>{m.created_at ? new Date(m.created_at).toLocaleTimeString() : ''}</span>
                      </div>
                      <p style={{ whiteSpace: 'pre-wrap' }}>{m.content}</p>
                    </div>
                  )
                })}
              </div>

              {/* Chat Input */}
              <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
                <input
                  type="text"
                  placeholder="Type a message to reply on this ticket..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  style={{
                    flex: 1,
                    padding: '12px 14px',
                    borderRadius: '8px',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-color)',
                    color: 'white',
                    outline: 'none'
                  }}
                />
                <button type="submit" className="btn btn-primary" disabled={sendingMsg || !chatInput.trim()}>
                  <Send size={16} />
                  <span>{sendingMsg ? 'Sending...' : 'Send'}</span>
                </button>
              </form>
            </div>
          )}

          {/* TAB 3: PERSISTENT INTERNAL NOTES (STAFF ONLY) */}
          {activeTab === 'notes' && isAgentOrAdmin && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ background: 'rgba(245,158,11,0.1)', padding: '10px 14px', borderRadius: '8px', fontSize: '12px', color: '#fde68a' }}>
                🔒 <strong>Internal Staff & Admin Notes:</strong> Confidential notes visible only to Support Specialists, Lead Agents, and Admins. Persisted directly in PostgreSQL.
              </div>

              {/* Add Note Form */}
              <form onSubmit={handleAddNote} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <textarea
                  rows={3}
                  placeholder="Add an internal note (e.g. escalated to engineering team, verified billing ledger, customer follow-up required)..."
                  value={noteInput}
                  onChange={(e) => setNoteInput(e.target.value)}
                  style={{
                    padding: '10px 12px',
                    borderRadius: '8px',
                    background: 'var(--bg-primary)',
                    border: '1px solid var(--border-color)',
                    color: 'white',
                    outline: 'none',
                    fontSize: '13px'
                  }}
                />
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={addingNote || !noteInput.trim()}>
                    <span>{addingNote ? 'Saving...' : 'Add Internal Note'}</span>
                  </button>
                </div>
              </form>

              {/* Notes List */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '10px' }}>
                {loadingNotes ? (
                  <p className="text-muted">Loading internal notes from database...</p>
                ) : notes.length === 0 ? (
                  <div className="doc-item">
                    <span className="text-muted">No internal notes added yet for this ticket.</span>
                  </div>
                ) : (
                  notes.map((n) => (
                    <div key={n.note_id} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderLeft: '4px solid #f59e0b', padding: '12px 14px', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                        <span><strong>{n.author_name}</strong> ({n.author_role})</span>
                        <span>{n.created_at ? new Date(n.created_at).toLocaleString() : ''}</span>
                      </div>
                      <p style={{ fontSize: '13px', whiteSpace: 'pre-wrap', color: 'var(--text-primary)' }}>{n.content}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  )
}
