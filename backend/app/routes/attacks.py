from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from app.database import get_db
from app.models.ml_prediction import MLPrediction
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/attacks", tags=["Attacks"])


@router.get("/endpoint/{endpoint_id}")
def get_attack_stats(
    endpoint_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get aggregated attack statistics for an endpoint."""
    predictions = (
        db.query(MLPrediction)
        .filter(MLPrediction.dst_ip.isnot(None))
        .all()
    )

    # Aggregate by attack type
    attack_counts: Dict[str, int] = {}
    total_blocked = 0
    total_monitored = 0
    avg_confidence = 0.0
    count = 0

    for pred in predictions:
        if pred.attack_type:
            attack_counts[pred.attack_type] = attack_counts.get(pred.attack_type, 0) + 1
        if pred.action == "block":
            total_blocked += 1
        elif pred.action == "monitor":
            total_monitored += 1
        avg_confidence += pred.confidence
        count += 1

    return {
        "endpoint_id": endpoint_id,
        "total_predictions": count,
        "total_blocked": total_blocked,
        "total_monitored": total_monitored,
        "average_confidence": round(avg_confidence / max(count, 1), 3),
        "attack_type_breakdown": attack_counts,
    }


@router.get("/endpoint/{endpoint_id}/app/{app_name}")
def get_attack_stats_by_app(
    endpoint_id: str,
    app_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get attack stats for a specific app on an endpoint."""
    predictions = (
        db.query(MLPrediction)
        .filter(MLPrediction.app_name == app_name)
        .all()
    )

    attack_counts: Dict[str, int] = {}
    total = 0
    total_blocked = 0

    for pred in predictions:
        if pred.attack_type:
            attack_counts[pred.attack_type] = attack_counts.get(pred.attack_type, 0) + 1
        if pred.action == "block":
            total_blocked += 1
        total += 1

    return {
        "endpoint_id": endpoint_id,
        "app_name": app_name,
        "total_predictions": total,
        "total_blocked": total_blocked,
        "attack_type_breakdown": attack_counts,
    }
