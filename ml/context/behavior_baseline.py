"""
Behavioral baseline tracking.
Learns what "normal" looks like per app/endpoint and detects deviations.
Uses exponential moving average for adaptive baselines.
"""

import time
import math
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class BaselineStats:
    """Rolling statistics for a source."""
    request_rate: float = 0.0  # requests per minute
    avg_packet_size: float = 0.0
    avg_bytes_per_flow: float = 0.0
    common_ports: Dict[int, int] = field(default_factory=dict)
    common_destinations: Dict[str, int] = field(default_factory=dict)
    total_observations: int = 0
    last_updated: float = 0.0

    # EMA parameters
    _rate_ema: float = 0.0
    _size_ema: float = 0.0
    _bytes_ema: float = 0.0
    _rate_var: float = 0.0
    _size_var: float = 0.0


@dataclass
class BehaviorContext:
    rate_deviation: float  # z-score: how unusual is the request rate
    size_deviation: float  # z-score: how unusual is the packet size
    destination_novelty: float  # 0.0 (seen before) to 1.0 (never seen)
    port_novelty: float  # 0.0 (common port) to 1.0 (never used port)


class BehaviorBaseline:
    """Tracks and compares against behavioral baselines per source."""

    ALPHA = 0.1  # EMA smoothing factor (lower = slower adaptation)

    def __init__(self):
        self._baselines: Dict[str, BaselineStats] = {}

    def update_and_compare(
        self,
        key: str,
        packet_size: float,
        bytes_in_flow: float,
        dst_ip: str,
        dst_port: int,
        timestamp: float = None,
    ) -> BehaviorContext:
        """
        Update baseline for this source and return deviation scores.

        Args:
            key: Source identifier (e.g., app name or endpoint IP)
            packet_size: Average packet size in this flow
            bytes_in_flow: Total bytes in this flow
            dst_ip: Destination IP
            dst_port: Destination port
            timestamp: Current time
        """
        ts = timestamp or time.time()

        if key not in self._baselines:
            self._baselines[key] = BaselineStats(last_updated=ts)

        baseline = self._baselines[key]

        # Calculate current request rate
        time_diff = ts - baseline.last_updated if baseline.last_updated > 0 else 60.0
        time_diff = max(time_diff, 0.001)
        current_rate = 60.0 / time_diff  # requests per minute

        # Compute deviations BEFORE updating baseline
        if baseline.total_observations < 5:
            # Not enough data for meaningful comparison
            rate_dev = 0.0
            size_dev = 0.0
        else:
            rate_dev = self._z_score(current_rate, baseline._rate_ema, baseline._rate_var)
            size_dev = self._z_score(packet_size, baseline._size_ema, baseline._size_var)

        # Destination novelty
        dest_count = baseline.common_destinations.get(dst_ip, 0)
        total_dest = sum(baseline.common_destinations.values()) or 1
        destination_novelty = 1.0 - (dest_count / total_dest) if dest_count > 0 else 1.0

        # Port novelty
        port_count = baseline.common_ports.get(dst_port, 0)
        total_ports = sum(baseline.common_ports.values()) or 1
        port_novelty = 1.0 - (port_count / total_ports) if port_count > 0 else 1.0

        # Update baseline with EMA
        alpha = self.ALPHA
        baseline._rate_ema = alpha * current_rate + (1 - alpha) * baseline._rate_ema
        baseline._size_ema = alpha * packet_size + (1 - alpha) * baseline._size_ema
        baseline._bytes_ema = alpha * bytes_in_flow + (1 - alpha) * baseline._bytes_ema
        baseline._rate_var = alpha * (current_rate - baseline._rate_ema) ** 2 + (1 - alpha) * baseline._rate_var
        baseline._size_var = alpha * (packet_size - baseline._size_ema) ** 2 + (1 - alpha) * baseline._size_var

        # Update destination/port counts
        baseline.common_destinations[dst_ip] = baseline.common_destinations.get(dst_ip, 0) + 1
        baseline.common_ports[dst_port] = baseline.common_ports.get(dst_port, 0) + 1

        # Keep only top 100 destinations/ports to prevent memory growth
        if len(baseline.common_destinations) > 100:
            sorted_dests = sorted(baseline.common_destinations.items(), key=lambda x: x[1], reverse=True)
            baseline.common_destinations = dict(sorted_dests[:100])
        if len(baseline.common_ports) > 50:
            sorted_ports = sorted(baseline.common_ports.items(), key=lambda x: x[1], reverse=True)
            baseline.common_ports = dict(sorted_ports[:50])

        baseline.total_observations += 1
        baseline.last_updated = ts

        return BehaviorContext(
            rate_deviation=rate_dev,
            size_deviation=size_dev,
            destination_novelty=destination_novelty,
            port_novelty=port_novelty,
        )

    def _z_score(self, value: float, mean: float, variance: float) -> float:
        """Compute z-score (number of standard deviations from mean)."""
        std = math.sqrt(variance) if variance > 0 else 1.0
        return abs(value - mean) / std

    def get_baseline(self, key: str) -> BaselineStats:
        """Get baseline stats for a source."""
        return self._baselines.get(key, BaselineStats())
