"""
Live packet capture using Scapy.
Captures TCP/UDP/ICMP packets and groups them into flows.
"""

import time
import threading
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional

from scapy.all import sniff, IP, TCP, UDP, ICMP, conf

logger = logging.getLogger(__name__)


@dataclass
class PacketInfo:
    """Parsed packet metadata."""
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str  # TCP, UDP, ICMP
    length: int
    flags: str = ""
    payload_size: int = 0
    ttl: int = 0
    header_length: int = 0


@dataclass
class Flow:
    """A network flow (5-tuple grouped packets)."""
    flow_id: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packets: List[PacketInfo] = field(default_factory=list)
    start_time: float = 0.0
    last_time: float = 0.0

    @property
    def duration(self) -> float:
        return self.last_time - self.start_time if self.packets else 0.0

    @property
    def total_bytes(self) -> int:
        return sum(p.length for p in self.packets)

    @property
    def packet_count(self) -> int:
        return len(self.packets)

    def add_packet(self, pkt: PacketInfo):
        if not self.packets:
            self.start_time = pkt.timestamp
        self.last_time = pkt.timestamp
        self.packets.append(pkt)


class PacketCapture:
    """Captures live network packets and groups them into flows."""

    def __init__(
        self,
        interface: str = "",
        capture_filter: str = "ip",
        flow_timeout: int = 10,
        buffer_size: int = 100,
    ):
        self.interface = interface or conf.iface
        self.capture_filter = capture_filter
        self.flow_timeout = flow_timeout
        self.buffer_size = buffer_size

        self._active_flows: Dict[str, Flow] = {}
        self._lock = threading.Lock()
        self._running = False
        self._on_flow_complete: Optional[Callable[[Flow], None]] = None
        self._capture_thread: Optional[threading.Thread] = None
        self._cleanup_thread: Optional[threading.Thread] = None

        # Stats
        self.total_packets = 0
        self.total_bytes = 0
        self.total_flows = 0

    def on_flow_complete(self, callback: Callable[[Flow], None]):
        """Register callback for when a flow is complete (timed out)."""
        self._on_flow_complete = callback

    def start(self):
        """Start packet capture in a background thread."""
        if self._running:
            return
        self._running = True

        self._capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._capture_thread.start()

        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

        logger.info(f"Packet capture started on interface: {self.interface}")

    def stop(self):
        """Stop packet capture."""
        self._running = False
        # Flush remaining flows
        with self._lock:
            for flow in self._active_flows.values():
                if self._on_flow_complete and flow.packet_count > 0:
                    self._on_flow_complete(flow)
            self._active_flows.clear()
        logger.info("Packet capture stopped")

    def _capture_loop(self):
        """Main capture loop using Scapy sniff."""
        try:
            sniff(
                iface=self.interface,
                filter=self.capture_filter,
                prn=self._process_packet,
                store=False,
                stop_filter=lambda _: not self._running,
            )
        except PermissionError:
            logger.error(
                "Permission denied: packet capture requires admin/root privileges. "
                "Run with elevated permissions."
            )
        except Exception as e:
            logger.error(f"Capture error: {e}")

    def _cleanup_loop(self):
        """Periodically flush timed-out flows."""
        while self._running:
            time.sleep(self.flow_timeout / 2)
            self._flush_expired_flows()

    def _process_packet(self, pkt):
        """Process a single captured packet."""
        if not pkt.haslayer(IP):
            return

        ip = pkt[IP]
        pkt_info = PacketInfo(
            timestamp=float(pkt.time),
            src_ip=ip.src,
            dst_ip=ip.dst,
            src_port=0,
            dst_port=0,
            protocol="OTHER",
            length=len(pkt),
            ttl=ip.ttl,
            header_length=ip.ihl * 4,
        )

        if pkt.haslayer(TCP):
            tcp = pkt[TCP]
            pkt_info.src_port = tcp.sport
            pkt_info.dst_port = tcp.dport
            pkt_info.protocol = "TCP"
            pkt_info.flags = str(tcp.flags)
            pkt_info.payload_size = len(tcp.payload) if tcp.payload else 0
        elif pkt.haslayer(UDP):
            udp = pkt[UDP]
            pkt_info.src_port = udp.sport
            pkt_info.dst_port = udp.dport
            pkt_info.protocol = "UDP"
            pkt_info.payload_size = len(udp.payload) if udp.payload else 0
        elif pkt.haslayer(ICMP):
            pkt_info.protocol = "ICMP"

        # Build flow ID (5-tuple)
        flow_id = f"{pkt_info.src_ip}:{pkt_info.src_port}-{pkt_info.dst_ip}:{pkt_info.dst_port}-{pkt_info.protocol}"

        with self._lock:
            if flow_id not in self._active_flows:
                self._active_flows[flow_id] = Flow(
                    flow_id=flow_id,
                    src_ip=pkt_info.src_ip,
                    dst_ip=pkt_info.dst_ip,
                    src_port=pkt_info.src_port,
                    dst_port=pkt_info.dst_port,
                    protocol=pkt_info.protocol,
                )
            self._active_flows[flow_id].add_packet(pkt_info)

        self.total_packets += 1
        self.total_bytes += pkt_info.length

    def _flush_expired_flows(self):
        """Flush flows that have been inactive longer than flow_timeout."""
        now = time.time()
        expired = []

        with self._lock:
            for flow_id, flow in self._active_flows.items():
                if now - flow.last_time > self.flow_timeout:
                    expired.append(flow_id)

            for flow_id in expired:
                flow = self._active_flows.pop(flow_id)
                self.total_flows += 1
                if self._on_flow_complete and flow.packet_count > 0:
                    self._on_flow_complete(flow)

    def get_stats(self) -> dict:
        """Return capture statistics."""
        with self._lock:
            active = len(self._active_flows)
        return {
            "total_packets": self.total_packets,
            "total_bytes": self.total_bytes,
            "total_flows": self.total_flows,
            "active_flows": active,
            "interface": self.interface,
            "running": self._running,
        }
