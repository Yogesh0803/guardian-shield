"""
Policy enforcement service.
Blocks/unblocks domains by modifying the Windows hosts file.
Blocks/unblocks IPs using Windows Firewall (netsh).
"""

import os
import sys
import socket
import subprocess
import logging
import re
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts" if sys.platform == "win32" else "/etc/hosts"
MARKER_START = "# >>> GuardianShield Blocked Domains"
MARKER_END = "# <<< GuardianShield Blocked Domains"


class PolicyEnforcer:
    """Enforces policies by modifying hosts file and firewall rules."""

    def __init__(self):
        self.blocked_domains: Dict[str, List[str]] = {}  # policy_id -> [domains]
        self.blocked_ips: Dict[str, List[str]] = {}  # policy_id -> [ips]
        self._initialized = False

    def sync_from_db(self, db_session):
        """Load all active 'block' policies from the DB and sync hosts file.

        Always rewrites the hosts file to match current DB state,
        cleaning up any stale entries from deleted/deactivated policies.
        """
        if self._initialized:
            return
        self._initialized = True
        try:
            from app.models.policy import Policy
            policies = db_session.query(Policy).filter(
                Policy.is_active == True,
                Policy.purpose == "block",
            ).all()
            # Reset in-memory state to match DB exactly
            self.blocked_domains.clear()
            self.blocked_ips.clear()
            for p in policies:
                if p.conditions and isinstance(p.conditions, dict):
                    domains = p.conditions.get("domains", [])
                    if domains:
                        self.blocked_domains[p.id] = domains
                    ips = p.conditions.get("ips", [])
                    if ips:
                        self.blocked_ips[p.id] = ips
            # Always rewrite hosts file to clean up stale entries
            self._rewrite_hosts_file()
            logger.info(f"Synced from DB: {len(self.blocked_domains)} domain policies, {len(self.blocked_ips)} IP policies")
        except Exception as e:
            logger.error(f"Failed to sync policies from DB: {e}")

    def enforce_policy(self, policy_id: str, purpose: str, conditions: dict) -> dict:
        """
        Enforce a policy. Returns status dict.

        For 'block' purpose: blocks domains/IPs
        For 'unblock' purpose: unblocks domains/IPs
        """
        if not conditions:
            return {"status": "no_conditions", "enforced": False}

        results = {}
        domains = conditions.get("domains", [])
        ips = conditions.get("ips", [])

        if purpose == "block":
            if domains:
                # 1. Resolve domain IPs FIRST (before hosts file blocks DNS)
                resolved_ips = self._resolve_domain_ips(domains)
                logger.warning(f"Resolved IPs for {domains}: {resolved_ips}")
                # 2. Block via hosts file (for browser/DNS-based access)
                success = self._block_domains(policy_id, domains)
                results["domains"] = {"blocked": domains, "success": success}
                # 3. Block resolved IPs via firewall (for apps using direct IPs)
                if resolved_ips:
                    ip_success = self._block_ips(policy_id, resolved_ips)
                    logger.warning(f"Firewall IP block result: {ip_success}")
                    results["resolved_ips"] = {"blocked": resolved_ips, "success": ip_success}
            if ips:
                success = self._block_ips(policy_id, ips)
                results["ips"] = {"blocked": ips, "success": success}
        elif purpose == "unblock":
            if domains:
                success = self._unblock_domains_list(domains)
                results["domains"] = {"unblocked": domains, "success": success}
            if ips:
                success = self._unblock_ips_list(ips)
                results["ips"] = {"unblocked": ips, "success": success}

        enforced = any(r.get("success") for r in results.values())
        return {"status": "enforced" if enforced else "failed", "enforced": enforced, "details": results}

    def unenforce_policy(self, policy_id: str) -> dict:
        """Remove all enforcement for a policy (when deleted or toggled off)."""
        results = {}

        # Remove blocked domains
        if policy_id in self.blocked_domains:
            domains = self.blocked_domains.pop(policy_id)
            success = self._unblock_domains_list(domains)
            results["domains"] = {"unblocked": domains, "success": success}

        # Remove blocked IPs from in-memory state
        if policy_id in self.blocked_ips:
            self.blocked_ips.pop(policy_id)

        # ALWAYS try to delete the firewall rule by policy_id
        # (handles case where backend restarted and in-memory state was lost)
        rule_name = f"GuardianShield_{policy_id[:8]}"
        fw_success = self._delete_firewall_rule(rule_name)
        results["firewall"] = {"rule": rule_name, "deleted": fw_success}

        self._rewrite_hosts_file()
        return {"status": "unenforced", "details": results}

    # ============ DNS resolution for app-level blocking ============

    def _resolve_domain_ips(self, domains: List[str]) -> List[str]:
        """Resolve domains to IPs using public DNS (bypasses local hosts file)."""
        resolved = set()
        for domain in domains:
            variants = [domain, f"www.{domain}"]
            if "whatsapp" in domain:
                variants += [f"web.{domain}", f"pps.{domain}", f"mmg.{domain}", f"media.{domain}"]
            elif "telegram" in domain:
                variants += [f"api.{domain}", f"web.{domain}", f"core.{domain}"]
            for d in variants:
                try:
                    # Use nslookup with Google DNS to bypass local hosts file
                    result = subprocess.run(
                        ["nslookup", d, "8.8.8.8"],
                        capture_output=True, text=True, timeout=5,
                    )
                    # Parse all IPv4 addresses from nslookup output
                    in_answer = False
                    for line in result.stdout.splitlines():
                        if "Name:" in line:
                            in_answer = True
                            continue
                        if in_answer:
                            # Match any IPv4 address on the line
                            ipv4s = re.findall(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', line)
                            for ip in ipv4s:
                                if not ip.startswith("127.") and ip != "8.8.8.8":
                                    resolved.add(ip)
                except (subprocess.TimeoutExpired, OSError):
                    pass
        logger.info(f"Resolved {len(resolved)} IPs from {len(domains)} domains: {resolved}")
        return list(resolved)

    # ============ Domain blocking via hosts file ============

    def _block_domains(self, policy_id: str, domains: List[str]) -> bool:
        """Block domains by adding them to hosts file."""
        self.blocked_domains[policy_id] = domains
        return self._rewrite_hosts_file()

    def _unblock_domains_list(self, domains: List[str]) -> bool:
        """Remove specific domains from all policies' blocked lists."""
        for pid in list(self.blocked_domains.keys()):
            self.blocked_domains[pid] = [
                d for d in self.blocked_domains[pid] if d not in domains
            ]
            if not self.blocked_domains[pid]:
                del self.blocked_domains[pid]
        return self._rewrite_hosts_file()

    def _rewrite_hosts_file(self) -> bool:
        """Rewrite the GuardianShield section of the hosts file."""
        try:
            # Read current hosts file
            with open(HOSTS_PATH, "r") as f:
                content = f.read()

            # Remove existing GuardianShield block
            pattern = re.compile(
                rf"{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}\n?",
                re.DOTALL,
            )
            content = pattern.sub("", content).rstrip("\n")

            # Collect all domains to block
            all_domains = set()
            for domains in self.blocked_domains.values():
                all_domains.update(domains)

            # Add new block if there are domains
            if all_domains:
                block_lines = [f"\n{MARKER_START}"]
                for domain in sorted(all_domains):
                    # Block the domain and common subdomains
                    block_lines.append(f"127.0.0.1 {domain}")
                    block_lines.append(f"127.0.0.1 www.{domain}")
                    # For YouTube specifically, block key subdomains
                    if "youtube" in domain:
                        block_lines.append(f"127.0.0.1 m.{domain}")
                        block_lines.append(f"127.0.0.1 music.{domain}")
                block_lines.append(MARKER_END)
                content += "\n".join(block_lines) + "\n"
            else:
                content += "\n"

            # Write back
            with open(HOSTS_PATH, "w") as f:
                f.write(content)

            # Flush DNS cache on Windows (try direct, then elevated)
            if sys.platform == "win32":
                r = subprocess.run(
                    ["ipconfig", "/flushdns"],
                    capture_output=True, timeout=10,
                )
                if r.returncode != 0:
                    subprocess.Popen(
                        ["powershell", "-Command",
                         'Start-Process cmd.exe -Verb RunAs -WindowStyle Hidden -ArgumentList "/c","ipconfig /flushdns"'],
                    )

            logger.info(f"Hosts file updated: {len(all_domains)} domains blocked")
            return True

        except PermissionError:
            logger.error(
                "Permission denied writing to hosts file. "
                "Run the backend as Administrator to enforce domain blocking."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to update hosts file: {e}")
            return False

    # ============ IP blocking via Windows Firewall ============

    def _run_elevated(self, cmd: str) -> bool:
        """Run a command with admin privileges via UAC elevation."""
        import time
        try:
            # First try direct (works if already admin)
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Direct command succeeded: {cmd[:60]}")
                return True

            # Not admin — write batch file and elevate
            bat_path = r"C:\Users\wwwyo\AppData\Local\Temp\gs_fw_cmd.bat"
            done_path = r"C:\Users\wwwyo\AppData\Local\Temp\gs_fw_done.txt"

            if os.path.exists(done_path):
                os.remove(done_path)

            with open(bat_path, "w") as f:
                f.write(f"@echo off\n{cmd}\necho DONE > \"{done_path}\"\n")

            # Use Start-Process -Verb RunAs -Wait with the batch file path
            ps_cmd = (
                f'Start-Process cmd.exe -Verb RunAs -Wait '
                f'-ArgumentList "/c","{bat_path}"'
            )
            subprocess.Popen(
                ["powershell", "-Command", ps_cmd],
            )

            # Wait for completion
            for _ in range(25):
                time.sleep(1)
                if os.path.exists(done_path):
                    os.remove(done_path)
                    logger.info(f"Elevated command completed: {cmd[:60]}")
                    return True

            logger.warning("Elevated command timed out")
            return False
        except Exception as e:
            logger.error(f"Elevated command error: {e}")
            return False

    def _block_ips(self, policy_id: str, ips: List[str]) -> bool:
        """Block IPs using Windows Firewall."""
        self.blocked_ips[policy_id] = ips
        if not ips:
            return True

        rule_name = f"GuardianShield_{policy_id[:8]}"
        ip_list = ",".join(ips)

        if sys.platform == "win32":
            # Try direct netsh first (works if backend runs as admin)
            cmd = f'netsh advfirewall firewall add rule name={rule_name} dir=out action=block remoteip={ip_list} protocol=any'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                logger.info(f"Firewall rule '{rule_name}' created blocking {len(ips)} IPs")
                return True

            # Fallback: try elevated PowerShell
            logger.warning(f"Direct netsh failed ({result.stderr.strip()}), trying elevated...")
            return self._run_elevated(cmd)
        else:
            success = True
            for ip in ips:
                r = subprocess.run(
                    ["iptables", "-A", "OUTPUT", "-d", ip, "-j", "DROP"],
                    capture_output=True, timeout=10,
                )
                if r.returncode != 0:
                    success = False
            return success

    def _delete_firewall_rule(self, rule_name: str) -> bool:
        """Delete a specific Windows Firewall rule by name."""
        if sys.platform != "win32":
            return True
        cmd = f'netsh advfirewall firewall delete rule name={rule_name}'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Deleted firewall rule: {rule_name}")
            return True
        # Try elevated if direct fails
        logger.warning(f"Direct delete failed for {rule_name}, trying elevated...")
        return self._run_elevated(cmd)

    def _unblock_ips_list(self, ips: List[str]) -> bool:
        """Remove firewall rules for blocked IPs."""
        if not ips:
            return True

        if sys.platform == "win32":
            # Build commands to delete all GuardianShield rules
            cmds = []
            for pid in list(self.blocked_ips.keys()):
                rule_name = f"GuardianShield_{pid[:8]}"
                cmds.append(f'netsh advfirewall firewall delete rule name={rule_name}')
            if not cmds:
                return True
            return self._run_elevated(" & ".join(cmds))
        else:
            success = True
            for ip in ips:
                r = subprocess.run(
                    ["iptables", "-D", "OUTPUT", "-d", ip, "-j", "DROP"],
                    capture_output=True, timeout=10,
                )
                if r.returncode != 0:
                    success = False
            return success

    def get_status(self) -> dict:
        """Get current enforcement status."""
        all_domains = set()
        for domains in self.blocked_domains.values():
            all_domains.update(domains)
        all_ips = set()
        for ips in self.blocked_ips.values():
            all_ips.update(ips)
        return {
            "blocked_domains": sorted(all_domains),
            "blocked_ips": sorted(all_ips),
            "total_policies_enforced": len(self.blocked_domains) + len(self.blocked_ips),
        }


# Singleton instance
enforcer = PolicyEnforcer()
