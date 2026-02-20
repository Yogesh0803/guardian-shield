"""
Context engine: combines all context sources into a unified context vector.
This is the core "context-aware" component of the firewall.
"""

import numpy as np
from dataclasses import dataclass
from typing import Optional

from .app_identifier import AppIdentifier, AppInfo
from .time_features import TimeFeatures, TimeContext
from .behavior_baseline import BehaviorBaseline, BehaviorContext
from .geo_lookup import GeoLookup, GeoContext
from ..capture.packet_capture import Flow
from ..capture.feature_extractor import FeatureExtractor
from ..config import config


@dataclass
class FlowContext:
    """Complete context for a network flow — used for ML inference."""
    # Network features (40 features from feature extractor)
    flow_features: np.ndarray

    # App context
    app_name: str
    process_id: int
    app_trust_score: float

    # Time context
    hour: int
    day_of_week: int
    is_business_hours: bool
    time_since_last_request: float

    # Behavioral context
    rate_deviation: float
    size_deviation: float
    destination_novelty: float
    port_novelty: float

    # Geo context
    dest_country: str
    dest_country_code: str
    is_geo_anomaly: bool

    # Flow metadata
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    flow_duration: float
    total_bytes: int
    packet_count: int

    def to_feature_vector(self) -> np.ndarray:
        """Convert full context to a feature vector for ML models."""
        context_features = np.array([
            # App context (3 features)
            self.app_trust_score,
            1.0 if self.app_name != "unknown" else 0.0,
            float(self.process_id > 0),

            # Time context (5 features)
            self.hour / 24.0,  # normalized
            self.day_of_week / 7.0,
            float(self.is_business_hours),
            min(self.time_since_last_request / 3600.0, 1.0),  # cap at 1 hour
            float(self.hour < 6 or self.hour > 22),  # is_late_night

            # Behavioral context (4 features)
            min(self.rate_deviation / 5.0, 1.0),  # normalized z-score
            min(self.size_deviation / 5.0, 1.0),
            self.destination_novelty,
            self.port_novelty,

            # Geo context (2 features)
            float(self.is_geo_anomaly),
            float(self.dest_country_code in ("CN", "RU", "KP", "IR")),  # high-risk countries

            # Flow metadata (5 features)
            min(self.flow_duration / 60.0, 1.0),  # normalized to minutes
            min(self.total_bytes / 1e6, 1.0),  # normalized to MB
            min(self.packet_count / 1000.0, 1.0),
            float(self.protocol == "TCP"),
            float(self.protocol == "UDP"),
        ], dtype=np.float32)

        # Combine: 40 network features + 19 context features = 59 features
        # Pad to 80 total for model compatibility
        combined = np.concatenate([self.flow_features, context_features])
        padded = np.zeros(config.total_features, dtype=np.float32)
        padded[:len(combined)] = combined
        return padded

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "app_name": self.app_name,
            "process_id": self.process_id,
            "app_trust_score": self.app_trust_score,
            "hour": self.hour,
            "day_of_week": self.day_of_week,
            "is_business_hours": self.is_business_hours,
            "time_since_last_request": self.time_since_last_request,
            "rate_deviation": self.rate_deviation,
            "size_deviation": self.size_deviation,
            "destination_novelty": self.destination_novelty,
            "dest_country": self.dest_country,
            "dest_asn": self.dest_country_code,
            "is_geo_anomaly": self.is_geo_anomaly,
        }


class ContextEngine:
    """Builds complete context for each flow by combining all context sources."""

    def __init__(self):
        self.feature_extractor = FeatureExtractor()
        self.app_identifier = AppIdentifier()
        self.time_features = TimeFeatures()
        self.behavior_baseline = BehaviorBaseline()
        self.geo_lookup = GeoLookup(db_path=config.geo_db_path)

    def build_context(self, flow: Flow) -> FlowContext:
        """Build full context for a network flow."""
        # 1. Extract network features
        features = self.feature_extractor.extract(flow)

        # 2. Identify application
        app_info = self.app_identifier.identify(
            flow.src_ip, flow.src_port, flow.dst_ip, flow.dst_port, flow.protocol
        )
        app_name = app_info.name if app_info else "unknown"
        pid = app_info.pid if app_info else 0
        trust = app_info.trust_score if app_info else 0.3

        # 3. Time context
        time_ctx = self.time_features.extract(app_name, flow.start_time)

        # 4. Behavioral baseline
        avg_pkt_size = flow.total_bytes / max(flow.packet_count, 1)
        behavior_ctx = self.behavior_baseline.update_and_compare(
            key=app_name,
            packet_size=avg_pkt_size,
            bytes_in_flow=flow.total_bytes,
            dst_ip=flow.dst_ip,
            dst_port=flow.dst_port,
            timestamp=flow.start_time,
        )

        # 5. Geo context
        geo_ctx = self.geo_lookup.lookup(flow.dst_ip, source_key=app_name)

        return FlowContext(
            flow_features=features,
            app_name=app_name,
            process_id=pid,
            app_trust_score=trust,
            hour=time_ctx.hour,
            day_of_week=time_ctx.day_of_week,
            is_business_hours=time_ctx.is_business_hours,
            time_since_last_request=time_ctx.time_since_last_request,
            rate_deviation=behavior_ctx.rate_deviation,
            size_deviation=behavior_ctx.size_deviation,
            destination_novelty=behavior_ctx.destination_novelty,
            port_novelty=behavior_ctx.port_novelty,
            dest_country=geo_ctx.country,
            dest_country_code=geo_ctx.country_code,
            is_geo_anomaly=geo_ctx.is_geo_anomaly,
            src_ip=flow.src_ip,
            dst_ip=flow.dst_ip,
            src_port=flow.src_port,
            dst_port=flow.dst_port,
            protocol=flow.protocol,
            flow_duration=flow.duration,
            total_bytes=flow.total_bytes,
            packet_count=flow.packet_count,
        )
