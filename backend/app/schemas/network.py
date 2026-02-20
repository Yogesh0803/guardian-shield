from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class NetworkUsageResponse(BaseModel):
    id: str
    endpoint_id: str
    bytes_in: int
    bytes_out: int
    packets: int
    avg_packet_size: Optional[float] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ConnectionInfo(BaseModel):
    src_ip: str
    dst_ip: str
    protocol: str
    port: int
    bytes_transferred: int
    status: str
    timestamp: datetime
