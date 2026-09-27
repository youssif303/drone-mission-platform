from enum import Enum
from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict
from backend.database.db import Base


class MissionStatus(str, Enum):
    planned = "planned"
    active = "active"
    paused = "paused"
    completed = "completed"
    aborted = "aborted"


# --- ORM Models ---

class MissionDB(Base):
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(SQLEnum(MissionStatus), default=MissionStatus.planned)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    waypoints = relationship("WaypointDB", back_populates="mission", cascade="all, delete-orphan")


class WaypointDB(Base):
    __tablename__ = "waypoints"

    id = Column(Integer, primary_key=True, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    sequence_order = Column(Integer)
    latitude = Column(Float)
    longitude = Column(Float)
    altitude = Column(Float)
    reached = Column(Boolean, default=False)
    reached_at = Column(DateTime, nullable=True)

    mission = relationship("MissionDB", back_populates="waypoints")


# --- Pydantic Schemas ---

class WaypointCreate(BaseModel):
    sequence_order: int
    latitude: float
    longitude: float
    altitude: float

class WaypointResponse(WaypointCreate):
    id: int
    mission_id: int
    reached: bool
    reached_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)

class MissionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    waypoints: List[WaypointCreate] = []

class MissionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: MissionStatus
    created_at: datetime
    updated_at: datetime
    waypoints: List[WaypointResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
