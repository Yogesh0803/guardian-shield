import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class MLConfig:
    # API
    backend_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Capture
    interface: str = os.getenv("CAPTURE_INTERFACE", "")  # empty = auto-detect
    capture_filter: str = "ip"
    flow_timeout: int = 10  # seconds to group packets into flows
    buffer_size: int = 100  # max flows to buffer before processing

    # Models
    model_dir: str = os.path.join(os.path.dirname(__file__), "models", "saved")
    anomaly_threshold_high: float = 0.8
    anomaly_threshold_medium: float = 0.5

    # Context
    behavior_window: int = 3600  # seconds of history for baseline
    geo_db_path: str = os.path.join(os.path.dirname(__file__), "data", "GeoLite2-Country.mmdb")

    # Enforcement
    platform: str = ""  # auto-detect: "windows" or "linux"
    block_duration: int = 300  # seconds for temporary blocks

    # Feature extraction
    feature_count: int = 40  # number of flow-level features
    context_feature_count: int = 40  # additional context features
    total_features: int = 80

    # Training
    training_data_path: str = os.path.join(os.path.dirname(__file__), "data", "cicids2017")
    batch_size: int = 64
    epochs: int = 50
    learning_rate: float = 0.001

    # Attack types
    attack_labels: List[str] = field(default_factory=lambda: [
        "Benign", "DoS", "DDoS", "PortScan", "BruteForce",
        "WebAttack", "Botnet", "Infiltration",
    ])


config = MLConfig()
