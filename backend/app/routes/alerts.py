from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    endpoint_id: Optional[str] = Query(None),
    app_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Alert)

    if endpoint_id:
        query = query.filter(Alert.endpoint_id == endpoint_id)
    if app_id:
        query = query.filter(Alert.app_id == app_id)
    if severity:
        query = query.filter(Alert.severity == severity)

    alerts = query.order_by(Alert.timestamp.desc()).limit(limit).all()
    return [AlertResponse.model_validate(a) for a in alerts]


@router.get("/endpoint/{endpoint_id}/app/{app_id}", response_model=List[AlertResponse])
def get_alerts_for_endpoint_app(
    endpoint_id: str,
    app_id: str,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alerts = (
        db.query(Alert)
        .filter(Alert.endpoint_id == endpoint_id, Alert.app_id == app_id)
        .order_by(Alert.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [AlertResponse.model_validate(a) for a in alerts]
