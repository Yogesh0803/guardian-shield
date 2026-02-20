import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, BigInteger

from sqlalchemy.orm import relationship

from app.database import Base


class NetworkUsage(Base):
    __tablename__ = "network_usages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    endpoint_id = Column(String(36), ForeignKey("endpoints.id"), nullable=False)
    bytes_in = Column(BigInteger, nullable=False, default=0)
    bytes_out = Column(BigInteger, nullable=False, default=0)
    packets = Column(Integer, nullable=False, default=0)
    avg_packet_size = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    endpoint = relationship("Endpoint", back_populates="network_usages")
