from sqlalchemy import Column, String, Text, Boolean, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(50), primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    fullname = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    password_hash = Column(Text, nullable=True)
    mobile_number = Column(String(20), nullable=True)
    role = Column(String(50), default="Customer", nullable=False, index=True)
    tenant_id = Column(String(50), default="default", nullable=False, index=True)
    is_guest = Column(Boolean, default=False, nullable=False, index=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tickets = relationship("Ticket", back_populates="user", cascade="all, delete")
