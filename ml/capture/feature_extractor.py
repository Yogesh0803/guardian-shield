"""
Extract numerical features from network flows.
Produces feature vectors compatible with CICIDS2017 format for ML models.
"""

import numpy as np
from typing import List
from .packet_capture import Flow, PacketInfo


class FeatureExtractor:
    """Extracts 40 numerical features from a network flow."""

    FEATURE_NAMES = [
        "flow_duration", "total_fwd_packets", "total_bwd_packets",
        "total_length_fwd", "total_length_bwd",
        "fwd_packet_length_max", "fwd_packet_length_min", "fwd_packet_length_mean", "fwd_packet_length_std",
        "bwd_packet_length_max", "bwd_packet_length_min", "bwd_packet_length_mean", "bwd_packet_length_std",
        "flow_bytes_per_sec", "flow_packets_per_sec",
        "flow_iat_mean", "flow_iat_std", "flow_iat_max", "flow_iat_min",
        "fwd_iat_mean", "fwd_iat_std", "fwd_iat_max", "fwd_iat_min",
        "bwd_iat_mean", "bwd_iat_std", "bwd_iat_max", "bwd_iat_min",
        "fwd_header_length", "bwd_header_length",
        "fwd_packets_per_sec", "bwd_packets_per_sec",
        "packet_length_mean", "packet_length_std", "packet_length_variance",
        "fin_flag_count", "syn_flag_count", "rst_flag_count",
        "psh_flag_count", "ack_flag_count", "urg_flag_count",
    ]

    def extract(self, flow: Flow) -> np.ndarray:
        """Extract feature vector from a flow."""
        packets = flow.packets
        if not packets:
            return np.zeros(40)

        # Split into forward (src→dst) and backward (dst→src)
        fwd = [p for p in packets if p.src_ip == flow.src_ip]
        bwd = [p for p in packets if p.src_ip != flow.src_ip]

        fwd_lengths = [p.length for p in fwd] or [0]
        bwd_lengths = [p.length for p in bwd] or [0]
        all_lengths = [p.length for p in packets]

        duration = flow.duration or 1e-6  # avoid div by zero

        # Inter-arrival times
        timestamps = sorted(p.timestamp for p in packets)
        iats = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)] or [0]

        fwd_times = sorted(p.timestamp for p in fwd)
        fwd_iats = [fwd_times[i + 1] - fwd_times[i] for i in range(len(fwd_times) - 1)] or [0]

        bwd_times = sorted(p.timestamp for p in bwd)
        bwd_iats = [bwd_times[i + 1] - bwd_times[i] for i in range(len(bwd_times) - 1)] or [0]

        # Flag counts (TCP only)
        flags = "".join(p.flags for p in packets)

        features = np.array([
            # Flow duration
            duration,
            # Packet counts
            len(fwd), len(bwd),
            # Total lengths
            sum(fwd_lengths), sum(bwd_lengths),
            # Fwd packet length stats
            max(fwd_lengths), min(fwd_lengths), np.mean(fwd_lengths), np.std(fwd_lengths),
            # Bwd packet length stats
            max(bwd_lengths), min(bwd_lengths), np.mean(bwd_lengths), np.std(bwd_lengths),
            # Flow rates
            sum(all_lengths) / duration,  # bytes/sec
            len(packets) / duration,  # packets/sec
            # Flow IAT stats
            np.mean(iats), np.std(iats), max(iats), min(iats),
            # Fwd IAT stats
            np.mean(fwd_iats), np.std(fwd_iats), max(fwd_iats), min(fwd_iats),
            # Bwd IAT stats
            np.mean(bwd_iats), np.std(bwd_iats), max(bwd_iats), min(bwd_iats),
            # Header lengths
            sum(p.header_length for p in fwd),
            sum(p.header_length for p in bwd),
            # Packets per sec
            len(fwd) / duration,
            len(bwd) / duration,
            # Packet length stats (all)
            np.mean(all_lengths), np.std(all_lengths), np.var(all_lengths),
            # TCP flag counts
            flags.count("F"),  # FIN
            flags.count("S"),  # SYN
            flags.count("R"),  # RST
            flags.count("P"),  # PSH
            flags.count("A"),  # ACK
            flags.count("U"),  # URG
        ], dtype=np.float32)

        # Replace NaN/inf with 0
        features = np.nan_to_num(features, nan=0.0, posinf=0.0, neginf=0.0)
        return features

    def extract_batch(self, flows: List[Flow]) -> np.ndarray:
        """Extract features for multiple flows."""
        return np.array([self.extract(f) for f in flows])
