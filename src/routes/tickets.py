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
from src.models.TicketMessage import TicketMessage
from src.models.TicketNote import TicketNote
from src.services.ticket_service import TicketService
from src.services.memory_service import MemoryService
from src.schemas.ticket import (
    TicketCreateRequest,
    TicketResponse,
    TicketApproveRequest,
    MessageCreateRequest,
    MessageResponse,
    NoteCreateRequest,
    NoteResponse
)

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


# =========================================================================
# Persistent Conversation Messages & Admin Notes (PostgreSQL / DB Backed)
# =========================================================================

@router.get("/{ticket_id}/messages", response_model=List[MessageResponse])
def get_ticket_messages(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full persistent chat conversation history from database across browsers/devices."""
    is_agent = current_user.role in AGENT_ROLES
    ticket = TicketService.get_scoped_ticket_by_id(
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        is_agent_or_admin=is_agent,
        db=db
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or access denied")

    messages = (
        db.query(TicketMessage)
        .filter(TicketMessage.ticket_id == ticket_id, TicketMessage.tenant_id == current_user.tenant_id)
        .order_by(TicketMessage.created_at.asc())
        .all()
    )
    return messages


@router.post("/{ticket_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_message(
    ticket_id: str,
    payload: MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Persist a new chat message to the database with sender identity, role, and tenant isolation."""
    is_agent = current_user.role in AGENT_ROLES
    ticket = TicketService.get_scoped_ticket_by_id(
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        user_id=current_user.user_id,
        is_agent_or_admin=is_agent,
        db=db
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or access denied")

    message_id = f"MSG{uuid.uuid4().hex[:8].upper()}"
    new_msg = TicketMessage(
        message_id=message_id,
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        sender_id=current_user.user_id,
        sender_name=current_user.fullname or current_user.username,
        sender_role=current_user.role,
        content=payload.content.strip()
    )
    db.add(new_msg)
    db.commit()
    db.refresh(new_msg)

    # Automatically record in episodic memory
    try:
        MemoryService.record_interaction(
            tenant_id=current_user.tenant_id,
            user_id=ticket.user_id,
            ticket_id=ticket_id,
            summary=f"Chat ({new_msg.sender_role} {new_msg.sender_name}): {new_msg.content[:200]}",
            memory_type="chat_interaction",
            db=db
        )
    except Exception as e:
        logger.warning(f"Could not record chat memory: {e}")

    return new_msg


@router.get("/{ticket_id}/notes", response_model=List[NoteResponse])
def get_ticket_notes(
    ticket_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_agent)
):
    """Retrieve persistent internal staff and admin notes for a ticket (Staff Only)."""
    ticket = TicketService.get_scoped_ticket_by_id(
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        is_agent_or_admin=True,
        db=db
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    notes = (
        db.query(TicketNote)
        .filter(TicketNote.ticket_id == ticket_id, TicketNote.tenant_id == current_user.tenant_id)
        .order_by(TicketNote.created_at.desc())
        .all()
    )
    return notes


@router.post("/{ticket_id}/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_note(
    ticket_id: str,
    payload: NoteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_agent)
):
    """Persist an internal note to the database for administrative coordination (Staff Only)."""
    ticket = TicketService.get_scoped_ticket_by_id(
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        is_agent_or_admin=True,
        db=db
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    note_id = f"NOTE{uuid.uuid4().hex[:8].upper()}"
    new_note = TicketNote(
        note_id=note_id,
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        author_id=current_user.user_id,
        author_name=current_user.fullname or current_user.username,
        author_role=current_user.role,
        content=payload.content.strip()
    )
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

