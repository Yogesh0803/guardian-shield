"""
Natural language policy parser.
Converts human-readable policy descriptions into structured rules.

Uses rule-based keyword extraction (no external LLM needed).
Deterministic, auditable, and works offline — ideal for security tooling.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ============ Keyword dictionaries ============

ACTION_KEYWORDS = {
    "block": ["block", "deny", "reject", "prevent", "stop", "forbid", "restrict", "disallow", "drop"],
    "unblock": ["allow", "permit", "enable", "accept", "unblock", "whitelist", "let"],
}

PROTOCOL_KEYWORDS = {
    "TCP": ["tcp"],
    "UDP": ["udp"],
    "ICMP": ["icmp", "ping"],
}

TIME_PATTERNS = {
    r"after (\d{1,2})\s*(am|pm|AM|PM)?": "after_hour",
    r"before (\d{1,2})\s*(am|pm|AM|PM)?": "before_hour",
    r"between (\d{1,2})\s*(am|pm)?\s*(?:and|to|-)\s*(\d{1,2})\s*(am|pm)?": "time_range",
    r"business hours": "business_hours",
    r"outside business hours": "outside_business_hours",
    r"night(?:time)?|late night": "night",
}

DAY_KEYWORDS = {
    "weekday": [0, 1, 2, 3, 4],
    "weekdays": [0, 1, 2, 3, 4],
    "weekend": [5, 6],
    "weekends": [5, 6],
    "monday": [0], "tuesday": [1], "wednesday": [2],
    "thursday": [3], "friday": [4], "saturday": [5], "sunday": [6],
}

COUNTRY_KEYWORDS = {
    "china": "CN", "chinese": "CN",
    "russia": "RU", "russian": "RU",
    "north korea": "KP",
    "iran": "IR", "iranian": "IR",
    "united states": "US", "us": "US", "usa": "US", "american": "US",
    "india": "IN", "indian": "IN",
    "germany": "DE", "german": "DE",
    "uk": "GB", "united kingdom": "GB", "british": "GB",
    "japan": "JP", "japanese": "JP",
    "brazil": "BR", "brazilian": "BR",
    "france": "FR", "french": "FR",
    "australia": "AU", "australian": "AU",
}

ATTACK_KEYWORDS = {
    "DDoS": ["ddos", "distributed denial"],
    "DoS": ["dos", "denial of service"],
    "BruteForce": ["brute force", "bruteforce", "brute-force"],
    "PortScan": ["port scan", "portscan", "port-scan"],
    "WebAttack": ["web attack", "sql injection", "xss", "cross-site"],
    "Botnet": ["botnet", "bot net"],
    "Infiltration": ["infiltration", "intrusion"],
    "Phishing": ["phishing", "phish"],
    "Malware": ["malware", "virus", "trojan", "ransomware"],
}


@dataclass
class ParsedPolicy:
    purpose: str = "block"
    domains: List[str] = field(default_factory=list)
    ips: List[str] = field(default_factory=list)
    ports: List[dict] = field(default_factory=list)
    app_names: List[str] = field(default_factory=list)
    time_range: Optional[dict] = None
    days_of_week: Optional[List[int]] = None
    geo_countries: Optional[List[str]] = None
    anomaly_threshold: Optional[float] = None
    attack_types: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    confidence: float = 0.0
    explanation: str = ""


class NLPPolicyParser:
    """Parses natural language policy descriptions into structured rules."""

    def parse(self, text: str) -> ParsedPolicy:
        """
        Parse a natural language policy description.

        Examples:
            "Block Chrome from accessing Russian IPs after 10PM"
            "Allow only TCP traffic on port 443 during business hours"
            "Block any app with anomaly score above 0.8"
            "Deny all DDoS and brute force attacks"
        """
        result = ParsedPolicy()
        text_lower = text.lower().strip()
        explanations = []

        # 1. Determine action (block/allow)
        result.purpose = self._extract_action(text_lower)
        explanations.append(f"Action: {result.purpose}")

        # 2. Extract app names
        apps = self._extract_apps(text_lower)
        if apps:
            result.app_names = apps
            explanations.append(f"Apps: {', '.join(apps)}")

        # 3. Extract IPs
        ips = self._extract_ips(text)
        if ips:
            result.ips = ips
            explanations.append(f"IPs: {', '.join(ips)}")

        # 4. Extract domains
        domains = self._extract_domains(text)
        if domains:
            result.domains = domains
            explanations.append(f"Domains: {', '.join(domains)}")

        # 5. Extract ports
        ports = self._extract_ports(text_lower)
        if ports:
            result.ports = ports
            explanations.append(f"Ports: {ports}")

        # 6. Extract time conditions
        time_range, days = self._extract_time(text_lower)
        if time_range:
            result.time_range = time_range
            explanations.append(f"Time: {time_range['start']} - {time_range['end']}")
        if days:
            result.days_of_week = days
            explanations.append(f"Days: {days}")

        # 7. Extract geo countries
        countries = self._extract_countries(text_lower)
        if countries:
            result.geo_countries = countries
            explanations.append(f"Countries: {', '.join(countries)}")

        # 8. Extract anomaly threshold
        threshold = self._extract_threshold(text_lower)
        if threshold is not None:
            result.anomaly_threshold = threshold
            explanations.append(f"Anomaly threshold: {threshold}")

        # 9. Extract attack types
        attacks = self._extract_attack_types(text_lower)
        if attacks:
            result.attack_types = attacks
            explanations.append(f"Attack types: {', '.join(attacks)}")

        # 10. Extract rate limit
        rate = self._extract_rate_limit(text_lower)
        if rate:
            result.rate_limit = rate
            explanations.append(f"Rate limit: {rate}/min")

        # Calculate confidence based on how many fields were extracted
        fields_found = sum([
            bool(result.app_names), bool(result.ips), bool(result.domains),
            bool(result.ports), bool(result.time_range), bool(result.geo_countries),
            bool(result.anomaly_threshold is not None), bool(result.attack_types),
            bool(result.rate_limit),
        ])
        result.confidence = min(0.5 + fields_found * 0.1, 1.0)
        result.explanation = "; ".join(explanations)

        return result

    def _extract_action(self, text: str) -> str:
        for action, keywords in ACTION_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    return action
        return "block"  # default

    def _extract_apps(self, text: str) -> List[str]:
        apps = []
        known_apps = [
            "chrome", "firefox", "brave", "edge", "safari", "opera",
            "python", "node", "java", "curl", "wget",
            "slack", "discord", "teams", "zoom", "spotify",
            "vscode", "code", "terminal", "powershell", "cmd",
        ]
        for app in known_apps:
            if app in text:
                apps.append(app)
        return apps

    def _extract_ips(self, text: str) -> List[str]:
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?\b'
        return re.findall(ip_pattern, text)

    def _extract_domains(self, text: str) -> List[str]:
        domain_pattern = r'\b(?:\*\.)?[a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?\b'
        candidates = re.findall(domain_pattern, text)
        # Filter out common words that match the pattern
        skip = {"e.g", "i.e", "etc.com"}
        return [d for d in candidates if d not in skip]

    def _extract_ports(self, text: str) -> List[dict]:
        ports = []
        # "port 80", "port 443", "ports 80 and 443"
        port_pattern = r'port[s]?\s+(\d+(?:\s*(?:,|and)\s*\d+)*)'
        matches = re.findall(port_pattern, text)
        for match in matches:
            for port_str in re.findall(r'\d+', match):
                port = int(port_str)
                if 1 <= port <= 65535:
                    # Check for protocol near the port mention
                    protocols = []
                    for proto, kws in PROTOCOL_KEYWORDS.items():
                        for kw in kws:
                            if kw in text:
                                protocols.append(proto)
                    ports.append({"port": port, "protocol": protocols or ["TCP", "UDP"]})
        return ports

    def _extract_time(self, text: str) -> Tuple[Optional[dict], Optional[List[int]]]:
        time_range = None
        days = None

        if "business hours" in text:
            if "outside" in text:
                time_range = {"start": "18:00", "end": "09:00"}
            else:
                time_range = {"start": "09:00", "end": "18:00"}

        if "night" in text or "late night" in text:
            time_range = {"start": "22:00", "end": "06:00"}

        # "after 10pm"
        after_match = re.search(r'after (\d{1,2})\s*(am|pm)?', text)
        if after_match:
            hour = int(after_match.group(1))
            period = after_match.group(2)
            if period and period.lower() == "pm" and hour < 12:
                hour += 12
            time_range = {"start": f"{hour:02d}:00", "end": "23:59"}

        # "before 6am"
        before_match = re.search(r'before (\d{1,2})\s*(am|pm)?', text)
        if before_match:
            hour = int(before_match.group(1))
            period = before_match.group(2)
            if period and period.lower() == "pm" and hour < 12:
                hour += 12
            time_range = {"start": "00:00", "end": f"{hour:02d}:00"}

        # Days of week
        for day_kw, day_nums in DAY_KEYWORDS.items():
            if day_kw in text:
                days = day_nums
                break

        return time_range, days

    def _extract_countries(self, text: str) -> List[str]:
        countries = []
        for name, code in COUNTRY_KEYWORDS.items():
            if name in text:
                if code not in countries:
                    countries.append(code)
        return countries

    def _extract_threshold(self, text: str) -> Optional[float]:
        patterns = [
            r'anomaly\s*(?:score)?\s*(?:above|over|greater than|>)\s*(\d*\.?\d+)',
            r'threshold\s*(?:of|:)?\s*(\d*\.?\d+)',
            r'score\s*>\s*(\d*\.?\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return None

    def _extract_attack_types(self, text: str) -> List[str]:
        attacks = []
        for attack_type, keywords in ATTACK_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    if attack_type not in attacks:
                        attacks.append(attack_type)
                    break
        return attacks

    def _extract_rate_limit(self, text: str) -> Optional[int]:
        patterns = [
            r'(?:rate|request)\s*(?:limit)?\s*(?:>|above|over|exceeds?)\s*(\d+)',
            r'more than (\d+)\s*(?:requests?|connections?)\s*(?:per|/)\s*(?:min|minute)',
            r'(\d+)\s*(?:requests?|connections?)\s*(?:per|/)\s*(?:min|minute)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return None
