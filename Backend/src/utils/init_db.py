import logging
from sqlalchemy import inspect, text
from src.database import engine, Base, SessionLocal
from src.models.Users import User
from src.models.Tickets import Ticket
from src.models.Threads import Thread
from src.models.EpisodicMemory import EpisodicMemory
from src.models.TicketMessage import TicketMessage
from src.models.TicketNote import TicketNote
from src.seed import seed_users, seed_tickets

logger = logging.getLogger(__name__)

def run_migrations():
    """Ensure newly added columns exist in both SQLite and PostgreSQL schemas."""
    inspector = inspect(engine)
    with engine.connect() as conn:
        if inspector.has_table("users"):
            user_cols = {c["name"] for c in inspector.get_columns("users")}
            if "role" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'Customer'"))
            if "tenant_id" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN tenant_id VARCHAR(50) DEFAULT 'default'"))
            if "is_guest" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_guest BOOLEAN DEFAULT FALSE"))
            if "expires_at" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN expires_at TIMESTAMP"))
            if "created_at" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN created_at TIMESTAMP"))
            if "updated_at" not in user_cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP"))

        if inspector.has_table("tickets"):
            ticket_cols = {c["name"] for c in inspector.get_columns("tickets")}
            if "tenant_id" not in ticket_cols:
                conn.execute(text("ALTER TABLE tickets ADD COLUMN tenant_id VARCHAR(50) DEFAULT 'default'"))

        if inspector.has_table("threads"):
            thread_cols = {c["name"] for c in inspector.get_columns("threads")}
            if "tenant_id" not in thread_cols:
                conn.execute(text("ALTER TABLE threads ADD COLUMN tenant_id VARCHAR(50) DEFAULT 'default'"))

        conn.commit()

def init_db():
    # 1. Create tables if not present
    Base.metadata.create_all(bind=engine)

    # 2. Apply column migrations if database already existed
    try:
        run_migrations()
    except Exception as e:
        logger.warning(f"Migration check encountered note: {e}")

    # 3. Seed users & tickets
    db = SessionLocal()
    try:
        seed_users(db)

        existing_ticket = db.query(Ticket).first()
        if not existing_ticket:
            logger.info("Seeding tickets...")
            seed_tickets(db)
            logger.info("Database initialized & seeded successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()
