from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Detection(BaseModel):
    frame_id: int
    class_name: str
    class_id: int
    bbox_x1: float
    bbox_y1: float
    bbox_x2: float
    bbox_y2: float
    confidence: float

class GeoDetection(BaseModel):
    track_id: int
    class_name: str
    latitude: float
    longitude: float
    speed_mps: float
    heading_deg: float
    confidence: float
    timestamp: datetime
