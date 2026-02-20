# Guardian Shield: Context-Aware ML Firewall

A full-stack, context-aware ML firewall powered by machine learning. Captures live network traffic, analyzes it in real-time using an ensemble of ML models, makes intelligent blocking decisions based on application context, and displays everything through a modern React dashboard.

## Architecture

```
                        React Frontend (TypeScript)
               Dashboard | Endpoints | Policies | Alerts | ML Status
                              |
                     REST API + WebSocket
                              |
                    FastAPI Backend (Python)
              Auth | CRUD | WebSocket Broadcast | Seed Data
                              |
                   ________________________
                  |                        |
              SQLite DB              ML Engine
                              |
            ___________________________________
           |          |           |             |
      Scapy       Context     ML Models     Policy
     Capture      Engine      Ensemble      Engine
                     |           |             |
               App Identity   Isolation    User Rules
               Time/Geo       Forest +     + ML-based
               Behavior       Autoencoder    Decisions
               Baseline       LSTM+CNN         |
                              XGBoost      Firewall
                                          Enforcement
                                        (netsh/iptables)
```

## What It Does

1. **Captures live network traffic** using Scapy - groups packets into flows
2. **Builds context** for every flow:
   - Which app made the request (psutil PID mapping)
   - Time of day, business hours, day of week
   - Behavioral baseline deviations (is this request rate normal?)
   - Geographic destination (GeoIP lookup)
3. **Analyzes with 4 ML models** (ensemble):
   - **Isolation Forest** - fast anomaly scoring
   - **Autoencoder** (PyTorch) - reconstruction-based anomaly detection
   - **LSTM+CNN hybrid** - deep learning on packet features
   - **XGBoost** - attack type classification (DoS, DDoS, PortScan, BruteForce, WebAttack, Botnet, Infiltration)
4. **Makes smart decisions** combining user policies + ML predictions
5. **Enforces firewall rules** - actually blocks malicious IPs (netsh on Windows, iptables on Linux)
6. **Displays everything** on a real-time dashboard with WebSocket streaming

## Project Structure

```
/
├── frontend/                # React + TypeScript
│   ├── src/
│   │   ├── pages/           # Dashboard, Endpoints, Policies, Alerts, Network, MLEngine
│   │   ├── components/      # Reusable UI (Card, Badge, Button, Modal, etc.)
│   │   ├── services/        # API service layer (axios + JWT)
│   │   ├── hooks/           # useWebSocket, useAuth
│   │   ├── context/         # AuthContext
│   │   └── types/           # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
│
├── backend/                 # Python FastAPI
│   ├── app/
│   │   ├── routes/          # auth, endpoints, policies, alerts, attacks, ml
│   │   ├── models/          # SQLAlchemy models (User, Endpoint, Policy, Alert, etc.)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── middleware/      # JWT auth, role-based access
│   │   ├── websocket/       # ConnectionManager + real-time handlers
│   │   ├── services/        # Database seeding
│   │   └── main.py          # FastAPI app entry
│   ├── Dockerfile
│   └── requirements.txt
│
├── ml/                      # ML Engine
│   ├── capture/             # Scapy packet capture + feature extraction
│   ├── context/             # App identifier, time, behavior, geo lookup
│   ├── models/              # Anomaly detector, attack classifier, LSTM+CNN
│   ├── pipeline/            # Inference pipeline + training scripts
│   ├── enforcer/            # Policy engine, firewall rules, NLP parser
│   ├── main.py              # ML engine entry point
│   └── requirements.txt
│
├── docker-compose.yml
├── .github/workflows/ci.yml
└── README.md
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, Chart.js, Framer Motion, Lucide Icons |
| **Backend** | Python, FastAPI, SQLAlchemy, Alembic, JWT (python-jose), Pydantic |
| **ML** | Scapy, scikit-learn, XGBoost, PyTorch, psutil, geoip2 |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **DevOps** | Docker, Docker Compose, GitHub Actions CI |

## Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/atulkp018/GuardianShield.git
cd GuardianShield
docker-compose up --build
```
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env
npm start
```

**ML Engine** (requires admin/root for packet capture):
```bash
cd ml
pip install -r requirements.txt
# Windows: Run as Administrator
# Linux: sudo python -m ml.main
python -m ml.main --interface eth0
```

### Default Login
- Email: `admin@guardian.com`
- Password: `password123`

## ML Model Training

To train models on the CICIDS2017 dataset:

```bash
# Download CICIDS2017 dataset into ml/data/cicids2017/
# Then run:
python -m ml.pipeline.training --model all --data ml/data/cicids2017/
```

This trains:
- **Isolation Forest** on normal traffic patterns
- **Autoencoder** (PyTorch) for reconstruction-based anomaly detection
- **LSTM+CNN** hybrid model for deep packet analysis
- **XGBoost** classifier for attack type identification

## Natural Language Policies

Users can describe policies in plain English:

> "Block Chrome from accessing Russian IPs after 10PM"

The NLP parser extracts:
- **Action**: block
- **App**: chrome
- **Country**: RU
- **Time**: after 22:00

Supported conditions: apps, IPs, domains, ports, protocols, time ranges, days of week, geolocation, anomaly thresholds, attack types, rate limits.

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| POST | `/api/auth/register` | Register user |
| POST | `/api/auth/login` | Login (returns JWT) |
| GET | `/api/auth/me` | Current user |
| GET | `/api/endpoints` | List endpoints |
| GET | `/api/endpoints/:id` | Endpoint details |
| POST | `/api/endpoints/:id/apps` | Add app to endpoint |
| GET/POST/DELETE | `/api/policies/*` | Policy CRUD |
| POST | `/api/policies/parse` | NLP policy parsing |
| GET | `/api/alerts` | Alerts (filterable) |
| GET | `/api/attacks/endpoint/:id` | Attack statistics |
| GET | `/api/ml/status` | ML engine status |
| POST | `/api/ml/retrain` | Trigger retraining |
| WS | `/ws/network` | Real-time network data |
| WS | `/ws/alerts` | Real-time alert stream |
| WS | `/ws/predictions` | Real-time ML predictions |

## Key Features

- **Real JWT Authentication** with access/refresh tokens and role-based access
- **Live Network Traffic Charts** updating in real-time via WebSocket
- **ML Prediction Feed** showing every allow/block/alert decision with confidence
- **Context Viewer** - click any alert to see full context (app, time, behavior, geo)
- **Attack Distribution Charts** from real ML classification
- **Natural Language Policy Creation** - describe rules in plain English
- **Cross-platform Enforcement** - blocks traffic on Windows (netsh) and Linux (iptables)
- **Automated Seed Data** - backend auto-populates with realistic sample data

## License

MIT License - see [LICENSE](LICENSE) for details.
