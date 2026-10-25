from sqlalchemy import Column, String, Text, Float, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base

class EpisodicMemory(Base):
    __tablename__ = "episodic_memories"

    memory_id = Column(String(50), primary_key=True, index=True)
    tenant_id = Column(String(50), default="default", nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    ticket_id = Column(String(50), ForeignKey("tickets.ticket_id", ondelete="CASCADE"), nullable=True, index=True)

    memory_type = Column(String(50), default="interaction", nullable=False) # 'interaction', 'resolution_summary', 'preference'
    summary = Column(Text, nullable=False)
    importance_score = Column(Float, default=1.0)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="memories")
    ticket = relationship("Ticket", backref="memories")
