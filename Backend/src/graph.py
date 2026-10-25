import logging
from langgraph.types import RetryPolicy
from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from src.state import IncidentState, UserContext
from src.config import settings
from src.nodes import (
    classify_incident, human_eval, human_review, human_router,
    doc_search, router, draft_response, evaluator,
    send_response, send_approved_response, approval_node
)

logger = logging.getLogger(__name__)

# Construct State Graph
graph = StateGraph(IncidentState, context_schema=UserContext)

graph.add_node("classify_incident", classify_incident)
graph.add_node("human_eval", human_eval)
graph.add_node("doc_search", doc_search, retry_policy=RetryPolicy(max_attempts=2))
graph.add_node("draft_response", draft_response)
graph.add_node("evaluator", evaluator)
graph.add_node("send_response", send_response)
graph.add_node("human_review", human_review)
graph.add_node("approval_node", approval_node)
graph.add_node("send_approved_response", send_approved_response)

graph.add_edge(START, "classify_incident")
graph.add_conditional_edges("classify_incident", router, ["human_eval", "doc_search"])
graph.add_edge("human_eval", END)
graph.add_edge("doc_search", "draft_response")
graph.add_edge("draft_response", "evaluator")

graph.add_conditional_edges("evaluator", human_router, ["send_response", "human_review"])
graph.add_edge("send_response", END)
graph.add_edge("human_review", "approval_node")
graph.add_edge("approval_node", "send_approved_response")
graph.add_edge("send_approved_response", END)

def get_checkpointer():
    """Build persistent or in-memory checkpointer safely."""
    if settings.LANGGRAPH_API:
        logger.info("Running in LangGraph Cloud API mode - checkpointer managed externally.")
        return None

    try:
        import psycopg
        from langgraph.checkpoint.postgres import PostgresSaver

        logger.info(f"Connecting checkpointer to PostgreSQL at {settings.DB_URI.split('@')[-1] if '@' in settings.DB_URI else 'configured URI'}")
        conn = psycopg.connect(settings.DB_URI, autocommit=True)
        checkpointer = PostgresSaver(conn)
        checkpointer.setup()
        return checkpointer
    except Exception as e:
        logger.warning(
            f"Could not connect to PostgreSQL checkpointer ({e}). "
            "Falling back to MemorySaver for thread state checkpointing."
        )
        return MemorySaver()

_checkpointer = get_checkpointer()
if _checkpointer is not None:
    agent = graph.compile(checkpointer=_checkpointer)
else:
    agent = graph.compile()
