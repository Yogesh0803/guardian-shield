from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AlertResponse(BaseModel):
    id: str
    severity: str
    category: str
    attack_type: Optional[str] = None
    message: str
    confidence: Optional[float] = None
    app_id: Optional[str] = None
    endpoint_id: str
    timestamp: datetime

    class Config:
        from_attributes = True


class AlertQuery(BaseModel):
    endpoint_id: Optional[str] = None
    app_id: Optional[str] = None
    severity: Optional[str] = None
    limit: int = Field(default=50, ge=1, le=500)
