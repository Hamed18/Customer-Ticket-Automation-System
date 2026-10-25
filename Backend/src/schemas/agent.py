from pydantic import BaseModel, Field
from typing import Optional

class AgentExecuteRequest(BaseModel):
    ticket_id: Optional[str] = Field(None, description="Optional existing ticket ID or generated automatically")
    title_query: str = Field(..., description="Query or title describing the issue")
    ticket_description: Optional[str] = Field(None, description="Detailed problem description")

class AgentResumeRequest(BaseModel):
    thread_id: str = Field(..., description="Active thread ID to resume")
    final_response: str = Field(..., description="Approved or edited response")
