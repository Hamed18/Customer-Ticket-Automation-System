import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from src.database import get_db
from src.utils.jwt_handler import get_current_user
from src.services.thread_service import ThreadService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/threads",
    tags=["Threads"]
)

class NewThread(BaseModel):
    thread_id: str
    ticket_id: str
    current_node: str = "Human Review"
    current_state: Dict[str, Any]
    status: str = "Running"
    interrupt_reason: str = "Low confidence flagged for review"
    last_run_at: Optional[datetime] = None

class UpdateThread(BaseModel):
    thread_id: str
    current_node: str = "send_approved_response"
    status: str = "Running"
    resume_answer: str
    last_run_at: Optional[datetime] = None


@router.get("/thread")
def get_thread(
    ticket_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    thread = ThreadService.get_thread_by_ticket(ticket_id, db=db)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found for the given ticket_id"
        )
    return {"thread_id": thread.thread_id, "ticket_id": thread.ticket_id, "status": thread.status}


@router.post("/insert")
def insert_thread(
    new_thread: NewThread,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    thread = ThreadService.save_thread(
        thread_id=new_thread.thread_id,
        ticket_id=new_thread.ticket_id,
        current_state=new_thread.current_state,
        current_node=new_thread.current_node,
        status=new_thread.status,
        interrupt_reason=new_thread.interrupt_reason,
        db=db
    )
    return {
        "message": "Thread inserted successfully",
        "thread_id": thread.thread_id,
        "ticket_id": thread.ticket_id
    }


@router.patch("/update/thread")
def update_thread_state(
    payload: UpdateThread,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    thread = ThreadService.resolve_thread(
        thread_id=payload.thread_id,
        resume_answer=payload.resume_answer,
        current_node=payload.current_node,
        status=payload.status,
        db=db
    )
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    return {
        "message": "Thread updated successfully",
        "thread_id": thread.thread_id
    }
