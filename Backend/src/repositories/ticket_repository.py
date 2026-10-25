from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from src.models.Tickets import Ticket

class TicketRepository:
    @staticmethod
    def get_scoped_tickets(
        db: Session,
        tenant_id: str,
        user_id: Optional[str] = None,
        is_agent_or_admin: bool = False
    ) -> List[Ticket]:
        """Fetch tickets strictly isolated by tenant and user role."""
        query = db.query(Ticket)

        # Non-superadmin is always isolated by tenant
        if tenant_id != "*":
            query = query.filter(Ticket.tenant_id == tenant_id)

        # Customers and guests are strictly isolated to their own user_id
        if not is_agent_or_admin and user_id:
            query = query.filter(Ticket.user_id == user_id)

        return query.order_by(Ticket.created_at.desc()).all()

    @staticmethod
    def get_scoped_ticket_by_id(
        db: Session,
        ticket_id: str,
        tenant_id: str,
        user_id: Optional[str] = None,
        is_agent_or_admin: bool = False
    ) -> Optional[Ticket]:
        """Fetch a specific ticket ensuring tenant and authorization checks."""
        query = db.query(Ticket).filter(Ticket.ticket_id == ticket_id)

        if tenant_id != "*":
            query = query.filter(Ticket.tenant_id == tenant_id)

        if not is_agent_or_admin and user_id:
            query = query.filter(Ticket.user_id == user_id)

        return query.first()

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
