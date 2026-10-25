from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base

class TicketMessage(Base):
    __tablename__ = "ticket_messages"

    message_id = Column(String(50), primary_key=True, index=True)
    ticket_id = Column(String(50), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(50), default="default", nullable=False, index=True)

    sender_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    sender_name = Column(String(100), nullable=False)
    sender_role = Column(String(50), default="Customer", nullable=False) # 'Customer', 'Lead Support Agent', 'Support Specialist', 'AI'

    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="messages")
    sender = relationship("User")
