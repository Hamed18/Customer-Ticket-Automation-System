from typing import Literal, List, Annotated, Optional, Any
from dataclasses import dataclass, field

try:
    from pydantic import BaseModel
    from langgraph.graph import add_messages
    from langchain.messages import AnyMessage

    @dataclass
    class UserContext:
        userid: str
        username: str
        access_token: str

    class IncidentClassification(BaseModel):
        category: Literal["Support", "Commerce", "Technical", "Product"]
        intent: Literal["Order Issue", "Payment/Billing", "Technical Bug", "Account Access", "Product Inquiry", "Feature Request"]
        urgency: Literal["Low", "Medium", "High"]

    class IncidentState(BaseModel):
        # Dynamic Incident context
        incident_id: str
        incident_title: str
        incident_sender: str
        incident_description: str

        # Incident Classification
        classification: IncidentClassification | None = None
        status: str | None = None

        # Historic Data
        history_incidents: List[str] | None = []
        relevant_docs: List[str] | None = []

        confidence: float | None = None

        # Generated response
        draft_response: str | None = None
        final_response: str | None = None

        messages: Annotated[List[AnyMessage], add_messages] | None = None

except ImportError:
    @dataclass
    class UserContext:
        userid: str = ""
        username: str = ""
        access_token: str = ""

    @dataclass
    class IncidentClassification:
        category: str = "Technical"
        intent: str = "Technical Bug"
        urgency: str = "Medium"

    @dataclass
    class IncidentState:
        incident_id: str = ""
        incident_title: str = ""
        incident_sender: str = ""
        incident_description: str = ""
        classification: Optional[IncidentClassification] = None
        status: Optional[str] = None
        history_incidents: Optional[List[str]] = field(default_factory=list)
        relevant_docs: Optional[List[str]] = field(default_factory=list)
        confidence: Optional[float] = None
        draft_response: Optional[str] = None
        final_response: Optional[str] = None
        messages: Optional[List[Any]] = field(default_factory=list)
