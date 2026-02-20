import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class Endpoint(Base):
    __tablename__ = "endpoints"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    ip_address = Column(String(45), unique=True, nullable=False)
    status = Column(String(50), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    applications = relationship("Application", back_populates="endpoint", lazy="selectin")
    policies = relationship("Policy", back_populates="endpoint", lazy="selectin")
    alerts = relationship("Alert", back_populates="endpoint", lazy="selectin")
    network_usages = relationship("NetworkUsage", back_populates="endpoint", lazy="selectin")
