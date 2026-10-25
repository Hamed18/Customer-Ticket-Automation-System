import logging
from uuid import uuid4
from typing import Dict, Any, Optional
try:
    from langgraph.types import Command
except ImportError:
    class Command:
        def __init__(self, resume=None, **kwargs):
            self.resume = resume
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from src.state import UserContext
from src.graph import agent
from src.services.thread_service import ThreadService
from src.services.ticket_service import TicketService

logger = logging.getLogger(__name__)

class AgentService:
    @staticmethod
    def execute_ticket(
        ticket_id: str,
        user_id: str,
        username: str,
        title_query: str,
        ticket_description: str,
        token: str,
        tenant_id: str = "default",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Execute the LangGraph workflow for a new or existing ticket."""
        thread_id = str(uuid4())
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        ticket_payload = {
            "incident_id": ticket_id,
            "incident_title": title_query,
            "incident_sender": username,
            "incident_description": ticket_description
        }
        user_context = UserContext(
            userid=user_id,
            username=username,
            access_token=token,
            tenant_id=tenant_id
        )

        logger.info(f"Starting agent execution for ticket {ticket_id} on thread {thread_id} (Tenant: {tenant_id})")
        result = agent.invoke(ticket_payload, context=user_context, config=config)

        # Check if the execution paused on a HITL interrupt
        is_interrupted = "__interrupt__" in result

        # Save thread tracking state directly via ThreadService
        thread_record = ThreadService.save_thread(
            thread_id=thread_id,
            ticket_id=ticket_id,
            current_state=jsonable_encoder(result),
            current_node="approval_node" if is_interrupted else "completed",
            status="Running" if is_interrupted else "Completed",
            interrupt_reason="Low confidence flagged for review" if is_interrupted else None,
            tenant_id=tenant_id,
            db=db
        )

        return {
            "message": "Execution started" if is_interrupted else "Execution completed",
            "thread_id": thread_id,
            "ticket_id": ticket_id,
            "tenant_id": tenant_id,
            "is_interrupted": is_interrupted,
            "state": jsonable_encoder(result)
        }

    @staticmethod
    def resume_ticket(
        thread_id: str,
        final_response: str,
        user_id: str,
        username: str,
        token: str,
        tenant_id: str = "default",
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """Resume an interrupted LangGraph workflow with human approval or edits."""
        config = {
            "configurable": {
                "thread_id": thread_id,
            }
        }
        user_context = UserContext(
            userid=user_id,
            username=username,
            access_token=token,
            tenant_id=tenant_id
        )

        logger.info(f"Resuming agent execution for thread {thread_id} (Tenant: {tenant_id})")
        result = agent.invoke(
            Command(resume=final_response),
            context=user_context,
            config=config
        )

        # Mark thread as resolved in database
        ThreadService.resolve_thread(
            thread_id=thread_id,
            resume_answer=final_response,
            status="Resolved",
            db=db
        )

        return {
            "message": "Thread resumed and resolved successfully",
            "thread_id": thread_id,
            "state": jsonable_encoder(result)
        }
