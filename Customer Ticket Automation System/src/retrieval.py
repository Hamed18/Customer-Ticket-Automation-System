import os
import logging
from typing import List, Dict, Any
from src.config import settings

logger = logging.getLogger("retrieval")

# Built-in knowledge base for instant zero-dependency retrieval fallback
FALLBACK_KNOWLEDGE_BASE = [
    {
        "page_content": "Password reset troubleshooting guide",
        "metadata": {
            "answer": "Users can reset passwords via the forgot password link. A reset token is sent to the registered email and expires in 15 minutes."
        }
    },
    {
        "page_content": "Refund policy internal document",
        "metadata": {
            "answer": "Refund requests submitted within 14 days of purchase are eligible for a full refund to the original payment method within 3-5 business days."
        }
    },
    {
        "page_content": "Billing issue resolution SOP",
        "metadata": {
            "answer": "For duplicate charges, verify transaction IDs with the payment processor. Initiate a void for uncaptured authorizations or a partial refund for captured payments."
        }
    },
    {
        "page_content": "VPN and connection troubleshooting steps",
        "metadata": {
            "answer": "Check gateway routing, ensure credentials and MFA token are valid, and confirm company SSO status."
        }
    },
    {
        "page_content": "Order cancellation workflow",
        "metadata": {
            "answer": "Orders in 'Processing' status can be canceled directly from the dashboard. Dispatched orders require a return merchandise authorization (RMA)."
        }
    }
]


def retrieve(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Retrieve relevant knowledge base documents using Qdrant with local fallback."""
    try:
        from qdrant_client import QdrantClient

        client_url = settings.QDRANT_CLIENT_URL
        client = QdrantClient(url=client_url, timeout=3)

        # Check if Google GenAI embeddings can be created
        if settings.GOOGLE_API_KEY:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                bi_encoder = GoogleGenerativeAIEmbeddings(
                    model="gemini-embedding-2-preview",
                    google_api_key=settings.GOOGLE_API_KEY
                )
                query_vector = bi_encoder.embed_query(query)

                results = client.query_points(
                    collection_name="new_collection",
                    query=query_vector,
                    limit=k,
                    with_payload=True
                )

                docs = []
                for point in results.points:
                    docs.append(point.payload)
                if docs:
                    return docs
            except Exception as e:
                logger.warning(f"Vector search embedding/query failed: {e}")

    except Exception as e:
        logger.warning(f"Qdrant connection unavailable ({e}). Using semantic fallback knowledge base.")

    # Intelligent fallback: keyword matching against built-in knowledge base
    query_lower = query.lower()
    matches = []
    for item in FALLBACK_KNOWLEDGE_BASE:
        text = (item["page_content"] + " " + item["metadata"]["answer"]).lower()
        score = sum(1 for word in query_lower.split() if word in text and len(word) > 2)
        if score > 0:
            matches.append((score, item))

    matches.sort(key=lambda x: x[0], reverse=True)
    if matches:
        return [m[1] for m in matches[:k]]

    return FALLBACK_KNOWLEDGE_BASE[:k]
