from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from pydantic import BaseModel, ConfigDict
from backend.database.db import Base

# --- ORM Models ---

class AlertDB(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String)  # zone_intrusion, speed_violation, new_object, loitering, track_lost
    severity = Column(String)    # info, warning, critical
    message = Column(String)
    track_id = Column(Integer, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AlertRuleDB(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String)
    name = Column(String)
    params_json = Column(String) # stores zone polygon or speed threshold as JSON string
    enabled = Column(Boolean, default=True)


# --- Pydantic Schemas ---

class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    message: str
    track_id: Optional[int]
    latitude: Optional[float]
    longitude: Optional[float]
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)

class AlertRuleCreate(BaseModel):
    rule_type: str
    name: str
    params_json: str
    enabled: bool = True

class AlertRuleResponse(AlertRuleCreate):
    id: int
    
    model_config = ConfigDict(from_attributes=True)
