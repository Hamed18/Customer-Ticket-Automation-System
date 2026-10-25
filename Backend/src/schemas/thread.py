from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ThreadResponse(BaseModel):
    thread_id: str
    tenant_id: str
    ticket_id: str
    current_node: Optional[str] = None
    current_state: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    interrupt_reason: Optional[str] = None
    resume_answer: Optional[str] = None
    last_run_at: Optional[datetime] = None

    class Config:
        from_attributes = True
