import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from contextlib import contextmanager
from src.config import settings

logger = logging.getLogger("database")

ACTIVE_DB_TYPE = "sqlite"
ACTIVE_DB_HOST = "local"

def create_db_engine():
    global ACTIVE_DB_TYPE, ACTIVE_DB_HOST
    db_url = settings.DATABASE_URL

    if "postgresql" in db_url:
        try:
            # Test direct connection to PostgreSQL
            test_engine = create_engine(db_url, pool_pre_ping=True)
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            ACTIVE_DB_TYPE = "postgresql"
            ACTIVE_DB_HOST = db_url.split("@")[-1] if "@" in db_url else "postgresql-server"
            logger.info(f"Connected to persistent PostgreSQL database successfully ({ACTIVE_DB_HOST}).")
            return test_engine
        except Exception as e:
            # Fallback path supports environment-configured persistent volume mount
            data_dir = os.getenv("DATA_DIR", ".")
            fallback_path = os.path.join(data_dir, "ticket_system.db")
            fallback_url = f"sqlite:///{fallback_path}"
            ACTIVE_DB_TYPE = "sqlite_fallback"
            ACTIVE_DB_HOST = fallback_path
            logger.warning(
                f"PostgreSQL connection failed ({e}). "
                f"Falling back to persistent SQLite storage at '{fallback_path}'."
            )
            return create_engine(fallback_url, connect_args={"check_same_thread": False})
    elif "sqlite" in db_url:
        ACTIVE_DB_TYPE = "sqlite"
        ACTIVE_DB_HOST = db_url.replace("sqlite:///", "")
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

def get_database_info():
    """Return database provider and host diagnostics."""
    return {
        "provider": ACTIVE_DB_TYPE,
        "location": ACTIVE_DB_HOST,
        "is_postgres": ACTIVE_DB_TYPE == "postgresql"
    }

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
