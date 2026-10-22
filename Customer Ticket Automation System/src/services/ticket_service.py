import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.database import get_db_context
from src.models.Tickets import Ticket
from src.repositories.ticket_repository import TicketRepository

logger = logging.getLogger(__name__)

class TicketService:
    @staticmethod
    def get_all_tickets(db: Optional[Session] = None) -> List[Ticket]:
        if db is not None:
            return TicketRepository.get_all(db)
        with get_db_context() as session:
            return TicketRepository.get_all(session)

    @staticmethod
    def get_ticket_by_id(ticket_id: str, db: Optional[Session] = None) -> Optional[Ticket]:
        if db is not None:
            return TicketRepository.get_by_id(db, ticket_id)
        with get_db_context() as session:
            return TicketRepository.get_by_id(session, ticket_id)

    @staticmethod
    def record_human_escalation(
        ticket_id: str,
        user_id: str,
        username: str,
        category: str,
        title_query: str,
        ticket_description: str,
        intent: str,
        priority: str,
        created_at: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Ticket:
        data = {
            "ticket_id": ticket_id,
            "user_id": user_id,
            "username": username,
            "category": category,
            "title_query": title_query,
            "ticket_description": ticket_description,
            "status": "Manual Handling",
            "created_at": created_at or datetime.now(timezone.utc),
            "intent": intent,
            "priority": priority,
            "resolution_state": "In Progress",
            "resolved_by": "Human"
        }
        logger.info(f"Escalating ticket {ticket_id} to manual human handling")
        if db is not None:
            return TicketRepository.upsert(db, data)
        with get_db_context() as session:
            return TicketRepository.upsert(session, data)

    @staticmethod
    def record_human_review(
        ticket_id: str,
        user_id: str,
        username: str,
        category: str,
        title_query: str,
        ticket_description: str,
        intent: str,
        priority: str,
        ai_response: str,
        ai_confidence: float,
        retrieved_documents: List[str],
        created_at: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Ticket:
        data = {
            "ticket_id": ticket_id,
            "user_id": user_id,
            "username": username,
            "category": category,
            "title_query": title_query,
            "ticket_description": ticket_description,
            "status": "Human Review",
            "created_at": created_at or datetime.now(timezone.utc),
            "intent": intent,
            "priority": priority,
            "resolution_state": "Needs Review",
            "ai_response": ai_response,
            "ai_confidence": ai_confidence,
            "retrieved_documents": retrieved_documents,
            "resolved_by": None
        }
        logger.info(f"Flagging ticket {ticket_id} for human review (confidence: {ai_confidence})")
        if db is not None:
            return TicketRepository.upsert(db, data)
        with get_db_context() as session:
            return TicketRepository.upsert(session, data)

    @staticmethod
    def record_auto_resolution(
        ticket_id: str,
        user_id: str,
        username: str,
        category: str,
        title_query: str,
        ticket_description: str,
        intent: str,
        priority: str,
        ai_response: str,
        ai_confidence: float,
        retrieved_documents: List[str],
        final_response: str,
        created_at: Optional[datetime] = None,
        db: Optional[Session] = None
    ) -> Ticket:
        data = {
            "ticket_id": ticket_id,
            "user_id": user_id,
            "username": username,
            "category": category,
            "title_query": title_query,
            "ticket_description": ticket_description,
            "status": "Resolved",
            "created_at": created_at or datetime.now(timezone.utc),
            "intent": intent,
            "priority": priority,
            "resolution_state": "Closed",
            "ai_response": ai_response,
            "ai_confidence": ai_confidence,
            "retrieved_documents": retrieved_documents,
            "final_response": final_response,
            "resolved_by": "AI"
        }
        logger.info(f"Auto-resolving ticket {ticket_id} via AI")
        if db is not None:
            return TicketRepository.upsert(db, data)
        with get_db_context() as session:
            return TicketRepository.upsert(session, data)

    @staticmethod
    def record_approved_response(
        ticket_id: str,
        final_response: str,
        status: str = "Resolved",
        resolution_state: str = "Closed",
        resolved_by: str = "AI+Human",
        db: Optional[Session] = None
    ) -> Optional[Ticket]:
        updates = {
            "final_response": final_response,
            "status": status,
            "resolution_state": resolution_state,
            "resolved_by": resolved_by
        }
        logger.info(f"Applying approved response to ticket {ticket_id}")
        if db is not None:
            return TicketRepository.update(db, ticket_id, updates)
        with get_db_context() as session:
            return TicketRepository.update(session, ticket_id, updates)
