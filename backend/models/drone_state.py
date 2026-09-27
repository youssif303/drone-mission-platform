from pydantic import BaseModel
from datetime import datetime

class DroneState(BaseModel):
    latitude: float
    longitude: float
    altitude_m: float
    heading_deg: float
    speed_mps: float
    battery_percent: float
    gps_fix: bool
    gimbal_pitch_deg: float
    timestamp: datetime
