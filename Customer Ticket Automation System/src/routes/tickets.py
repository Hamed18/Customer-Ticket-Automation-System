import logging
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Form, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.database import get_db
from src.utils.jwt_handler import get_current_user
from src.services.ticket_service import TicketService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

class InsertHumanEscalation(BaseModel):
    ticket_id: str
    user_id: str
    username: str
    category: str
    title_query: str
    ticket_description: str
    status: str
    created_at: Optional[datetime] = None
    intent: str
    priority: str
    resolution_state: str
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


@router.get("")
@router.get("/")
def get_tickets(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    tickets = TicketService.get_all_tickets(db)
    return tickets


@router.post("/update")
def update_ticket_response(
    ticket_id: str = Form(...),
    final_response: str = Form(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
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
    current_user: str = Depends(get_current_user)
):
    ticket = TicketService.record_human_escalation(
        ticket_id=payload.ticket_id,
        user_id=payload.user_id,
        username=payload.username,
        category=payload.category,
        title_query=payload.title_query,
        ticket_description=payload.ticket_description,
        intent=payload.intent,
        priority=payload.priority,
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
    current_user: str = Depends(get_current_user)
):
    ticket = TicketService.record_human_review(
        ticket_id=payload.ticket_id,
        user_id=payload.user_id,
        username=payload.username,
        category=payload.category,
        title_query=payload.title_query,
        ticket_description=payload.ticket_description,
        intent=payload.intent,
        priority=payload.priority,
        ai_response=payload.ai_response,
        ai_confidence=payload.ai_confidence,
        retrieved_documents=payload.retrieved_documents,
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
    current_user: str = Depends(get_current_user)
):
    ticket = TicketService.record_auto_resolution(
        ticket_id=payload.ticket_id,
        user_id=payload.user_id,
        username=payload.username,
        category=payload.category,
        title_query=payload.title_query,
        ticket_description=payload.ticket_description,
        intent=payload.intent,
        priority=payload.priority,
        ai_response=payload.ai_response,
        ai_confidence=payload.ai_confidence,
        retrieved_documents=payload.retrieved_documents,
        final_response=payload.final_response,
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
    current_user: str = Depends(get_current_user)
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
