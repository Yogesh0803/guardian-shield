from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, SessionLocal, Base
from app.models import (
    User, Endpoint, Application, Policy, Alert, NetworkUsage, MLPrediction,
)
from app.routes.auth import router as auth_router
from app.routes.endpoints import router as endpoints_router
from app.routes.policies import router as policies_router
from app.routes.alerts import router as alerts_router
from app.routes.attacks import router as attacks_router
from app.routes.ml import router as ml_router
from app.websocket.handlers import (
    websocket_network_endpoint,
    websocket_alerts_endpoint,
    websocket_predictions_endpoint,
)
from app.services.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed data
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="Guardian Shield - Context-Aware ML Firewall",
    description="Backend API for Guardian Shield — a context-aware ML firewall with real-time threat detection",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(endpoints_router)
app.include_router(policies_router)
app.include_router(alerts_router)
app.include_router(attacks_router)
app.include_router(ml_router)


# WebSocket endpoints
@app.websocket("/ws/network")
async def ws_network(websocket: WebSocket):
    await websocket_network_endpoint(websocket)


@app.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    await websocket_alerts_endpoint(websocket)


@app.websocket("/ws/predictions")
async def ws_predictions(websocket: WebSocket):
    await websocket_predictions_endpoint(websocket)


@app.get("/")
def root():
    return {
        "name": "Guardian Shield API",
        "version": "1.0.0",
        "status": "operational",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
