import React, { useState } from 'react'
import { AuthProvider, useAuth } from './context/AuthContext'
import { Navbar } from './components/Navbar'
import { AuthView } from './components/AuthView'
import { TicketDashboard } from './components/TicketDashboard'
import { TicketDetailsModal } from './components/TicketDetailsModal'
import { CreateTicketModal } from './components/CreateTicketModal'

const MainContent = () => {
  const { isAuthenticated } = useAuth()
  const [selectedTicket, setSelectedTicket] = useState(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  if (!isAuthenticated) {
    return <AuthView />
  }

  return (
    <div className="app-layout">
      <Navbar onOpenCreate={() => setShowCreateModal(true)} />

      <main className="main-content">
        <TicketDashboard
          key={refreshTrigger}
          onSelectTicket={(ticket) => setSelectedTicket(ticket)}
          onOpenCreate={() => setShowCreateModal(true)}
        />
      </main>

      {selectedTicket && (
        <TicketDetailsModal
          ticket={selectedTicket}
          onClose={() => setSelectedTicket(null)}
          onUpdated={() => setRefreshTrigger(prev => prev + 1)}
        />
      )}

      {showCreateModal && (
        <CreateTicketModal
          onClose={() => setShowCreateModal(false)}
          onCreated={() => setRefreshTrigger(prev => prev + 1)}
        />
      )}
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <MainContent />
    </AuthProvider>
  )
}
