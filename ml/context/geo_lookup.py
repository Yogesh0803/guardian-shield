"""
IP geolocation lookup using MaxMind GeoLite2 database.
Provides country and ASN information for destination IPs.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class GeoContext:
    country: str
    country_code: str
    is_geo_anomaly: bool  # unusual destination for this source


# Private/reserved IP ranges that don't need geo lookup
PRIVATE_PREFIXES = ("10.", "172.16.", "172.17.", "172.18.", "172.19.",
                    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
                    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
                    "172.30.", "172.31.", "192.168.", "127.", "0.", "169.254.")


class GeoLookup:
    """IP geolocation with anomaly detection per source."""

    def __init__(self, db_path: str = ""):
        self._reader = None
        self._cache: Dict[str, str] = {}
        self._source_countries: Dict[str, Set[str]] = {}  # source -> set of countries

        if db_path:
            try:
                import geoip2.database
                self._reader = geoip2.database.Reader(db_path)
                logger.info(f"GeoIP database loaded from {db_path}")
            except Exception as e:
                logger.warning(f"GeoIP database not available: {e}. Using fallback.")

    def lookup(self, dst_ip: str, source_key: str = "") -> GeoContext:
        """
        Look up geolocation for a destination IP.

        Args:
            dst_ip: Destination IP address
            source_key: Source identifier (app name) for anomaly detection
        """
        # Skip private IPs
        if any(dst_ip.startswith(p) for p in PRIVATE_PREFIXES):
            return GeoContext(country="Local", country_code="--", is_geo_anomaly=False)

        # Check cache
        if dst_ip in self._cache:
            country_code = self._cache[dst_ip]
        else:
            country_code = self._resolve(dst_ip)
            self._cache[dst_ip] = country_code

        country = self._code_to_name(country_code)

        # Geo anomaly detection
        is_anomaly = False
        if source_key:
            if source_key not in self._source_countries:
                self._source_countries[source_key] = set()

            known_countries = self._source_countries[source_key]
            if known_countries and country_code not in known_countries:
                is_anomaly = True  # This source hasn't contacted this country before

            self._source_countries[source_key].add(country_code)

        return GeoContext(
            country=country,
            country_code=country_code,
            is_geo_anomaly=is_anomaly,
        )

    def _resolve(self, ip: str) -> str:
        """Resolve IP to country code."""
        if self._reader:
            try:
                response = self._reader.country(ip)
                return response.country.iso_code or "??"
            except Exception:
                return "??"
        return "??"

    def _code_to_name(self, code: str) -> str:
        """Convert country code to name."""
        names = {
            "US": "United States", "CN": "China", "RU": "Russia",
            "GB": "United Kingdom", "DE": "Germany", "FR": "France",
            "JP": "Japan", "IN": "India", "BR": "Brazil", "AU": "Australia",
            "CA": "Canada", "KR": "South Korea", "NL": "Netherlands",
            "SG": "Singapore", "IE": "Ireland", "--": "Local", "??": "Unknown",
        }
        return names.get(code, code)

    def close(self):
        if self._reader:
            self._reader.close()
