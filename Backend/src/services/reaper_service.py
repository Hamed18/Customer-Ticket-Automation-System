import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from src.database import get_db_context
from src.models.Users import User
from src.models.Tickets import Ticket
from src.models.Threads import Thread
from src.models.EpisodicMemory import EpisodicMemory
from src.utils.jwt_handler import _clean_expired_revocations

logger = logging.getLogger("reaper")

class TTLReaperService:
    last_run_stats: Dict[str, Any] = {
        "last_run": None,
        "swept_guests": 0,
        "swept_tickets": 0,
        "swept_memories": 0
    }

    @staticmethod
    def run_sweep(db: Session) -> Dict[str, Any]:
        """Sweep and purge all expired guest sessions, temporary tickets, and memories."""
        now = datetime.now(timezone.utc)
        logger.info(f"TTL Reaper initiating sweep at {now.isoformat()}...")

        # 1. Clean in-memory token revocation cache
        _clean_expired_revocations()

        # 2. Query expired guests
        expired_guests: List[User] = (
            db.query(User)
            .filter(User.is_guest == True, User.expires_at != None, User.expires_at <= now)
            .all()
        )

        swept_guest_ids = [g.user_id for g in expired_guests]
        total_tickets_swept = 0
        total_memories_swept = 0

        if swept_guest_ids:
            # 3. Purge episodic memories
            total_memories_swept = (
                db.query(EpisodicMemory)
                .filter(EpisodicMemory.user_id.in_(swept_guest_ids))
                .delete(synchronize_session=False)
            )

            # 4. Find guest tickets to purge threads
            guest_tickets = (
                db.query(Ticket.ticket_id)
                .filter(Ticket.user_id.in_(swept_guest_ids))
                .all()
            )
            guest_ticket_ids = [t[0] for t in guest_tickets]

            if guest_ticket_ids:
                db.query(Thread).filter(Thread.ticket_id.in_(guest_ticket_ids)).delete(synchronize_session=False)
                total_tickets_swept = (
                    db.query(Ticket)
                    .filter(Ticket.ticket_id.in_(guest_ticket_ids))
                    .delete(synchronize_session=False)
                )

            # 5. Purge expired guest user records
            db.query(User).filter(User.user_id.in_(swept_guest_ids)).delete(synchronize_session=False)
            db.commit()

            logger.info(
                f"TTL Reaper completed: Purged {len(swept_guest_ids)} guest sessions, "
                f"{total_tickets_swept} tickets, {total_memories_swept} memories."
            )
        else:
            logger.info("TTL Reaper sweep completed: No expired sessions found.")

        stats = {
            "last_run": now.isoformat(),
            "swept_guests": len(swept_guest_ids),
            "swept_tickets": total_tickets_swept,
            "swept_memories": total_memories_swept,
            "purged_user_ids": swept_guest_ids
        }
        TTLReaperService.last_run_stats = stats
        return stats


async def reaper_background_worker(interval_seconds: int = 60):
    """Asynchronous background worker that periodically runs the TTL Reaper."""
    logger.info(f"Background TTL Reaper worker started (Interval: {interval_seconds}s)")
    try:
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                with get_db_context() as session:
                    TTLReaperService.run_sweep(session)
            except Exception as e:
                logger.error(f"Error during automated TTL Reaper sweep: {e}", exc_info=True)
    except asyncio.CancelledError:
        logger.info("Background TTL Reaper worker stopped gracefully.")
