from sqlalchemy import Column, String, Text, Float, ForeignKey, TIMESTAMP, CheckConstraint, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    ticket_id = Column(String(50), primary_key=True, index=True)
    tenant_id = Column(String(50), default="default", nullable=False, index=True)
    user_id = Column(String(50), ForeignKey("users.user_id"), nullable=False, index=True)
    username = Column(String(50), nullable=False)

    category = Column(String(50))
    title_query = Column(Text, nullable=False)
    ticket_description = Column(Text)

    status = Column(String(30), default="AI Processing")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    intent = Column(String(100))
    priority = Column(String(20), default="Medium")

    ai_response = Column(Text)
    ai_confidence = Column(Float)
    retrieved_documents = Column(JSON)

    final_response = Column(Text)
    resolution_state = Column(String(30), default="Open")
    resolved_by = Column(String(20))

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('Manual Handling','AI Processing','Human Review','Resolved')",
            name="check_status"
        ),
        CheckConstraint(
            "priority IN ('Low','Medium','High')",
            name="check_priority"
        ),
        CheckConstraint(
            "resolved_by IS NULL OR resolved_by IN ('AI','Human','AI+Human')",
            name="check_resolved_by"
        ),
    )

    # Relationships
    user = relationship("User", back_populates="tickets")
    threads = relationship("Thread", back_populates="ticket", cascade="all, delete")
