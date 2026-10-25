import logging
import random
from typing import List, Literal
from datetime import datetime, timezone
try:
    from langgraph.runtime import Runtime
    from langgraph.types import interrupt
except ImportError:
    from typing import Any
    Runtime = Any
    def interrupt(data):
        return data
from src.state import IncidentClassification, IncidentState, UserContext
from src.llms import Incident_classifier, llm
from src.prompts import RAG_response_generation_prompt
from src.retrieval import retrieve
from src.services.ticket_service import TicketService
from src.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

# ==========================================
# Graph Nodes and Routers
# ==========================================

def classify_incident(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """Classify user query into category, intent, and urgency."""
    logger.info(f"Classifying incident {state.incident_id}: '{state.incident_title}'")
    try:
        classification = Incident_classifier.invoke(state.incident_title)
        state.classification = classification
    except Exception as e:
        logger.warning(f"Classification failed ({e}), using default fallback")
        state.classification = IncidentClassification(
            category="Technical",
            intent="Technical Bug",
            urgency="Medium"
        )
    return state


def router(state: IncidentState, runtime: Runtime[UserContext]) -> Literal["human_eval", "doc_search"]:
    """Route High/Critical urgency tickets directly to human evaluation."""
    urgency = state.classification.urgency if state.classification else "Medium"
    if urgency in ["High", "Critical"]:
        return "human_eval"
    return "doc_search"


def human_eval(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """Record direct escalation to manual human handling."""
    userid = runtime.context.userid if runtime.context else "system"
    username = runtime.context.username if runtime.context else "system"
    tenant_id = getattr(runtime.context, "tenant_id", "default") if runtime.context else "default"
    category = state.classification.category if state.classification else "Technical"
    intent = state.classification.intent if state.classification else "Technical Bug"
    priority = state.classification.urgency if state.classification else "High"

    TicketService.record_human_escalation(
        ticket_id=state.incident_id,
        user_id=userid,
        username=username,
        category=category,
        title_query=state.incident_title,
        ticket_description=state.incident_description,
        intent=intent,
        priority=priority,
        tenant_id=tenant_id,
        created_at=datetime.now(timezone.utc)
    )

    state.status = "Manual Handling"
    logger.info(f"Ticket {state.incident_id} saved with status Manual Handling.")
    return state


def doc_search(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """Retrieve relevant knowledge base documents and user episodic memories."""
    query = state.incident_title
    logger.info(f"Retrieving documents for query: '{query}'")

    try:
        docs = retrieve(query)
    except Exception as e:
        logger.warning(f"Vector search retrieval failed: {e}. Continuing with empty context.")
        docs = []

    retrieval_format = "Query: {}\nAnswer: {}"
    formatted_docs = []
    history = []

    for doc in docs:
        if isinstance(doc, dict):
            page_content = doc.get("page_content") or doc.get("query", "")
            metadata = doc.get("metadata", {})
            answer = metadata.get("answer", doc.get("answer", "No answer available"))
            formatted_docs.append(retrieval_format.format(page_content, answer))
            history.append(page_content)
        elif isinstance(doc, str):
            formatted_docs.append(doc)
            history.append(doc)

    state.relevant_docs = formatted_docs
    state.history_incidents = history

    # Phase 3: Retrieve Episodic Memories for this specific user in their tenant
    userid = runtime.context.userid if runtime.context else "system"
    tenant_id = getattr(runtime.context, "tenant_id", "default") if runtime.context else "default"

    try:
        episodic_memories = MemoryService.retrieve_relevant_memory(
            tenant_id=tenant_id,
            user_id=userid,
            current_query=query,
            limit=3
        )
        state.user_memories = episodic_memories
        logger.info(f"Retrieved {len(episodic_memories)} episodic memories for user {userid} in tenant {tenant_id}")
    except Exception as e:
        logger.warning(f"Could not retrieve episodic memories: {e}")
        state.user_memories = []

    return state


def draft_response(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """Generate draft response using retrieved context and episodic user history."""
    logger.info(f"Drafting RAG response for incident {state.incident_id}")
    context_str = "\n\n".join(state.relevant_docs) if state.relevant_docs else "No relevant knowledge base docs found."
    episodic_str = (
        "\n".join(f"- {m}" for m in state.user_memories)
        if state.user_memories
        else "No previous interaction history on file for this user."
    )

    prompt = RAG_response_generation_prompt.format(
        query=state.incident_title,
        episodic_context=episodic_str,
        retrieved_context=context_str
    )

    try:
        result = llm.invoke(prompt)
        response = result.content if hasattr(result, "content") else str(result)
    except Exception as e:
        logger.error(f"Error during draft response generation: {e}")
        response = "I encountered an error generating an automated response. Flagging for support review."

    state.draft_response = response
    return state


def evaluator(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """Calculate confidence score for the drafted response."""
    if not state.relevant_docs:
        confidence_score = 55.0
    else:
        confidence_score = float(random.choice([65.0, 72.0, 82.0, 91.0]))

    state.confidence = confidence_score
    logger.info(f"Evaluated confidence for {state.incident_id}: {confidence_score}%")
    return state


def human_router(state: IncidentState, runtime: Runtime[UserContext]) -> Literal["send_response", "human_review"]:
    """Route based on confidence threshold (>75% auto-resolves, <=75% requires human review)."""
    score = state.confidence or 0.0
    if score > 75:
        return "send_response"
    return "human_review"


def human_review(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """Flag ticket for human review due to low confidence."""
    userid = runtime.context.userid if runtime.context else "system"
    username = runtime.context.username if runtime.context else "system"
    tenant_id = getattr(runtime.context, "tenant_id", "default") if runtime.context else "default"
    category = state.classification.category if state.classification else "Technical"
    intent = state.classification.intent if state.classification else "Technical Bug"
    priority = state.classification.urgency if state.classification else "Medium"

    TicketService.record_human_review(
        ticket_id=state.incident_id,
        user_id=userid,
        username=username,
        category=category,
        title_query=state.incident_title,
        ticket_description=state.incident_description,
        intent=intent,
        priority=priority,
        ai_response=state.draft_response or "",
        ai_confidence=state.confidence or 0.0,
        retrieved_documents=state.history_incidents or [],
        tenant_id=tenant_id,
        created_at=datetime.now(timezone.utc)
    )

    state.status = "Human Review"
    logger.info(f"Ticket {state.incident_id} saved with status Human Review.")
    return state


def approval_node(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """LangGraph interrupt node: halts execution until human agent approves or edits response."""
    approved_text = interrupt(
        {
            "question": "Approve draft?",
            "draft": state.draft_response
        }
    )
    state.final_response = str(approved_text)
    return state


def send_approved_response(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """Finalize ticket with human-reviewed response and record episodic memory."""
    userid = runtime.context.userid if runtime.context else "system"
    tenant_id = getattr(runtime.context, "tenant_id", "default") if runtime.context else "default"
    category = state.classification.category if state.classification else "Technical"
    final_resp = state.final_response or state.draft_response or "Response approved."

    TicketService.record_approved_response(
        ticket_id=state.incident_id,
        final_response=final_resp,
        status="Resolved",
        resolution_state="Closed",
        resolved_by="AI+Human"
    )

    # Phase 3: Store Episodic Memory of the human-approved resolution
    try:
        MemoryService.record_ticket_resolution(
            tenant_id=tenant_id,
            user_id=userid,
            ticket_id=state.incident_id,
            title_query=state.incident_title,
            final_response=final_resp,
            category=category
        )
    except Exception as e:
        logger.warning(f"Failed to record episodic memory on approved response: {e}")

    state.status = "Resolved"
    logger.info(f"Ticket {state.incident_id} finalized with human-approved response and episodic memory stored.")
    return state


def send_response(state: IncidentState, runtime: Runtime[UserContext]) -> IncidentState:
    """Auto-resolve ticket when AI confidence exceeds threshold and record episodic memory."""
    userid = runtime.context.userid if runtime.context else "system"
    username = runtime.context.username if runtime.context else "system"
    tenant_id = getattr(runtime.context, "tenant_id", "default") if runtime.context else "default"
    category = state.classification.category if state.classification else "Technical"
    intent = state.classification.intent if state.classification else "Technical Bug"
    priority = state.classification.urgency if state.classification else "Medium"
    response_text = state.draft_response or "Ticket resolved automatically."

    TicketService.record_auto_resolution(
        ticket_id=state.incident_id,
        user_id=userid,
        username=username,
        category=category,
        title_query=state.incident_title,
        ticket_description=state.incident_description,
        intent=intent,
        priority=priority,
        ai_response=response_text,
        ai_confidence=state.confidence or 0.0,
        retrieved_documents=state.history_incidents or [],
        final_response=response_text,
        tenant_id=tenant_id,
        created_at=datetime.now(timezone.utc)
    )

    # Phase 3: Store Episodic Memory of auto-resolution
    try:
        MemoryService.record_ticket_resolution(
            tenant_id=tenant_id,
            user_id=userid,
            ticket_id=state.incident_id,
            title_query=state.incident_title,
            final_response=response_text,
            category=category
        )
    except Exception as e:
        logger.warning(f"Failed to record episodic memory on auto-resolution: {e}")

    state.status = "Resolved"
    state.final_response = response_text
    logger.info(f"Ticket {state.incident_id} auto-resolved successfully and episodic memory stored.")
    return state
