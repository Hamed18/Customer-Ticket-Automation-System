from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class TicketCreateRequest(BaseModel):
    title_query: str = Field(..., min_length=3, description="Incident or inquiry summary")
    ticket_description: Optional[str] = Field(None, description="Detailed problem description")
    category: Optional[str] = Field(None, description="Optional ticket category")
    priority: Optional[str] = Field("Medium", description="Urgency priority (Low, Medium, High)")

class TicketResponse(BaseModel):
    ticket_id: str
    tenant_id: str
    user_id: str
    username: str
    category: Optional[str] = None
    title_query: str
    ticket_description: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    intent: Optional[str] = None
    priority: Optional[str] = None
    ai_response: Optional[str] = None
    ai_confidence: Optional[float] = None
    retrieved_documents: Optional[List[Any]] = None
    final_response: Optional[str] = None
    resolution_state: Optional[str] = None
    resolved_by: Optional[str] = None

    class Config:
        from_attributes = True

class TicketApproveRequest(BaseModel):
    ticket_id: str
    final_response: str
    status: str = "Resolved"
    resolution_state: str = "Closed"
    resolved_by: str = "AI+Human"
