"""
Identify which application owns a network connection using psutil.
Maps connections to PIDs to process names.
"""

import logging
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

import psutil

logger = logging.getLogger(__name__)


@dataclass
class AppInfo:
    pid: int
    name: str
    exe: str
    trust_score: float = 0.5  # 0.0 (untrusted) to 1.0 (trusted)


# Well-known system processes that are generally trusted
TRUSTED_APPS = {
    "svchost.exe", "System", "lsass.exe", "csrss.exe", "services.exe",
    "systemd", "kworker", "NetworkManager",
}

# Well-known user apps
KNOWN_APPS = {
    "chrome.exe": 0.7, "firefox.exe": 0.7, "msedge.exe": 0.7,
    "brave.exe": 0.7, "opera.exe": 0.7, "safari": 0.7,
    "code.exe": 0.8, "Code.exe": 0.8,  # VS Code
    "python.exe": 0.6, "python3": 0.6, "python": 0.6,
    "node.exe": 0.6, "node": 0.6,
    "java.exe": 0.5, "java": 0.5,
    "slack.exe": 0.7, "Slack": 0.7,
    "discord.exe": 0.6, "Discord": 0.6,
    "spotify.exe": 0.7, "Spotify": 0.7,
    "Teams.exe": 0.7, "zoom.exe": 0.6,
    "curl.exe": 0.5, "curl": 0.5, "wget": 0.5,
}


class AppIdentifier:
    """Identifies the application associated with a network connection."""

    def __init__(self):
        self._cache: Dict[Tuple[str, int], AppInfo] = {}
        self._history: Dict[str, int] = {}  # app_name -> connection count

    def identify(self, src_ip: str, src_port: int, dst_ip: str, dst_port: int, protocol: str) -> Optional[AppInfo]:
        """Find which process owns the connection."""
        cache_key = (src_ip, src_port)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            proto_map = {"TCP": "tcp", "UDP": "udp", "tcp": "tcp", "udp": "udp"}
            kind = proto_map.get(protocol, "inet")

            connections = psutil.net_connections(kind=kind)
            for conn in connections:
                if not conn.laddr:
                    continue
                local_ip, local_port = conn.laddr
                if local_port == src_port and (local_ip == src_ip or local_ip in ("0.0.0.0", "::", "127.0.0.1")):
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            name = proc.name()
                            exe = proc.exe() if proc.exe() else name

                            trust = self._compute_trust(name)
                            app_info = AppInfo(pid=conn.pid, name=name, exe=exe, trust_score=trust)

                            self._cache[cache_key] = app_info
                            self._history[name] = self._history.get(name, 0) + 1
                            return app_info
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
        except Exception as e:
            logger.debug(f"App identification failed: {e}")

        return None

    def _compute_trust(self, name: str) -> float:
        """Compute trust score for an application."""
        if name in TRUSTED_APPS:
            return 0.9
        if name in KNOWN_APPS:
            return KNOWN_APPS[name]

        # Unknown process — lower trust, especially if rarely seen
        history_count = self._history.get(name, 0)
        if history_count > 100:
            return 0.5  # frequently seen
        elif history_count > 10:
            return 0.4
        else:
            return 0.3  # rarely seen, more suspicious

    def get_stats(self) -> Dict[str, int]:
        """Return app connection counts."""
        return dict(self._history)

    def clear_cache(self):
        """Clear the connection cache."""
        self._cache.clear()
