from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.endpoint import Endpoint
from app.models.application import Application
from app.schemas.endpoint import (
    EndpointCreate,
    EndpointResponse,
    EndpointListResponse,
    AppCreate,
    AppResponse,
)
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/endpoints", tags=["Endpoints"])


@router.get("/", response_model=List[EndpointListResponse])
def list_endpoints(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoints = db.query(Endpoint).all()
    return [EndpointListResponse.model_validate(ep) for ep in endpoints]


@router.get("/{endpoint_id}", response_model=EndpointResponse)
def get_endpoint(
    endpoint_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )
    return EndpointResponse.model_validate(endpoint)


@router.post("/{endpoint_id}/apps", response_model=AppResponse)
def add_app_to_endpoint(
    endpoint_id: str,
    app_data: AppCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    endpoint = db.query(Endpoint).filter(Endpoint.id == endpoint_id).first()
    if not endpoint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Endpoint not found",
        )

    application = Application(
        name=app_data.name,
        process_name=app_data.process_name,
        status=app_data.status,
        endpoint_id=endpoint_id,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return AppResponse.model_validate(application)
