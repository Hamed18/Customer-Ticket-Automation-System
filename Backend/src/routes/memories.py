import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from src.database import get_db
from src.dependencies import get_current_user, AGENT_ROLES
from src.models.Users import User
from src.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/memories",
    tags=["Episodic Memory"]
)

@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_episodic_memories(
    user_id: Optional[str] = Query(None, description="Optional target user ID (for Support Agents)"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve episodic interaction memories strictly scoped by tenant and user authorization."""
    is_agent = current_user.role in AGENT_ROLES

    # If non-agent, strictly force user_id to current_user.user_id
    target_user_id = user_id if (is_agent and user_id) else current_user.user_id

    memories = MemoryService.get_user_memories(
        tenant_id=current_user.tenant_id,
        user_id=target_user_id,
        limit=limit,
        db=db
    )
    return memories
