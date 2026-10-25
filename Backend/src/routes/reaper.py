import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.dependencies import get_current_user, get_current_active_agent
from src.models.Users import User
from src.services.reaper_service import TTLReaperService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reaper",
    tags=["TTL Reaper"]
)

@router.post("/trigger", response_model=Dict[str, Any])
def trigger_sweep(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_agent)
):
    """Manually invoke the TTL Reaper cleanup sweep (Agent/Admin privilege required)."""
    logger.info(f"TTL Reaper sweep manually invoked by {current_user.username}")
    result = TTLReaperService.run_sweep(db)
    return result

@router.get("/stats", response_model=Dict[str, Any])
def get_reaper_stats(
    current_user: User = Depends(get_current_user)
):
    """View latest TTL Reaper execution metrics and statistics."""
    return TTLReaperService.last_run_stats
