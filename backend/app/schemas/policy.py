from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class PolicyCreate(BaseModel):
    name: str = Field(..., description="Policy name")
    description: Optional[str] = None
    purpose: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    endpoint_id: Optional[str] = None
    is_active: bool = Field(default=True)
    natural_language: Optional[str] = Field(
        default=None,
        description="Natural language description to parse into conditions",
    )


class PolicyResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    purpose: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    endpoint_id: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class NLPPolicyParse(BaseModel):
    natural_language: Optional[str] = None
    input: Optional[str] = None  # frontend sends "input" field


class NLPPolicyParseResponse(BaseModel):
    name: str
    description: str
    purpose: str
    parsed: Dict[str, Any]
    confidence: float
    explanation: str
