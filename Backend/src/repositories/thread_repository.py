from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.Threads import Thread

class ThreadRepository:
    @staticmethod
    def get_scoped_by_ticket_id(db: Session, ticket_id: str, tenant_id: str) -> Optional[Thread]:
        query = db.query(Thread).filter(Thread.ticket_id == ticket_id)
        if tenant_id != "*":
            query = query.filter(Thread.tenant_id == tenant_id)
        return query.order_by(Thread.last_run_at.desc()).first()

    @staticmethod
    def get_by_ticket_id(db: Session, ticket_id: str) -> Optional[Thread]:
        return db.query(Thread).filter(Thread.ticket_id == ticket_id).order_by(Thread.last_run_at.desc()).first()

    @staticmethod
    def get_by_thread_id(db: Session, thread_id: str) -> Optional[Thread]:
        return db.query(Thread).filter(Thread.thread_id == thread_id).first()

    @staticmethod
    def upsert(db: Session, thread_data: Dict[str, Any]) -> Thread:
        thread_id = thread_data.get("thread_id")
        existing_thread = None
        if thread_id:
            existing_thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()

        if existing_thread:
            for key, value in thread_data.items():
                if hasattr(existing_thread, key) and value is not None:
                    setattr(existing_thread, key, value)
            db.commit()
            db.refresh(existing_thread)
            return existing_thread
        else:
            new_thread = Thread(**thread_data)
            db.add(new_thread)
            db.commit()
            db.refresh(new_thread)
            return new_thread

    @staticmethod
    def update(db: Session, thread_id: str, updates: Dict[str, Any]) -> Optional[Thread]:
        thread = db.query(Thread).filter(Thread.thread_id == thread_id).first()
        if not thread:
            return None

        for key, value in updates.items():
            if hasattr(thread, key):
                setattr(thread, key, value)

        db.commit()
        db.refresh(thread)
        return thread
