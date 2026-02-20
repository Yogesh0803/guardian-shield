"""
Firewall rule enforcement.
Actually blocks/allows traffic using OS-level firewall commands.
Supports Windows (netsh) and Linux (iptables).
"""

import sys
import subprocess
import logging
import time
from typing import Dict, Optional
from dataclasses import dataclass, field
from threading import Timer

logger = logging.getLogger(__name__)


@dataclass
class BlockRule:
    """An active block rule."""
    ip: str
    rule_name: str
    created_at: float
    expires_at: Optional[float] = None  # None = permanent
    app_name: str = ""
    reason: str = ""


class FirewallEnforcer:
    """Cross-platform firewall rule management."""

    def __init__(self, default_block_duration: int = 300):
        self.default_block_duration = default_block_duration
        self.active_rules: Dict[str, BlockRule] = {}
        self.platform = "windows" if sys.platform == "win32" else "linux"
        self._timers: Dict[str, Timer] = {}

    def block_ip(
        self,
        ip: str,
        duration: Optional[int] = None,
        app_name: str = "",
        reason: str = "",
    ) -> bool:
        """
        Block an IP address.

        Args:
            ip: IP address to block
            duration: Block duration in seconds (None = permanent)
            app_name: App that triggered the block
            reason: Reason for blocking (e.g., "DDoS detected")

        Returns: True if rule was applied successfully
        """
        if ip in self.active_rules:
            logger.debug(f"IP {ip} already blocked")
            return True

        rule_name = f"GuardianShield_Block_{ip.replace('.', '_')}"
        dur = duration or self.default_block_duration

        try:
            if self.platform == "windows":
                success = self._block_windows(ip, rule_name)
            else:
                success = self._block_linux(ip)

            if success:
                now = time.time()
                self.active_rules[ip] = BlockRule(
                    ip=ip,
                    rule_name=rule_name,
                    created_at=now,
                    expires_at=now + dur if dur else None,
                    app_name=app_name,
                    reason=reason,
                )

                # Set auto-expire timer
                if dur:
                    timer = Timer(dur, self._expire_rule, args=[ip])
                    timer.daemon = True
                    timer.start()
                    self._timers[ip] = timer

                logger.info(f"Blocked IP {ip} for {dur}s (reason: {reason})")
                return True

        except Exception as e:
            logger.error(f"Failed to block {ip}: {e}")

        return False

    def unblock_ip(self, ip: str) -> bool:
        """Remove block rule for an IP."""
        if ip not in self.active_rules:
            return True

        rule = self.active_rules[ip]

        try:
            if self.platform == "windows":
                success = self._unblock_windows(rule.rule_name)
            else:
                success = self._unblock_linux(ip)

            if success:
                del self.active_rules[ip]
                if ip in self._timers:
                    self._timers[ip].cancel()
                    del self._timers[ip]
                logger.info(f"Unblocked IP {ip}")
                return True

        except Exception as e:
            logger.error(f"Failed to unblock {ip}: {e}")

        return False

    def _expire_rule(self, ip: str):
        """Called when a temporary block expires."""
        logger.info(f"Block expired for IP {ip}")
        self.unblock_ip(ip)

    # ============ Windows (netsh) ============

    def _block_windows(self, ip: str, rule_name: str) -> bool:
        result = subprocess.run(
            [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name={rule_name}",
                "dir=out",
                "action=block",
                f"remoteip={ip}",
                "protocol=any",
            ],
            capture_output=True, text=True,
        )
        return result.returncode == 0

    def _unblock_windows(self, rule_name: str) -> bool:
        result = subprocess.run(
            [
                "netsh", "advfirewall", "firewall", "delete", "rule",
                f"name={rule_name}",
            ],
            capture_output=True, text=True,
        )
        return result.returncode == 0

    # ============ Linux (iptables) ============

    def _block_linux(self, ip: str) -> bool:
        result = subprocess.run(
            ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"],
            capture_output=True, text=True,
        )
        return result.returncode == 0

    def _unblock_linux(self, ip: str) -> bool:
        result = subprocess.run(
            ["iptables", "-D", "OUTPUT", "-d", ip, "-j", "DROP"],
            capture_output=True, text=True,
        )
        return result.returncode == 0

    # ============ Status ============

    def get_active_rules(self) -> list:
        """Get all active block rules."""
        now = time.time()
        return [
            {
                "ip": r.ip,
                "app_name": r.app_name,
                "reason": r.reason,
                "created_at": r.created_at,
                "expires_in": int(r.expires_at - now) if r.expires_at else None,
                "permanent": r.expires_at is None,
            }
            for r in self.active_rules.values()
        ]

    def cleanup(self):
        """Remove all active rules (called on shutdown)."""
        for ip in list(self.active_rules.keys()):
            self.unblock_ip(ip)
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()
