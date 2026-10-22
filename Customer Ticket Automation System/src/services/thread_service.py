import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.database import get_db_context
from src.models.Threads import Thread
from src.repositories.thread_repository import ThreadRepository

logger = logging.getLogger(__name__)

class ThreadService:
    @staticmethod
    def get_thread_by_ticket(ticket_id: str, db: Optional[Session] = None) -> Optional[Thread]:
        if db is not None:
            return ThreadRepository.get_by_ticket_id(db, ticket_id)
        with get_db_context() as session:
            return ThreadRepository.get_by_ticket_id(session, ticket_id)

    @staticmethod
    def get_thread_by_id(thread_id: str, db: Optional[Session] = None) -> Optional[Thread]:
        if db is not None:
            return ThreadRepository.get_by_thread_id(db, thread_id)
        with get_db_context() as session:
            return ThreadRepository.get_by_thread_id(session, thread_id)

    @staticmethod
    def save_thread(
        thread_id: str,
        ticket_id: str,
        current_state: Dict[str, Any],
        current_node: str = "Human Review",
        status: str = "Running",
        interrupt_reason: str = "Low confidence flagged for review",
        resume_answer: Optional[str] = None,
        db: Optional[Session] = None
    ) -> Thread:
        data = {
            "thread_id": thread_id,
            "ticket_id": ticket_id,
            "current_node": current_node,
            "current_state": current_state,
            "status": status,
            "interrupt_reason": interrupt_reason,
            "resume_answer": resume_answer,
            "last_run_at": datetime.now(timezone.utc)
        }
        logger.info(f"Saving thread state for thread {thread_id} (ticket: {ticket_id})")
        if db is not None:
            return ThreadRepository.upsert(db, data)
        with get_db_context() as session:
            return ThreadRepository.upsert(session, data)

    @staticmethod
    def update_thread(
        thread_id: str,
        updates: Dict[str, Any],
        db: Optional[Session] = None
    ) -> Optional[Thread]:
        if "last_run_at" not in updates:
            updates["last_run_at"] = datetime.now(timezone.utc)
        logger.info(f"Updating thread {thread_id}")
        if db is not None:
            return ThreadRepository.update(db, thread_id, updates)
        with get_db_context() as session:
            return ThreadRepository.update(session, thread_id, updates)

    @staticmethod
    def resolve_thread(
        thread_id: str,
        resume_answer: str,
        current_node: str = "send_approved_response",
        status: str = "Resolved",
        db: Optional[Session] = None
    ) -> Optional[Thread]:
        updates = {
            "resume_answer": resume_answer,
            "current_node": current_node,
            "status": status,
            "last_run_at": datetime.now(timezone.utc)
        }
        return ThreadService.update_thread(thread_id, updates, db=db)
