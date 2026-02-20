import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.sqlite import JSON

from sqlalchemy.orm import relationship

from app.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    purpose = Column(String(255), nullable=True)
    conditions = Column(JSON, nullable=True)
    endpoint_id = Column(String(36), ForeignKey("endpoints.id"), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    endpoint = relationship("Endpoint", back_populates="policies")
