import os
import json
import re
import logging
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from src.config import settings
from src.state import IncidentClassification

logger = logging.getLogger("llm.fallback")

@dataclass
class LLMResponse:
    content: str

    def __str__(self):
        return self.content


class DistributedFallbackLLM:
    """
    Distributed multi-tier fallback LLM client powered by OpenRouter.
    Executes queries with automatic graceful degradation across models:
    1. Tier 1: Gemini 2.5 Flash (Fast, high quality)
    2. Tier 2: Qwen 2.5 72B (Open weights flagship)
    3. Tier 3: LLaMA 3.3 70B (High capability OSS model)
    4. Tier 4: OpenRouter Free Router (Dynamic zero-cost fallback)
    """

    DEFAULT_MODELS = [
        "google/gemini-2.5-flash",
        "qwen/qwen-2.5-72b-instruct",
        "meta-llama/llama-3.3-70b-instruct",
        "openrouter/free"
    ]

    OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None, models: Optional[List[str]] = None):
        self.api_key = api_key or settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "")
        self.models = models or self.DEFAULT_MODELS

    def _call_model(self, model: str, messages: List[Dict[str, str]], max_tokens: int = 1000, temperature: float = 0.3) -> str:
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost:8000",
            "X-Title": "Agentic Ticket Resolution Distributed System"
        }

        req = urllib.request.Request(self.OPENROUTER_URL, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        choices = result.get("choices", [])
        if not choices:
            raise ValueError(f"No choices returned by {model}: {result}")

        msg = choices[0].get("message", {})
        content = msg.get("content")
        # Handle reasoning models where output might appear in reasoning field
        if not content:
            content = msg.get("reasoning", "")

        return content.strip() if content else ""

    def invoke(self, prompt: Any, max_tokens: int = 1000, temperature: float = 0.3) -> LLMResponse:
        """Invoke distributed system with cascading failover across model tiers."""
        # Normalize prompt into messages format
        if isinstance(prompt, str):
            messages = [{"role": "user", "content": prompt}]
        elif isinstance(prompt, list):
            messages = []
            for item in prompt:
                if hasattr(item, "content"):
                    role = "user" if getattr(item, "type", "") in ["human", "user"] else "assistant"
                    messages.append({"role": role, "content": str(item.content)})
                elif isinstance(item, dict):
                    messages.append(item)
                else:
                    messages.append({"role": "user", "content": str(item)})
        else:
            messages = [{"role": "user", "content": str(prompt)}]

        last_error = None
        for idx, model in enumerate(self.models):
            try:
                logger.info(f"[Distributed LLM] Attempting Tier {idx + 1}: {model}")
                content = self._call_model(model, messages, max_tokens=max_tokens, temperature=temperature)
                if content:
                    logger.info(f"[Distributed LLM] Succeeded on Tier {idx + 1} ({model})")
                    return LLMResponse(content=content)
            except Exception as e:
                logger.warning(f"[Distributed LLM] Tier {idx + 1} ({model}) failed: {e}. Failing over to next tier...")
                last_error = e

        # If all tiers fail, raise or return error notice
        logger.error(f"[Distributed LLM] All fallback tiers failed! Last error: {last_error}")
        return LLMResponse(content=f"Service temporarily degraded. All fallback tiers exhausted: {last_error}")

    def with_structured_output(self, schema_cls: Any):
        """Provide LangChain-compatible structured output helper."""
        return StructuredOutputAdapter(self, schema_cls)


class IncidentClassifier:
    """Classifies incoming ticket queries into category, intent, and urgency using the fallback pipeline."""

    CATEGORIES = ["Support", "Commerce", "Technical", "Product"]
    INTENTS = [
        "Order Issue", "Payment/Billing", "Technical Bug",
        "Account Access", "Product Inquiry", "Feature Request"
    ]
    URGENCIES = ["Low", "Medium", "High"]

    PROMPT_TEMPLATE = """You are a support ticket classification engine.
Analyze the user query and return a strict JSON object with:
1. "category": Must be exactly one of: ["Support", "Commerce", "Technical", "Product"]
2. "intent": Must be exactly one of: ["Order Issue", "Payment/Billing", "Technical Bug", "Account Access", "Product Inquiry", "Feature Request"]
3. "urgency": Must be exactly one of: ["Low", "Medium", "High"]

Guidelines:
- High: blocking bugs, crash, payment/billing errors, outages, security issues
- Medium: non-critical bugs, delays, account issues
- Low: general questions, feature requests, product inquiry

Query to classify:
"{query}"

Respond with ONLY the raw JSON object. No explanation, no markdown ticks.
Example:
{{"category": "Commerce", "intent": "Payment/Billing", "urgency": "High"}}
"""

    def __init__(self, llm_engine: DistributedFallbackLLM):
        self.llm = llm_engine

    def invoke(self, query: str) -> IncidentClassification:
        prompt = self.PROMPT_TEMPLATE.format(query=query)
        response = self.llm.invoke(prompt, max_tokens=150, temperature=0.1)

        raw = response.content.strip()
        logger.info(f"Raw classification output: {raw}")

        # Attempt to parse JSON from response
        try:
            match = re.search(r"\{.*?\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
            else:
                data = json.loads(raw)

            # Sanitize category
            category = data.get("category", "Technical")
            if category not in self.CATEGORIES:
                category = "Technical"

            # Sanitize intent
            intent = data.get("intent", "Technical Bug")
            if intent not in self.INTENTS:
                intent = "Technical Bug"

            # Sanitize urgency
            urgency = data.get("urgency", "Medium")
            if urgency not in self.URGENCIES:
                urgency = "Medium"

            return IncidentClassification(
                category=category,
                intent=intent,
                urgency=urgency
            )
        except Exception as e:
            logger.warning(f"Failed to parse classification JSON ({e}), applying intelligent heuristics")
            query_lower = query.lower()

            # Rule heuristics fallback
            urgency = "Medium"
            if any(w in query_lower for w in ["payment", "charged", "billing", "refund", "crash", "outage", "blocker"]):
                urgency = "High"
            elif any(w in query_lower for w in ["how to", "feature", "inquiry", "info"]):
                urgency = "Low"

            category = "Technical"
            intent = "Technical Bug"
            if any(w in query_lower for w in ["refund", "billing", "payment", "card", "charge"]):
                category = "Commerce"
                intent = "Payment/Billing"
            elif any(w in query_lower for w in ["login", "password", "access", "account"]):
                category = "Support"
                intent = "Account Access"
            elif any(w in query_lower for w in ["feature", "request", "suggest"]):
                category = "Product"
                intent = "Feature Request"

            return IncidentClassification(
                category=category,
                intent=intent,
                urgency=urgency
            )


class StructuredOutputAdapter:
    """Adapter to give DistributedFallbackLLM the .with_structured_output() interface."""
    def __init__(self, llm: DistributedFallbackLLM, schema_cls: Any):
        self.llm = llm
        self.schema_cls = schema_cls

    def invoke(self, query: str) -> Any:
        classifier = IncidentClassifier(self.llm)
        return classifier.invoke(query)


# Global distributed fallback instances
llm = DistributedFallbackLLM()
gemini_llm = llm
Incident_classifier = IncidentClassifier(llm)
