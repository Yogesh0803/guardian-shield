from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class MLAccuracy(BaseModel):
    anomaly_detector: float
    attack_classifier: float


class MLStatusResponse(BaseModel):
    is_running: bool
    models_loaded: list[str]
    predictions_per_minute: int
    last_retrain: str
    accuracy: MLAccuracy
    total_predictions: int
    total_blocked: int


class MLPredictionResponse(BaseModel):
    id: str
    anomaly_score: float
    attack_type: Optional[str] = None
    confidence: float
    action: str
    app_name: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    context_json: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
