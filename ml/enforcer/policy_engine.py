"""
Policy engine: combines user-defined rules with ML predictions.
Decides whether to allow, block, or alert on a flow.
"""

import logging
from typing import List, Optional
from dataclasses import dataclass

from ..context.context_engine import FlowContext
from ..config import config

logger = logging.getLogger(__name__)


@dataclass
class PolicyRule:
    """A user-defined firewall policy rule."""
    id: str
    name: str
    purpose: str  # "block" or "unblock"
    is_active: bool
    # Conditions
    domains: List[str]
    ips: List[str]
    ports: List[dict]  # [{"port": 80, "protocol": ["TCP"]}]
    app_names: List[str]
    time_range: Optional[dict] = None  # {"start": "09:00", "end": "18:00"}
    days_of_week: Optional[List[int]] = None  # [0,1,2,3,4] = Mon-Fri
    geo_countries: Optional[List[str]] = None  # ["CN", "RU"]
    anomaly_threshold: Optional[float] = None
    attack_types: Optional[List[str]] = None
    rate_limit: Optional[int] = None  # max requests per minute


class PolicyEngine:
    """Evaluates flows against user policies and ML predictions."""

    def __init__(self):
        self.policies: List[PolicyRule] = []

    def load_policies(self, policies: List[dict]):
        """Load policies from the backend API."""
        self.policies = []
        for p in policies:
            conditions = p.get("conditions", {})
            self.policies.append(PolicyRule(
                id=p["id"],
                name=p["name"],
                purpose=p["purpose"],
                is_active=p.get("is_active", True),
                domains=conditions.get("domains", []),
                ips=conditions.get("ips", []),
                ports=conditions.get("ports", []),
                app_names=conditions.get("app_names", []),
                time_range=conditions.get("time_range"),
                days_of_week=conditions.get("days_of_week"),
                geo_countries=conditions.get("geo_countries"),
                anomaly_threshold=conditions.get("anomaly_threshold"),
                attack_types=conditions.get("attack_types"),
                rate_limit=conditions.get("rate_limit"),
            ))
        logger.info(f"Loaded {len(self.policies)} policies")

    def evaluate(
        self,
        context: FlowContext,
        anomaly_score: float,
        attack_type: str,
        confidence: float,
    ) -> str:
        """
        Evaluate a flow against all policies.

        Returns: "allow", "block", or "alert"
        """
        # 1. Check user-defined policies first (highest priority)
        for policy in self.policies:
            if not policy.is_active:
                continue

            if self._matches_policy(policy, context, anomaly_score, attack_type):
                action = "block" if policy.purpose == "block" else "allow"
                logger.debug(f"Policy '{policy.name}' matched: {action}")
                return action

        # 2. ML-informed decision (if no policy matched)
        if anomaly_score > config.anomaly_threshold_high and confidence > 0.85:
            return "block"
        elif anomaly_score > config.anomaly_threshold_high:
            return "alert"
        elif anomaly_score > config.anomaly_threshold_medium:
            if attack_type in ("DDoS", "DoS", "BruteForce") and confidence > 0.7:
                return "block"
            return "alert"

        return "allow"

    def _matches_policy(
        self,
        policy: PolicyRule,
        ctx: FlowContext,
        anomaly_score: float,
        attack_type: str,
    ) -> bool:
        """Check if a flow matches a policy's conditions."""
        # All conditions must match (AND logic)
        checks = []

        # IP match
        if policy.ips:
            checks.append(ctx.dst_ip in policy.ips or ctx.src_ip in policy.ips)

        # Port match
        if policy.ports:
            port_match = False
            for p in policy.ports:
                if ctx.dst_port == p.get("port"):
                    protocols = p.get("protocol", [])
                    if not protocols or ctx.protocol in protocols:
                        port_match = True
                        break
            checks.append(port_match)

        # App name match
        if policy.app_names:
            checks.append(
                ctx.app_name.lower() in [a.lower() for a in policy.app_names]
            )

        # Time range
        if policy.time_range:
            start = int(policy.time_range.get("start", "0").split(":")[0])
            end = int(policy.time_range.get("end", "24").split(":")[0])
            checks.append(start <= ctx.hour < end)

        # Days of week
        if policy.days_of_week:
            checks.append(ctx.day_of_week in policy.days_of_week)

        # Geo countries
        if policy.geo_countries:
            checks.append(ctx.dest_country_code in policy.geo_countries)

        # Anomaly threshold
        if policy.anomaly_threshold is not None:
            checks.append(anomaly_score > policy.anomaly_threshold)

        # Attack types
        if policy.attack_types:
            checks.append(attack_type in policy.attack_types)

        # If no conditions specified, policy doesn't match anything
        if not checks:
            return False

        return all(checks)
