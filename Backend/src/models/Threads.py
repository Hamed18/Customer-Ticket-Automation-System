from sqlalchemy import Column, String, Text, ForeignKey, TIMESTAMP, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base

class Thread(Base):
    __tablename__ = "threads"

    thread_id = Column(String(50), primary_key=True, index=True)
    tenant_id = Column(String(50), default="default", nullable=False, index=True)
    ticket_id = Column(String(50), ForeignKey("tickets.ticket_id"), nullable=False, index=True)

    current_node = Column(String(100))
    current_state = Column(JSON)

    status = Column(String(30))

    interrupt_reason = Column(Text)
    resume_answer = Column(Text)

    last_run_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationship
    ticket = relationship("Ticket", back_populates="threads")
