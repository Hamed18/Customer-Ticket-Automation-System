import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.utils.init_db import init_db
from src.routes import auth, tickets, agent, threads, memories, reaper
from src.services.reaper_service import reaper_background_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("api")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database and launch automated TTL Reaper background worker
    logger.info("Application starting up: initializing database...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization warning: {e}")

    # Start periodic background TTL Reaper worker
    reaper_task = asyncio.create_task(reaper_background_worker(interval_seconds=60))

    yield

    # Shutdown: cancel background worker gracefully
    logger.info("Application shutting down: stopping background reaper...")
    reaper_task.cancel()
    try:
        await reaper_task
    except asyncio.CancelledError:
        pass
    logger.info("Application shutdown complete.")

app = FastAPI(
    title="Agentic Customer Ticket Resolution API",
    description="Production-grade AI agent system with Multi-Tenant Isolation, Episodic Memory, and automated TTL Reaper.",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Configuration from Settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Register Routers
app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(agent.router)
app.include_router(threads.router)
app.include_router(memories.router)
app.include_router(reaper.router)

@app.get("/health", tags=["Monitoring"])
def health_check():
    """Health check probe."""
    return {"status": "healthy", "service": "ticket-agent-api", "version": "2.0.0"}

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
