import uuid
import random
from datetime import datetime, timezone, timedelta

import bcrypt
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.endpoint import Endpoint
from app.models.application import Application
from app.models.policy import Policy
from app.models.alert import Alert
from app.models.network_usage import NetworkUsage
from app.models.ml_prediction import MLPrediction



def seed_database(db: Session) -> None:
    """Seed the database with sample data. Only runs if the DB is empty."""

    # Check if data already exists
    if db.query(User).first() is not None:
        return

    now = datetime.now(timezone.utc)

    # --- Admin user ---
    admin = User(
        id=str(uuid.uuid4()),
        email="admin@guardian.com",
        hashed_password=bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8"),
        name="Admin User",
        role="admin",
        created_at=now - timedelta(days=30),
    )
    db.add(admin)

    # --- Endpoints ---
    endpoint_data = [
        ("Web Server Alpha", "10.0.1.10"),
        ("Database Cluster Beta", "10.0.2.20"),
        ("API Gateway Gamma", "10.0.3.30"),
        ("File Server Delta", "10.0.4.40"),
        ("Mail Server Epsilon", "10.0.5.50"),
    ]
    endpoints = []
    for name, ip in endpoint_data:
        ep = Endpoint(
            id=str(uuid.uuid4()),
            name=name,
            ip_address=ip,
            status=random.choice(["active", "active", "active", "warning"]),
            created_at=now - timedelta(days=random.randint(10, 60)),
        )
        db.add(ep)
        endpoints.append(ep)

    # --- Applications (3 per endpoint) ---
    app_templates = [
        ("nginx", "nginx"),
        ("PostgreSQL", "postgres"),
        ("Redis Cache", "redis-server"),
        ("Node API", "node"),
        ("Python Worker", "python3"),
        ("Apache Kafka", "kafka"),
        ("Elasticsearch", "elasticsearch"),
        ("Docker Engine", "dockerd"),
        ("HAProxy", "haproxy"),
        ("MongoDB", "mongod"),
        ("RabbitMQ", "rabbitmq-server"),
        ("Memcached", "memcached"),
        ("Prometheus", "prometheus"),
        ("Grafana", "grafana-server"),
        ("Consul", "consul"),
    ]
    all_apps = []
    for i, ep in enumerate(endpoints):
        for j in range(3):
            tmpl = app_templates[i * 3 + j]
            app = Application(
                id=str(uuid.uuid4()),
                name=tmpl[0],
                process_name=tmpl[1],
                status=random.choice(["running", "running", "running", "stopped"]),
                endpoint_id=ep.id,
                created_at=now - timedelta(days=random.randint(1, 30)),
            )
            db.add(app)
            all_apps.append(app)

    # --- Policies (10 total) ---
    policy_templates = [
        ("Block External SSH", "Block all SSH traffic from external sources", "security",
         {"field": "port", "operator": "equals", "value": 22, "action": "block"}),
        ("Rate Limit API", "Limit API requests to 1000/min per IP", "rate_limiting",
         {"field": "request_rate", "operator": "greater_than", "value": 1000, "action": "throttle"}),
        ("Allow HTTPS Only", "Only allow encrypted HTTPS traffic", "compliance",
         {"field": "protocol", "operator": "equals", "value": "HTTPS", "action": "allow"}),
        ("Block Known Malware IPs", "Block traffic from known malicious IP addresses", "threat_prevention",
         {"field": "source_ip", "operator": "in_list", "value": "threat_intel_feed", "action": "block"}),
        ("Monitor Large Transfers", "Monitor data transfers exceeding 100MB", "data_loss_prevention",
         {"field": "bytes_out", "operator": "greater_than", "value": 104857600, "action": "monitor"}),
        ("Block SQL Injection", "Block requests containing SQL injection patterns", "app_security",
         {"field": "payload", "operator": "matches", "value": "sql_injection_pattern", "action": "block"}),
        ("Restrict Admin Access", "Restrict admin panel access to internal IPs", "access_control",
         {"field": "source_ip", "operator": "in_range", "value": "10.0.0.0/8", "action": "allow"}),
        ("Log DNS Queries", "Log all DNS queries for analysis", "monitoring",
         {"field": "protocol", "operator": "equals", "value": "DNS", "action": "log"}),
        ("Block Tor Exit Nodes", "Block traffic from known Tor exit nodes", "threat_prevention",
         {"field": "source_ip", "operator": "in_list", "value": "tor_exit_nodes", "action": "block"}),
        ("Bandwidth Throttle", "Throttle bandwidth during peak hours", "performance",
         {"field": "bandwidth", "operator": "greater_than", "value": 500000000, "action": "throttle"}),
    ]
    for i, (name, desc, purpose, conditions) in enumerate(policy_templates):
        ep = endpoints[i % len(endpoints)]
        policy = Policy(
            id=str(uuid.uuid4()),
            name=name,
            description=desc,
            purpose=purpose,
            conditions=conditions,
            endpoint_id=ep.id,
            is_active=random.choice([True, True, True, False]),
            created_at=now - timedelta(days=random.randint(1, 20)),
        )
        db.add(policy)

    # --- Alerts (50 total) ---
    severities = ["low", "medium", "high", "critical"]
    severity_weights = [0.3, 0.35, 0.25, 0.1]
    categories = ["intrusion", "malware", "anomaly", "policy_violation", "data_leak", "authentication"]
    attack_types = [
        "DDoS", "SQL Injection", "XSS", "Port Scan", "Brute Force",
        "Man-in-the-Middle", "DNS Tunneling", "Data Exfiltration",
    ]
    alert_messages = [
        "Unusual outbound traffic detected from endpoint",
        "Multiple failed authentication attempts detected",
        "Suspicious SQL query pattern identified",
        "Port scanning activity detected from external IP",
        "Anomalous bandwidth usage spike detected",
        "Potential data exfiltration attempt blocked",
        "Cross-site scripting payload detected in request",
        "DNS tunneling activity flagged by ML model",
        "Brute force attack detected on SSH service",
        "DDoS attack pattern identified on web server",
    ]

    for i in range(50):
        ep = random.choice(endpoints)
        ep_apps = [a for a in all_apps if a.endpoint_id == ep.id]
        severity = random.choices(severities, weights=severity_weights, k=1)[0]
        alert = Alert(
            id=str(uuid.uuid4()),
            severity=severity,
            category=random.choice(categories),
            attack_type=random.choice(attack_types) if random.random() > 0.3 else None,
            message=random.choice(alert_messages),
            confidence=round(random.uniform(0.5, 0.99), 3),
            app_id=random.choice(ep_apps).id if ep_apps and random.random() > 0.3 else None,
            endpoint_id=ep.id,
            timestamp=now - timedelta(
                hours=random.randint(0, 168),
                minutes=random.randint(0, 59),
            ),
        )
        db.add(alert)

    # --- Network Usage (100 entries) ---
    for i in range(100):
        ep = random.choice(endpoints)
        usage = NetworkUsage(
            id=str(uuid.uuid4()),
            endpoint_id=ep.id,
            bytes_in=random.randint(10000, 50000000),
            bytes_out=random.randint(5000, 25000000),
            packets=random.randint(100, 50000),
            avg_packet_size=round(random.uniform(64.0, 1500.0), 2),
            timestamp=now - timedelta(
                hours=random.randint(0, 72),
                minutes=random.randint(0, 59),
            ),
        )
        db.add(usage)

    # --- ML Predictions (30 entries) ---
    ml_attack_types = [
        "DDoS", "SQL Injection", "XSS", "Port Scan", "Brute Force",
        "Man-in-the-Middle", "DNS Tunneling", "Data Exfiltration", "Malware C2",
    ]
    ml_actions = ["allow", "block", "monitor"]
    ml_app_names = ["nginx", "postgres", "redis-server", "node", "python3"]

    for i in range(30):
        anomaly_score = round(random.uniform(0.0, 1.0), 4)
        is_anomaly = anomaly_score > 0.6
        prediction = MLPrediction(
            id=str(uuid.uuid4()),
            anomaly_score=anomaly_score,
            attack_type=random.choice(ml_attack_types) if is_anomaly else None,
            confidence=round(random.uniform(0.6, 0.99), 3) if is_anomaly else round(random.uniform(0.85, 0.99), 3),
            action="block" if anomaly_score > 0.8 else ("monitor" if is_anomaly else "allow"),
            app_name=random.choice(ml_app_names),
            src_ip=f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            dst_ip=f"10.0.{random.randint(1, 5)}.{random.randint(1, 254)}",
            context_json={
                "protocol": random.choice(["TCP", "UDP", "HTTP", "HTTPS", "DNS"]),
                "port": random.choice([22, 80, 443, 3306, 5432, 6379, 8080]),
                "session_duration": random.randint(1, 3600),
                "payload_size": random.randint(64, 65535),
            },
            timestamp=now - timedelta(
                hours=random.randint(0, 48),
                minutes=random.randint(0, 59),
            ),
        )
        db.add(prediction)

    db.commit()
    print("Database seeded successfully with sample data.")
