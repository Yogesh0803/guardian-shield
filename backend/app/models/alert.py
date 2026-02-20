import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Float

from sqlalchemy.orm import relationship

from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    severity = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    attack_type = Column(String(100), nullable=True)
    message = Column(String(500), nullable=False)
    confidence = Column(Float, nullable=True)
    app_id = Column(String(36), ForeignKey("applications.id"), nullable=True)
    endpoint_id = Column(String(36), ForeignKey("endpoints.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    endpoint = relationship("Endpoint", back_populates="alerts")
    application = relationship("Application", lazy="selectin")
