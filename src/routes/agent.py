import logging
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database import get_db
from src.dependencies import get_current_user, oauth2_scheme, AGENT_ROLES
from src.models.Users import User
from src.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)

class InputTicket(BaseModel):
    ticket_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    title_query: str
    ticket_description: Optional[str] = ""
    token: Optional[str] = None

class ResumeGraph(BaseModel):
    thread_id: str
    final_response: str
    ticket_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    token: Optional[str] = None


@router.post("/execute")
def execute_ticket(
    input_ticket: InputTicket,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    auth_token: str = Depends(oauth2_scheme)
):
    """Execute LangGraph workflow with strict tenant and authenticated user binding."""
    try:
        active_token = auth_token or input_ticket.token
        ticket_id = input_ticket.ticket_id or f"TCK{uuid.uuid4().hex[:6].upper()}"

        # Enforce authenticated identity - ignore untrusted client payload overrides
        result = AgentService.execute_ticket(
            ticket_id=ticket_id,
            user_id=current_user.user_id,
            username=current_user.username,
            title_query=input_ticket.title_query,
            ticket_description=input_ticket.ticket_description or "",
            token=active_token,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Failed to execute ticket for user {current_user.username}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution error: {str(e)}"
        )


@router.post("/resume")
def resume_graph(
    resume_ticket: ResumeGraph,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    auth_token: str = Depends(oauth2_scheme)
):
    """Resume an interrupted LangGraph HITL workflow."""
    try:
        active_token = auth_token or resume_ticket.token
        result = AgentService.resume_ticket(
            thread_id=resume_ticket.thread_id,
            final_response=resume_ticket.final_response,
            user_id=current_user.user_id,
            username=current_user.username,
            token=active_token,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Failed to resume thread {resume_ticket.thread_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent resume error: {str(e)}"
        )
