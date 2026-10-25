import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.EpisodicMemory import EpisodicMemory

class MemoryRepository:
    @staticmethod
    def add(
        db: Session,
        memory_id: str,
        tenant_id: str,
        user_id: str,
        summary: str,
        memory_type: str = "interaction",
        ticket_id: Optional[str] = None,
        importance_score: float = 1.0
    ) -> EpisodicMemory:
        memory = EpisodicMemory(
            memory_id=memory_id,
            tenant_id=tenant_id,
            user_id=user_id,
            ticket_id=ticket_id,
            memory_type=memory_type,
            summary=summary,
            importance_score=importance_score
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory

    @staticmethod
    def get_scoped_memories(
        db: Session,
        tenant_id: str,
        user_id: str,
        limit: int = 10
    ) -> List[EpisodicMemory]:
        """Fetch chronological episodic memories for a user, isolated by tenant."""
        query = db.query(EpisodicMemory).filter(
            EpisodicMemory.tenant_id == tenant_id,
            EpisodicMemory.user_id == user_id
        )
        return query.order_by(EpisodicMemory.created_at.desc()).limit(limit).all()

    @staticmethod
    def search_relevant(
        db: Session,
        tenant_id: str,
        user_id: str,
        query_text: str,
        limit: int = 3
    ) -> List[EpisodicMemory]:
        """
        Fast TF-IDF / term overlap matching algorithm with recency weighting.
        Runs in microsecond time without external vector store latency.
        """
        all_memories = MemoryRepository.get_scoped_memories(db, tenant_id, user_id, limit=25)
        if not all_memories:
            return []

        words = set(re.findall(r"\w+", query_text.lower()))
        if not words:
            return all_memories[:limit]

        scored = []
        for idx, mem in enumerate(all_memories):
            mem_words = set(re.findall(r"\w+", mem.summary.lower()))
            overlap = len(words.intersection(mem_words))

            # Recency bonus: recent memories get slight boost
            recency_weight = max(0.2, 1.0 - (idx * 0.05))
            score = (overlap * 2.0 + mem.importance_score) * recency_weight

            scored.append((score, mem))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

    @staticmethod
    def delete_by_user_id(db: Session, user_id: str) -> int:
        """Purge all episodic memories for a given user (used by TTL Reaper)."""
        deleted = db.query(EpisodicMemory).filter(EpisodicMemory.user_id == user_id).delete()
        db.commit()
        return deleted
