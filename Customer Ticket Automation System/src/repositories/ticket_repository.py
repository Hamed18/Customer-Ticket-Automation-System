from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.Tickets import Ticket

class TicketRepository:
    @staticmethod
    def get_all(db: Session) -> List[Ticket]:
        return db.query(Ticket).order_by(Ticket.created_at.desc()).all()

    @staticmethod
    def get_by_id(db: Session, ticket_id: str) -> Optional[Ticket]:
        return db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

    @staticmethod
    def upsert(db: Session, ticket_data: Dict[str, Any]) -> Ticket:
        ticket_id = ticket_data.get("ticket_id")
        existing_ticket = None
        if ticket_id:
            existing_ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()

        if existing_ticket:
            for key, value in ticket_data.items():
                if hasattr(existing_ticket, key) and value is not None:
                    setattr(existing_ticket, key, value)
            db.commit()
            db.refresh(existing_ticket)
            return existing_ticket
        else:
            new_ticket = Ticket(**ticket_data)
            db.add(new_ticket)
            db.commit()
            db.refresh(new_ticket)
            return new_ticket

    @staticmethod
    def update(db: Session, ticket_id: str, updates: Dict[str, Any]) -> Optional[Ticket]:
        ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not ticket:
            return None

        for key, value in updates.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)

        db.commit()
        db.refresh(ticket)
        return ticket
