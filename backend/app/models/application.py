import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    process_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="running")
    endpoint_id = Column(String(36), ForeignKey("endpoints.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    endpoint = relationship("Endpoint", back_populates="applications")
