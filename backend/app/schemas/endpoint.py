from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AppCreate(BaseModel):
    name: str = Field(..., description="Application name")
    process_name: str = Field(..., description="Process name")
    status: str = Field(default="running", description="Application status")


class AppResponse(BaseModel):
    id: str
    name: str
    process_name: str
    status: str
    endpoint_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class EndpointCreate(BaseModel):
    name: str = Field(..., description="Endpoint name")
    ip_address: str = Field(..., description="IP address")
    status: str = Field(default="active", description="Endpoint status")


class PolicyBrief(BaseModel):
    id: str
    name: str
    is_active: bool

    class Config:
        from_attributes = True


class AlertBrief(BaseModel):
    id: str
    severity: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True


class EndpointResponse(BaseModel):
    id: str
    name: str
    ip_address: str
    status: str
    created_at: datetime
    applications: List[AppResponse] = []
    policies: List[PolicyBrief] = []
    alerts: List[AlertBrief] = []

    class Config:
        from_attributes = True


class EndpointListResponse(BaseModel):
    id: str
    name: str
    ip_address: str
    status: str
    created_at: datetime
    applications: List[AppResponse] = []

    class Config:
        from_attributes = True
