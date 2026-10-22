import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.database import get_db
from src.dependencies import oauth2_scheme
from src.utils.jwt_handler import get_current_user
from src.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)

class InputTicket(BaseModel):
    ticket_id: str
    user_id: str
    username: str
    title_query: str
    ticket_description: str
    token: Optional[str] = None

class ResumeGraph(BaseModel):
    thread_id: str
    final_response: str
    user_id: str
    username: str
    token: Optional[str] = None


@router.post("/execute")
def execute_ticket(
    input_ticket: InputTicket,
    db: Session = Depends(get_db),
    current_username: str = Depends(get_current_user),
    auth_token: str = Depends(oauth2_scheme)
):
    try:
        active_token = input_ticket.token or auth_token
        result = AgentService.execute_ticket(
            ticket_id=input_ticket.ticket_id,
            user_id=input_ticket.user_id,
            username=input_ticket.username,
            title_query=input_ticket.title_query,
            ticket_description=input_ticket.ticket_description,
            token=active_token,
            db=db
        )
        return result
    except Exception as e:
        logger.error(f"Failed to execute ticket {input_ticket.ticket_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent execution error: {str(e)}"
        )


@router.post("/resume")
def resume_graph(
    resume_ticket: ResumeGraph,
    db: Session = Depends(get_db),
    current_username: str = Depends(get_current_user),
    auth_token: str = Depends(oauth2_scheme)
):
    try:
        active_token = resume_ticket.token or auth_token
        result = AgentService.resume_ticket(
            thread_id=resume_ticket.thread_id,
            final_response=resume_ticket.final_response,
            user_id=resume_ticket.user_id,
            username=resume_ticket.username,
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
