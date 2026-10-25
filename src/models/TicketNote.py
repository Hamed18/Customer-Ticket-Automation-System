from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base

class TicketNote(Base):
    __tablename__ = "ticket_notes"

    note_id = Column(String(50), primary_key=True, index=True)
    ticket_id = Column(String(50), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(50), default="default", nullable=False, index=True)

    author_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    author_name = Column(String(100), nullable=False)
    author_role = Column(String(50), default="Support Specialist", nullable=False)

    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="notes")
    author = relationship("User")
