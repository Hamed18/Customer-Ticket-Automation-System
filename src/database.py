import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from contextlib import contextmanager
from src.config import settings

logger = logging.getLogger("database")

def create_db_engine():
    db_url = settings.DATABASE_URL
    if "postgresql" in db_url:
        try:
            test_engine = create_engine(db_url, pool_pre_ping=True)
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to PostgreSQL database successfully.")
            return test_engine
        except Exception as e:
            fallback_url = "sqlite:///./ticket_system.db"
            logger.warning(
                f"PostgreSQL connection failed ({e}). "
                f"Auto-falling back to local SQLite database ({fallback_url}) for local execution."
            )
            return create_engine(fallback_url, connect_args={"check_same_thread": False})
    elif "sqlite" in db_url:
        return create_engine(db_url, connect_args={"check_same_thread": False})
    return create_engine(db_url, pool_pre_ping=True)

engine = create_db_engine()

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager for database sessions outside of FastAPI request lifecycle."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
