import logging
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database import get_db
from src.dependencies import get_current_user, get_current_active_agent, AGENT_ROLES
from src.models.Users import User
from src.services.ticket_service import TicketService
from src.schemas.ticket import TicketCreateRequest, TicketResponse, TicketApproveRequest

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

class InsertHumanEscalation(BaseModel):
    ticket_id: str
    user_id: Optional[str] = None
    username: Optional[str] = None
    category: str
    title_query: str
    ticket_description: str
    status: str = "Manual Handling"
    created_at: Optional[datetime] = None
    intent: str
    priority: str
    resolution_state: str = "In Progress"
    resolved_by: Optional[str] = "Human"

class InsertHumanReview(InsertHumanEscalation):
    ai_response: str
    ai_confidence: float
    retrieved_documents: List[str]

class InsertResolved(InsertHumanReview):
    final_response: str

class UpdateApprovedResponse(BaseModel):
    ticket_id: str
    status: str = "Resolved"
    resolution_state: str = "Closed"
    final_response: str
    resolved_by: str = "AI+Human"


@router.get("", response_model=List[TicketResponse])
@router.get("/", response_model=List[TicketResponse])
def get_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch tickets strictly scoped to the user's tenant and role."""
    is_agent = current_user.role in AGENT_ROLES
    tickets = TicketService.get_scoped_tickets(
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        is_agent_or_admin=is_agent,
        db=db
    )
    return tickets


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve single ticket with tenant & user ownership enforcement."""
    is_agent = current_user.role in AGENT_ROLES
    ticket = TicketService.get_scoped_ticket_by_id(
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        is_agent_or_admin=is_agent,
        db=db
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found or access denied"
        )
    return ticket


@router.post("/create", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    payload: TicketCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new ticket bound to the caller's verified identity and tenant."""
    ticket_id = f"TCK{uuid.uuid4().hex[:6].upper()}"
    ticket = TicketService.record_human_escalation(
        ticket_id=ticket_id,
        user_id=current_user.user_id,
        username=current_user.username,
        category=payload.category or "Support",
        title_query=payload.title_query,
        ticket_description=payload.ticket_description or "",
        intent="Support Request",
        priority=payload.priority or "Medium",
        tenant_id=current_user.tenant_id,
        db=db
    )
    return ticket


@router.post("/update")
def update_ticket_response(
    ticket_id: str = Form(...),
    final_response: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_agent)
):
    updated = TicketService.record_approved_response(
        ticket_id=ticket_id,
        final_response=final_response,
        status="Resolved",
        resolution_state="Closed",
        resolved_by="AI+Human",
        db=db
    )
    if not updated:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"status": "Updated", "ticket_id": ticket_id}


@router.post("/update/human_eval")
def escalate_ticket_to_human(
    payload: InsertHumanEscalation,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = TicketService.record_human_escalation(
        ticket_id=payload.ticket_id,
        user_id=payload.user_id or current_user.user_id,
        username=payload.username or current_user.username,
        category=payload.category,
        title_query=payload.title_query,
        ticket_description=payload.ticket_description,
        intent=payload.intent,
        priority=payload.priority,
        tenant_id=current_user.tenant_id,
        created_at=payload.created_at,
        db=db
    )
    return {
        "message": "Ticket escalated to human evaluation successfully",
        "ticket_id": ticket.ticket_id
    }


@router.post("/update/human_review")
def escalate_ticket_to_human_review(
    payload: InsertHumanReview,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = TicketService.record_human_review(
        ticket_id=payload.ticket_id,
        user_id=payload.user_id or current_user.user_id,
        username=payload.username or current_user.username,
        category=payload.category,
        title_query=payload.title_query,
        ticket_description=payload.ticket_description,
        intent=payload.intent,
        priority=payload.priority,
        ai_response=payload.ai_response,
        ai_confidence=payload.ai_confidence,
        retrieved_documents=payload.retrieved_documents,
        tenant_id=current_user.tenant_id,
        created_at=payload.created_at,
        db=db
    )
    return {
        "message": "Ticket marked for human review successfully",
        "ticket_id": ticket.ticket_id
    }


@router.post("/update/auto_resolve")
def auto_resolve_ticket(
    payload: InsertResolved,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ticket = TicketService.record_auto_resolution(
        ticket_id=payload.ticket_id,
        user_id=payload.user_id or current_user.user_id,
        username=payload.username or current_user.username,
        category=payload.category,
        title_query=payload.title_query,
        ticket_description=payload.ticket_description,
        intent=payload.intent,
        priority=payload.priority,
        ai_response=payload.ai_response,
        ai_confidence=payload.ai_confidence,
        retrieved_documents=payload.retrieved_documents,
        final_response=payload.final_response,
        tenant_id=current_user.tenant_id,
        created_at=payload.created_at,
        db=db
    )
    return {
        "message": "Ticket auto-resolved successfully",
        "ticket_id": ticket.ticket_id
    }


@router.patch("/update/approved_response")
def update_approved_response(
    payload: UpdateApprovedResponse,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_agent)
):
    ticket = TicketService.record_approved_response(
        ticket_id=payload.ticket_id,
        final_response=payload.final_response,
        status=payload.status,
        resolution_state=payload.resolution_state,
        resolved_by=payload.resolved_by,
        db=db
    )
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    return {"message": "Ticket updated successfully", "ticket_id": ticket.ticket_id}
