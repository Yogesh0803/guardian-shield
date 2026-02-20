"""
Guardian Shield ML Engine — Main Entry Point.

Captures live network traffic, analyzes it through the ML pipeline,
enforces firewall rules, and reports results to the backend API.

Usage:
    python -m ml.main
    python -m ml.main --interface eth0
    python -m ml.main --no-enforce  (analysis only, no blocking)
"""

import os
import sys
import time
import json
import logging
import argparse
import threading
from typing import Optional

import requests

from .capture.packet_capture import PacketCapture, Flow
from .pipeline.inference import InferencePipeline, Prediction
from .enforcer.policy_engine import PolicyEngine
from .enforcer.firewall_rules import FirewallEnforcer
from .config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("guardian-shield")


class GuardianShieldEngine:
    """Main ML engine that ties capture, inference, and enforcement together."""

    def __init__(self, interface: str = "", enforce: bool = True):
        self.capture = PacketCapture(
            interface=interface or config.interface,
            flow_timeout=config.flow_timeout,
            buffer_size=config.buffer_size,
        )
        self.pipeline = InferencePipeline()
        self.policy_engine = PolicyEngine()
        self.enforcer = FirewallEnforcer(default_block_duration=config.block_duration)
        self.enforce = enforce

        self._running = False
        self._predictions: list = []
        self._lock = threading.Lock()

    def start(self):
        """Start the ML engine."""
        logger.info("=" * 60)
        logger.info("  Guardian Shield — Context-Aware ML Firewall Engine")
        logger.info("=" * 60)

        # Load ML models
        logger.info("Loading ML models...")
        load_results = self.pipeline.load_models()
        loaded_count = sum(1 for v in load_results.values() if v)
        logger.info(f"Models loaded: {loaded_count}/{len(load_results)}")

        if loaded_count == 0:
            logger.warning(
                "No pre-trained models found. The engine will run with context-based "
                "anomaly detection only. Train models with: python -m ml.pipeline.training"
            )

        # Load policies from backend
        self._load_policies()

        # Register flow callback
        self.capture.on_flow_complete(self._on_flow_complete)

        # Start capture
        self._running = True
        self.capture.start()

        # Start background threads
        threading.Thread(target=self._report_loop, daemon=True).start()
        threading.Thread(target=self._policy_refresh_loop, daemon=True).start()

        logger.info(f"Engine started. Capturing on: {self.capture.interface}")
        logger.info(f"Enforcement: {'ENABLED' if self.enforce else 'DISABLED (analysis only)'}")
        logger.info("Press Ctrl+C to stop.\n")

        # Keep main thread alive
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the ML engine gracefully."""
        logger.info("Shutting down...")
        self._running = False
        self.capture.stop()
        self.enforcer.cleanup()
        logger.info("Engine stopped.")

    def _on_flow_complete(self, flow: Flow):
        """Called when a network flow is complete. Runs ML analysis."""
        try:
            # Run inference pipeline
            prediction = self.pipeline.analyze(flow)

            # Log the prediction
            self._log_prediction(prediction)

            # Enforce action
            if self.enforce and prediction.action == "block":
                self.enforcer.block_ip(
                    ip=prediction.context.dst_ip,
                    app_name=prediction.context.app_name,
                    reason=f"{prediction.attack_type} (score: {prediction.anomaly_score:.2f})",
                )

            # Buffer for reporting to backend
            with self._lock:
                self._predictions.append(prediction.to_dict())
                if len(self._predictions) > 1000:
                    self._predictions = self._predictions[-500:]

        except Exception as e:
            logger.error(f"Error analyzing flow: {e}")

    def _log_prediction(self, pred: Prediction):
        """Log prediction with color-coded action."""
        action_colors = {
            "allow": "\033[92m",  # green
            "alert": "\033[93m",  # yellow
            "block": "\033[91m",  # red
        }
        reset = "\033[0m"
        color = action_colors.get(pred.action, "")

        logger.info(
            f"{color}[{pred.action.upper()}]{reset} "
            f"{pred.context.app_name} → {pred.context.dst_ip}:{pred.context.dst_port} "
            f"| Score: {pred.anomaly_score:.3f} "
            f"| Type: {pred.attack_type} ({pred.confidence:.0%}) "
            f"| Country: {pred.context.dest_country}"
        )

    def _report_loop(self):
        """Periodically send predictions and stats to the backend API."""
        while self._running:
            time.sleep(5)
            try:
                with self._lock:
                    if not self._predictions:
                        continue
                    batch = self._predictions[:50]
                    self._predictions = self._predictions[50:]

                # Send to backend
                requests.post(
                    f"{config.backend_url}/api/ml/predictions",
                    json={"predictions": batch},
                    timeout=5,
                )
            except Exception:
                pass  # Backend might not be running

    def _policy_refresh_loop(self):
        """Periodically refresh policies from the backend."""
        while self._running:
            time.sleep(60)
            self._load_policies()

    def _load_policies(self):
        """Load active policies from backend API."""
        try:
            res = requests.get(f"{config.backend_url}/api/policies", timeout=5)
            if res.status_code == 200:
                policies = res.json()
                self.policy_engine.load_policies(policies)
        except Exception:
            logger.debug("Could not load policies from backend (may not be running)")


def main():
    parser = argparse.ArgumentParser(description="Guardian Shield ML Engine")
    parser.add_argument("--interface", "-i", default="", help="Network interface to capture on")
    parser.add_argument("--no-enforce", action="store_true", help="Analysis only, don't block traffic")
    args = parser.parse_args()

    engine = GuardianShieldEngine(
        interface=args.interface,
        enforce=not args.no_enforce,
    )
    engine.start()


if __name__ == "__main__":
    main()
