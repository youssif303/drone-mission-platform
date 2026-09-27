from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime
from pydantic import BaseModel, ConfigDict
from backend.database.db import Base

# --- ORM Models ---

class TrackDB(Base):
    __tablename__ = "tracks"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, index=True, unique=True)
    class_name = Column(String)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_lat = Column(Float, nullable=True)
    last_lon = Column(Float, nullable=True)
    last_speed_mps = Column(Float, nullable=True)
    last_heading_deg = Column(Float, nullable=True)
    total_detections = Column(Integer, default=1)
    status = Column(String, default="active") # active, lost, deleted


# --- Pydantic Schemas ---

class TrackResponse(BaseModel):
    id: int
    track_id: int
    class_name: str
    first_seen: datetime
    last_seen: datetime
    last_lat: Optional[float]
    last_lon: Optional[float]
    last_speed_mps: Optional[float]
    last_heading_deg: Optional[float]
    total_detections: int
    status: str

    model_config = ConfigDict(from_attributes=True)

class TrackHistoryPoint(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    speed_mps: float
    heading_deg: float
