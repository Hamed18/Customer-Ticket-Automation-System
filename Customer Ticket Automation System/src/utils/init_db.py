from src.database import engine, Base, SessionLocal
from src.models.Users import User
from src.models.Tickets import Ticket
from src.models.Threads import Thread
from src.seed import seed_users, seed_tickets
import logging

logger = logging.getLogger(__name__)

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if users already exist
        existing_user = db.query(User).first()
        if existing_user:
            logger.info("Database already initialized, skipping seed.")
            return

        logger.info("Seeding database...")
        seed_users(db)
        seed_tickets(db)
        logger.info("Database seeded successfully")
    except Exception as e:
        db.rollback()
        logger.error(f"Error during database initialization: {e}")
        raise
    finally:
        db.close()
