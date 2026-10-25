import uuid
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.database import get_db_context
from src.models.EpisodicMemory import EpisodicMemory
from src.repositories.memory_repository import MemoryRepository

logger = logging.getLogger(__name__)

class MemoryService:
    @staticmethod
    def record_interaction(
        tenant_id: str,
        user_id: str,
        summary: str,
        ticket_id: Optional[str] = None,
        memory_type: str = "interaction",
        importance_score: float = 1.0,
        db: Optional[Session] = None
    ) -> EpisodicMemory:
        memory_id = f"MEM{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Recording episodic memory {memory_id} for user {user_id} in tenant {tenant_id}")
        if db is not None:
            return MemoryRepository.add(
                db=db,
                memory_id=memory_id,
                tenant_id=tenant_id,
                user_id=user_id,
                summary=summary,
                memory_type=memory_type,
                ticket_id=ticket_id,
                importance_score=importance_score
            )
        with get_db_context() as session:
            return MemoryRepository.add(
                db=session,
                memory_id=memory_id,
                tenant_id=tenant_id,
                user_id=user_id,
                summary=summary,
                memory_type=memory_type,
                ticket_id=ticket_id,
                importance_score=importance_score
            )

    @staticmethod
    def record_ticket_resolution(
        tenant_id: str,
        user_id: str,
        ticket_id: str,
        title_query: str,
        final_response: str,
        category: Optional[str] = None,
        db: Optional[Session] = None
    ) -> EpisodicMemory:
        """Create a persistent resolution memory for future session recall."""
        summary = (
            f"Ticket {ticket_id} ({category or 'General'}): User reported '{title_query}'. "
            f"Resolution provided: '{final_response}'"
        )
        return MemoryService.record_interaction(
            tenant_id=tenant_id,
            user_id=user_id,
            ticket_id=ticket_id,
            summary=summary,
            memory_type="resolution_summary",
            importance_score=1.5,
            db=db
        )

    @staticmethod
    def retrieve_relevant_memory(
        tenant_id: str,
        user_id: str,
        current_query: str,
        limit: int = 3,
        db: Optional[Session] = None
    ) -> List[str]:
        """Retrieve relevant past interactions as formatted strings for LLM injection."""
        if db is not None:
            memories = MemoryRepository.search_relevant(db, tenant_id, user_id, current_query, limit)
        else:
            with get_db_context() as session:
                memories = MemoryRepository.search_relevant(session, tenant_id, user_id, current_query, limit)

        return [mem.summary for mem in memories]

    @staticmethod
    def get_user_memories(
        tenant_id: str,
        user_id: str,
        limit: int = 10,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """Fetch memories for user profile or agent inspection UI."""
        if db is not None:
            mems = MemoryRepository.get_scoped_memories(db, tenant_id, user_id, limit)
        else:
            with get_db_context() as session:
                mems = MemoryRepository.get_scoped_memories(session, tenant_id, user_id, limit)

        return [
            {
                "memory_id": m.memory_id,
                "ticket_id": m.ticket_id,
                "memory_type": m.memory_type,
                "summary": m.summary,
                "importance_score": m.importance_score,
                "created_at": m.created_at.isoformat() if m.created_at else None
            }
            for m in mems
        ]
