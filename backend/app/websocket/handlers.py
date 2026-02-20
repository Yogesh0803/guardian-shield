import asyncio
import random
import uuid
import psutil
from datetime import datetime, timezone

from fastapi import WebSocket, WebSocketDisconnect

from app.websocket.manager import manager


def _get_real_network_stats():
    """Get real network usage from psutil."""
    counters = psutil.net_io_counters()
    return {
        "bytes_in": counters.bytes_recv,
        "bytes_out": counters.bytes_sent,
        "packets": counters.packets_recv + counters.packets_sent,
    }


def _get_real_connections():
    """Get real active connections from psutil."""
    connections = []
    seen = set()
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.status == "NONE" or not conn.laddr:
                continue

            # Get process name
            app_name = "unknown"
            if conn.pid:
                try:
                    proc = psutil.Process(conn.pid)
                    app_name = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            dst_ip = conn.raddr.ip if conn.raddr else "0.0.0.0"
            dst_port = conn.raddr.port if conn.raddr else 0

            # Deduplicate
            key = (conn.laddr.ip, conn.laddr.port, dst_ip, dst_port)
            if key in seen:
                continue
            seen.add(key)

            # Map status
            status = conn.status
            if status not in ("ESTABLISHED", "CLOSE_WAIT", "TIME_WAIT", "LISTEN"):
                status = "ESTABLISHED"

            connections.append({
                "id": str(uuid.uuid4()),
                "endpoint": "localhost",
                "app": app_name,
                "status": status,
                "src_ip": conn.laddr.ip,
                "src_port": conn.laddr.port,
                "dst_ip": dst_ip,
                "dst_port": dst_port,
                "protocol": "TCP" if conn.type == 1 else "UDP",
            })

            if len(connections) >= 50:
                break
    except (psutil.AccessDenied, OSError):
        pass

    return connections


# Track previous stats for delta calculation
_prev_stats = {"bytes_in": 0, "bytes_out": 0, "packets": 0}


async def websocket_network_endpoint(websocket: WebSocket):
    """WebSocket handler for real-time network data."""
    global _prev_stats
    await manager.connect(websocket, "network")

    # Initialize previous stats
    current = _get_real_network_stats()
    _prev_stats = current.copy()

    try:
        while True:
            # Get real network stats
            current = _get_real_network_stats()

            # Calculate deltas (traffic since last update)
            delta_in = max(0, current["bytes_in"] - _prev_stats["bytes_in"])
            delta_out = max(0, current["bytes_out"] - _prev_stats["bytes_out"])
            delta_packets = max(0, current["packets"] - _prev_stats["packets"])
            _prev_stats = current.copy()

            avg_packet_size = (delta_in + delta_out) / max(delta_packets, 1)

            # Send network_usage in the format the frontend expects
            usage_data = {
                "type": "network_usage",
                "data": {
                    "localhost": {
                        "id": "local-1",
                        "endpoint_id": "local-1",
                        "endpoint_name": "This Machine",
                        "bytes_in": delta_in,
                        "bytes_out": delta_out,
                        "packets": delta_packets,
                        "avg_packet_size": round(avg_packet_size, 2),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                },
            }
            await manager.send_personal_message(usage_data, websocket)

            # Also send real connections
            connections = _get_real_connections()
            conn_data = {
                "type": "connections",
                "data": connections,
            }
            await manager.send_personal_message(conn_data, websocket)

            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "network")


async def websocket_alerts_endpoint(websocket: WebSocket):
    """WebSocket handler for real-time alerts."""
    await manager.connect(websocket, "alerts")
    severities = ["low", "medium", "high", "critical"]
    categories = ["intrusion", "malware", "anomaly", "policy_violation", "data_leak"]
    attack_types = [
        "DDoS", "SQL Injection", "XSS", "Port Scan",
        "Brute Force", "DNS Tunneling", "Data Exfiltration",
    ]
    try:
        while True:
            # Occasionally send an alert (simulated)
            if random.random() < 0.3:
                severity = random.choice(severities)
                category = random.choice(categories)
                data = {
                    "type": "new_alert",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "severity": severity,
                    "category": category,
                    "attack_type": random.choice(attack_types) if random.random() > 0.3 else None,
                    "message": f"Detected {category} event with {severity} severity",
                    "confidence": round(random.uniform(0.5, 0.99), 3),
                }
                await manager.send_personal_message(data, websocket)
            await asyncio.sleep(3)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "alerts")


async def websocket_predictions_endpoint(websocket: WebSocket):
    """WebSocket handler for real-time ML predictions."""
    await manager.connect(websocket, "predictions")
    attack_types = [
        "DDoS", "SQL Injection", "XSS", "Port Scan",
        "Brute Force", "Man-in-the-Middle", "DNS Tunneling",
        "Data Exfiltration", "Malware C2",
    ]
    app_names = ["nginx", "postgres", "redis", "node-api", "python-worker"]
    try:
        while True:
            anomaly_score = round(random.uniform(0.0, 1.0), 4)
            is_anomaly = anomaly_score > 0.7
            action = "block" if anomaly_score > 0.85 else ("alert" if is_anomaly else "allow")
            attack_type = random.choice(attack_types) if is_anomaly else "Benign"
            src_ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
            dst_ip = f"10.0.{random.randint(1, 10)}.{random.randint(1, 254)}"
            app_name = random.choice(app_names)

            data = {
                "type": "prediction",
                "data": {
                    "id": str(uuid.uuid4()),
                    "anomaly_score": anomaly_score,
                    "attack_type": attack_type,
                    "confidence": round(random.uniform(0.6, 0.99), 3) if is_anomaly else round(random.uniform(0.85, 0.99), 3),
                    "action": action,
                    "app_name": app_name,
                    "src_ip": src_ip,
                    "dst_ip": dst_ip,
                    "context": {
                        "app_name": app_name,
                        "process_id": random.randint(1000, 65000),
                        "app_trust_score": round(random.uniform(0.3, 1.0), 2),
                        "hour": datetime.now().hour,
                        "day_of_week": datetime.now().weekday(),
                        "is_business_hours": 9 <= datetime.now().hour <= 17,
                        "rate_deviation": round(random.uniform(-1.0, 3.0), 2),
                        "size_deviation": round(random.uniform(-0.5, 2.5), 2),
                        "destination_novelty": round(random.uniform(0.0, 1.0), 2),
                        "dest_country": random.choice(["United States", "Germany", "China", "Russia", "India", "Japan"]),
                        "dest_country_code": random.choice(["US", "DE", "CN", "RU", "IN", "JP"]),
                        "is_geo_anomaly": random.random() > 0.85,
                        "src_ip": src_ip,
                        "dst_ip": dst_ip,
                        "dst_port": random.choice([80, 443, 22, 3306, 5432, 8080]),
                        "protocol": random.choice(["TCP", "UDP"]),
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
            await manager.send_personal_message(data, websocket)
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        manager.disconnect(websocket, "predictions")
