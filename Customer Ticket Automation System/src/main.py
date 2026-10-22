import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.utils.init_db import init_db
from src.routes import auth, tickets, agent, threads

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize and seed database if necessary
    logger.info("Application starting up: initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")
    yield
    # Shutdown
    logger.info("Application shutting down.")

app = FastAPI(
    title="Agentic Customer Ticket Resolution API",
    description="Production-grade AI agent system for customer ticket resolution and human-in-the-loop escalation.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration from Settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(agent.router)
app.include_router(threads.router)

@app.get("/health", tags=["Monitoring"])
def health_check():
    """Health check probe."""
    return {"status": "healthy", "service": "ticket-agent-api"}

@app.get("/ready", tags=["Monitoring"])
def readiness_check():
    """Readiness probe checking database connectivity."""
    from src.database import engine
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "degraded", "database": str(e)}
