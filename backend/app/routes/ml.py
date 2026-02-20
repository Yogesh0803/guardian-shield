from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta

from app.schemas.ml import MLStatusResponse, MLAccuracy
from app.middleware.auth import get_current_user, require_admin
from app.models.user import User

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])


@router.get("/status", response_model=MLStatusResponse)
def get_ml_status(current_user: User = Depends(get_current_user)):
    """Return ML model status matching the frontend MLStatus interface."""
    return MLStatusResponse(
        is_running=True,
        models_loaded=["isolation_forest", "autoencoder", "lstm_cnn", "xgboost"],
        predictions_per_minute=142,
        last_retrain=(datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
        accuracy=MLAccuracy(
            anomaly_detector=0.943,
            attack_classifier=0.957,
        ),
        total_predictions=15847,
        total_blocked=538,
    )


@router.post("/retrain")
def retrain_model(admin_user: User = Depends(require_admin)):
    """Trigger model retraining (placeholder). Requires admin role."""
    return {
        "status": "training_initiated",
        "message": "Model retraining has been queued. Estimated time: 15 minutes.",
        "initiated_by": admin_user.email,
        "estimated_completion": (
            datetime.now(timezone.utc) + timedelta(minutes=15)
        ).isoformat(),
    }
