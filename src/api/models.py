"""Pydantic models for request and response validation."""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Payload schema for diagnostic inference requests."""
    query: str = Field(..., description="The farmer's symptom description or question.")
    history: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional multi-turn conversation history."
    )


class QueryResponse(BaseModel):
    """Structured JSON response returned by the triage engine."""
    answer: str = Field(..., description="Conversational advice or clarifying questions.")
    status: str = Field(..., description="Execution status: 'success' or 'fallback'.")
    language: Optional[str] = Field(default="en", description="Detected ISO language code.")
    disease_id: Optional[str] = Field(default=None, description="Matched KALRO/IITA disease identifier.")
    disease_name: Optional[str] = Field(default=None, description="Localized disease name.")
    urgency: Optional[str] = Field(default="GREEN", description="Triage color: RED, ORANGE, YELLOW, or GREEN.")
    escalate: Optional[bool] = Field(default=False, description="Whether immediate human veterinary escalation is triggered.")
