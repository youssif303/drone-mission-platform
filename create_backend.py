import os

project_root = r"d:\Projects\New folder\recon-eye"

files = {
    "docker-compose.yml": r"""services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app/backend
      - ./perception:/app/perception
      - ./mission_planner:/app/mission_planner
      - ./simulation:/app/simulation
    environment:
      - DEMO_MODE=true
      - DATABASE_URL=sqlite+aiosqlite:///./drone_platform.db

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
""",
    "Dockerfile.backend": r"""FROM python:3.11-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ /app/backend/
COPY perception/ /app/perception/
COPY mission_planner/ /app/mission_planner/
COPY simulation/ /app/simulation/
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    "Dockerfile.frontend": r"""# Stage 1: Build
FROM node:20-slim as build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
""",
    ".gitignore": r"""__pycache__
*.pyc
.env
node_modules
dist
build
*.db
.pytest_cache
venv
.venv
*.onnx
*.pt
""",
    ".env.example": r"""DEMO_MODE=true
DATABASE_URL=sqlite+aiosqlite:///./drone_platform.db
""",
    "LICENSE": r"""MIT License

Copyright (c) 2026 Drone Mission Planning & Perception Platform

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
""",
    ".github/workflows/ci.yml": r"""name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  backend-lint-test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r backend/requirements.txt
    - name: Run pytest
      run: |
        cd backend
        pytest

  frontend-build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Node.js 20
      uses: actions/setup-node@v3
      with:
        node-version: "20"
    - name: Install dependencies and build
      run: |
        cd frontend
        npm ci
        npm run build
""",
    "frontend/nginx.conf": r"""server {
    listen 3000;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
""",
    "backend/requirements.txt": r"""fastapi[standard]>=0.115.0
uvicorn[standard]>=0.30.0
sqlalchemy[asyncio]>=2.0.0
aiosqlite>=0.20.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.9
websockets>=12.0
reportlab>=4.0
aiofiles>=24.0
httpx>=0.27.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
""",
    "backend/config.py": r"""from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = 'Drone Mission Planning & Perception Platform'
    DATABASE_URL: str = 'sqlite+aiosqlite:///./drone_platform.db'
    DEMO_MODE: bool = True
    DEMO_DATA_DIR: str = '../simulation/demo_data'
    CORS_ORIGINS: List[str] = ['http://localhost:5173', 'http://localhost:3000']
    WS_FRAME_RATE: int = 15

    class Config:
        env_file = ".env"

settings = Settings()
""",
    "backend/database/db.py": r"""from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
""",
    "backend/models/mission.py": r"""from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from backend.database.db import Base
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class MissionStatus(enum.Enum):
    planned = "planned"
    active = "active"
    paused = "paused"
    completed = "completed"
    aborted = "aborted"

class MissionDB(Base):
    __tablename__ = "missions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(SQLEnum(MissionStatus), default=MissionStatus.planned)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    waypoints = relationship("WaypointDB", back_populates="mission", cascade="all, delete-orphan", lazy="selectin")

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

# Pydantic Schemas
class WaypointBase(BaseModel):
    sequence_order: int
    latitude: float
    longitude: float
    altitude: float

class WaypointCreate(WaypointBase):
    pass

class WaypointResponse(WaypointBase):
    id: int
    mission_id: int
    reached: bool
    reached_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

class MissionBase(BaseModel):
    name: str
    description: Optional[str] = None

class MissionCreate(MissionBase):
    waypoints: List[WaypointCreate]

class MissionResponse(MissionBase):
    id: int
    status: MissionStatus
    created_at: datetime
    updated_at: datetime
    waypoints: List[WaypointResponse] = []
    model_config = ConfigDict(from_attributes=True)
""",
    "backend/models/track.py": r"""from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from backend.database.db import Base
from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class TrackDB(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, index=True, unique=True)
    class_name = Column(String)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    last_lat = Column(Float)
    last_lon = Column(Float)
    last_speed_mps = Column(Float)
    last_heading_deg = Column(Float)
    total_detections = Column(Integer, default=1)
    status = Column(String, default="active")

class TrackResponse(BaseModel):
    id: int
    track_id: int
    class_name: str
    first_seen: datetime
    last_seen: datetime
    last_lat: float
    last_lon: float
    last_speed_mps: float
    last_heading_deg: float
    total_detections: int
    status: str
    model_config = ConfigDict(from_attributes=True)

class TrackHistoryPoint(BaseModel):
    lat: float
    lon: float
    speed_mps: float
    heading_deg: float
    timestamp: datetime
""",
    "backend/models/detection.py": r"""from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Detection(BaseModel):
    frame_id: int
    class_name: str
    class_id: int
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float

class GeoDetection(BaseModel):
    track_id: int
    class_name: str
    lat: float
    lon: float
    speed_mps: float
    heading_deg: float
    confidence: float
    timestamp: datetime
""",
    "backend/models/alert.py": r"""from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime
from backend.database.db import Base
from pydantic import BaseModel, ConfigDict
from typing import Optional

class AlertDB(Base):
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String)
    severity = Column(String)
    message = Column(String)
    track_id = Column(Integer, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AlertRuleDB(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_type = Column(String)
    name = Column(String)
    params_json = Column(String)
    enabled = Column(Boolean, default=True)

class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    message: str
    track_id: Optional[int]
    lat: Optional[float]
    lon: Optional[float]
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
""",
    "backend/models/drone_state.py": r"""from pydantic import BaseModel
from datetime import datetime

class DroneState(BaseModel):
    lat: float
    lon: float
    altitude_m: float
    heading_deg: float
    speed_mps: float
    battery_percent: float
    gps_fix: int
    gimbal_pitch_deg: float
    timestamp: datetime
""",
    "backend/models/__init__.py": r"""from .mission import MissionDB, WaypointDB, MissionStatus, MissionCreate, MissionResponse, WaypointCreate, WaypointResponse
from .track import TrackDB, TrackResponse, TrackHistoryPoint
from .detection import Detection, GeoDetection
from .alert import AlertDB, AlertRuleDB, AlertResponse, AlertRuleCreate, AlertRuleResponse
from .drone_state import DroneState

__all__ = [
    "MissionDB", "WaypointDB", "MissionStatus", "MissionCreate", "MissionResponse", "WaypointCreate", "WaypointResponse",
    "TrackDB", "TrackResponse", "TrackHistoryPoint",
    "Detection", "GeoDetection",
    "AlertDB", "AlertRuleDB", "AlertResponse", "AlertRuleCreate", "AlertRuleResponse",
    "DroneState"
]
""",
    "backend/api/routes/missions.py": r"""from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from backend.database.db import get_db
from backend.models.mission import MissionDB, WaypointDB, MissionCreate, MissionResponse, MissionStatus
from backend.services.mission_service import MissionService

router = APIRouter(prefix="/api/missions", tags=["missions"])

@router.post("", response_model=MissionResponse)
async def create_mission(mission: MissionCreate, db: AsyncSession = Depends(get_db)):
    return await MissionService.create_mission(db, mission)

@router.get("", response_model=List[MissionResponse])
async def list_missions(db: AsyncSession = Depends(get_db)):
    return await MissionService.list_missions(db)

@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    mission = await MissionService.get_mission(db, mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@router.put("/{mission_id}", response_model=MissionResponse)
async def update_mission(mission_id: int, mission_data: MissionCreate, db: AsyncSession = Depends(get_db)):
    mission = await MissionService.update_mission(db, mission_id, mission_data)
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@router.delete("/{mission_id}")
async def delete_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await MissionService.delete_mission(db, mission_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Mission not found")
    return {"message": "Mission deleted successfully"}

@router.post("/{mission_id}/start")
async def start_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    return await MissionService.update_mission_status(db, mission_id, MissionStatus.active)

@router.post("/{mission_id}/pause")
async def pause_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    return await MissionService.update_mission_status(db, mission_id, MissionStatus.paused)

@router.post("/{mission_id}/abort")
async def abort_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    return await MissionService.update_mission_status(db, mission_id, MissionStatus.aborted)
""",
    "backend/api/routes/tracks.py": r"""from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from backend.database.db import get_db
from backend.models.track import TrackDB, TrackResponse, TrackHistoryPoint

router = APIRouter(prefix="/api/tracks", tags=["tracks"])

@router.get("", response_model=List[TrackResponse])
async def list_tracks(
    status: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    query = select(TrackDB)
    if status:
        query = query.filter(TrackDB.status == status)
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(track_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrackDB).filter(TrackDB.track_id == track_id))
    track = result.scalars().first()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

@router.get("/{track_id}/history", response_model=List[TrackHistoryPoint])
async def get_track_history(track_id: int, db: AsyncSession = Depends(get_db)):
    # Demo endpoint, returning an empty list for history since history model isn't requested in models
    return []
""",
    "backend/api/routes/alerts.py": r"""from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from backend.database.db import get_db
from backend.models.alert import AlertDB, AlertRuleDB, AlertResponse, AlertRuleCreate, AlertRuleResponse

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
rules_router = APIRouter(prefix="/api/alert-rules", tags=["alert-rules"])

@router.get("", response_model=List[AlertResponse])
async def list_alerts(limit: int = 100, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertDB).order_by(AlertDB.timestamp.desc()).limit(limit))
    return result.scalars().all()

@rules_router.post("", response_model=AlertRuleResponse)
async def create_alert_rule(rule: AlertRuleCreate, db: AsyncSession = Depends(get_db)):
    db_rule = AlertRuleDB(**rule.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule

@rules_router.get("", response_model=List[AlertRuleResponse])
async def list_alert_rules(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRuleDB))
    return result.scalars().all()

@rules_router.put("/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: int, rule: AlertRuleCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRuleDB).filter(AlertRuleDB.id == rule_id))
    db_rule = result.scalars().first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    for key, value in rule.model_dump().items():
        setattr(db_rule, key, value)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule

@rules_router.delete("/{rule_id}")
async def delete_alert_rule(rule_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AlertRuleDB).filter(AlertRuleDB.id == rule_id))
    db_rule = result.scalars().first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    await db.delete(db_rule)
    await db.commit()
    return {"message": "Deleted successfully"}
""",
    "backend/api/routes/reports.py": r"""from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.db import get_db
from backend.services.report_generator import ReportGenerator
import io

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/{mission_id}")
async def generate_mission_report(mission_id: int, db: AsyncSession = Depends(get_db)):
    pdf_buffer = await ReportGenerator.generate_report(db, mission_id)
    if not pdf_buffer:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=mission_{mission_id}_report.pdf"}
    )
""",
    "backend/api/routes/health.py": r"""from fastapi import APIRouter
from backend.config import settings

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "demo_mode": settings.DEMO_MODE,
        "uptime": "OK" # Can be implemented more specifically later
    }
""",
    "backend/api/websocket/video_feed.py": r"""from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from backend.config import settings
import base64
import os

router = APIRouter()

@router.websocket("/ws/video-feed")
async def websocket_video_feed(websocket: WebSocket):
    await websocket.accept()
    try:
        # Dummy implementation for demo mode
        while True:
            await asyncio.sleep(1.0 / settings.WS_FRAME_RATE)
            if settings.DEMO_MODE:
                # In real scenario, read from demo_data or real stream
                await websocket.send_text("base64_jpeg_data")
    except WebSocketDisconnect:
        pass
""",
    "backend/api/websocket/detections.py": r"""from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from backend.config import settings
import json
from datetime import datetime

router = APIRouter()

@router.websocket("/ws/detections")
async def websocket_detections(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(1.0)
            if settings.DEMO_MODE:
                # Dummy demo detection
                det = {
                    "track_id": 1,
                    "class_name": "person",
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "speed_mps": 1.2,
                    "heading_deg": 90,
                    "confidence": 0.95,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_json(det)
    except WebSocketDisconnect:
        pass
""",
    "backend/api/websocket/drone_telemetry.py": r"""from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from backend.config import settings
from datetime import datetime

router = APIRouter()

@router.websocket("/ws/drone-telemetry")
async def websocket_drone_telemetry(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await asyncio.sleep(1.0)
            if settings.DEMO_MODE:
                telemetry = {
                    "lat": 37.7749,
                    "lon": -122.4194,
                    "altitude_m": 100.0,
                    "heading_deg": 45.0,
                    "speed_mps": 15.0,
                    "battery_percent": 85.5,
                    "gps_fix": 3,
                    "gimbal_pitch_deg": -45.0,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await websocket.send_json(telemetry)
    except WebSocketDisconnect:
        pass
""",
    "backend/services/alert_engine.py": r"""class AlertEngine:
    @staticmethod
    def check_zone_intrusion(lat: float, lon: float, polygon: list):
        # Point-in-polygon algorithm implementation (simplified)
        return False
        
    @staticmethod
    def check_speed_violation(speed_mps: float, max_speed: float):
        return speed_mps > max_speed
        
    @staticmethod
    def check_new_object(track_id: int):
        # Check if object track_id is new
        return True
        
    @staticmethod
    def process_detection(detection):
        # Process detection and generate alerts based on rules
        pass
""",
    "backend/services/mission_service.py": r"""from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from backend.models.mission import MissionDB, WaypointDB, MissionCreate, MissionStatus

class MissionService:
    @staticmethod
    async def create_mission(db: AsyncSession, mission_data: MissionCreate):
        mission = MissionDB(name=mission_data.name, description=mission_data.description)
        for wp in mission_data.waypoints:
            mission.waypoints.append(WaypointDB(**wp.model_dump()))
        db.add(mission)
        await db.commit()
        await db.refresh(mission)
        return mission

    @staticmethod
    async def list_missions(db: AsyncSession):
        result = await db.execute(select(MissionDB).options(selectinload(MissionDB.waypoints)))
        return result.scalars().all()

    @staticmethod
    async def get_mission(db: AsyncSession, mission_id: int):
        result = await db.execute(
            select(MissionDB).options(selectinload(MissionDB.waypoints)).filter(MissionDB.id == mission_id)
        )
        return result.scalars().first()

    @staticmethod
    async def update_mission(db: AsyncSession, mission_id: int, mission_data: MissionCreate):
        mission = await MissionService.get_mission(db, mission_id)
        if not mission:
            return None
        mission.name = mission_data.name
        mission.description = mission_data.description
        
        # Simple replace waypoints for update
        for wp in mission.waypoints:
            await db.delete(wp)
        mission.waypoints = []
        for wp in mission_data.waypoints:
            mission.waypoints.append(WaypointDB(**wp.model_dump()))
            
        await db.commit()
        await db.refresh(mission)
        return mission

    @staticmethod
    async def delete_mission(db: AsyncSession, mission_id: int):
        mission = await MissionService.get_mission(db, mission_id)
        if not mission:
            return False
        await db.delete(mission)
        await db.commit()
        return True

    @staticmethod
    async def update_mission_status(db: AsyncSession, mission_id: int, status: MissionStatus):
        mission = await MissionService.get_mission(db, mission_id)
        if mission:
            mission.status = status
            await db.commit()
            await db.refresh(mission)
        return mission
""",
    "backend/services/report_generator.py": r"""from sqlalchemy.ext.asyncio import AsyncSession
from reportlab.pdfgen import canvas
import io
from backend.services.mission_service import MissionService

class ReportGenerator:
    @staticmethod
    async def generate_report(db: AsyncSession, mission_id: int):
        mission = await MissionService.get_mission(db, mission_id)
        if not mission:
            return None
            
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer)
        p.drawString(100, 800, f"Mission Report: {mission.name}")
        p.drawString(100, 780, f"Status: {mission.status.value}")
        p.drawString(100, 760, f"Description: {mission.description}")
        p.drawString(100, 740, "Summary Table, Detection Breakdown, Alert List placeholder...")
        
        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer
""",
    "backend/main.py": r"""from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database.db import init_db
from backend.api.routes import missions, tracks, alerts, reports, health
from backend.api.websocket import video_feed, detections, drone_telemetry

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

app.include_router(missions.router)
app.include_router(tracks.router)
app.include_router(alerts.router)
app.include_router(alerts.rules_router)
app.include_router(reports.router)
app.include_router(health.router)
app.include_router(video_feed.router)
app.include_router(detections.router)
app.include_router(drone_telemetry.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Drone Mission Planning & Perception Platform API"}
""",
    "backend/tests/test_missions_api.py": r"""import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app

@pytest.mark.asyncio
async def test_create_mission():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/missions", json={
            "name": "Test Mission",
            "description": "Test Description",
            "waypoints": [
                {"sequence_order": 1, "latitude": 10.0, "longitude": 20.0, "altitude": 100.0}
            ]
        })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Mission"
    assert len(data["waypoints"]) == 1

@pytest.mark.asyncio
async def test_list_missions():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/missions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
""",
    "backend/api/__init__.py": "",
    "backend/api/routes/__init__.py": "",
    "backend/api/websocket/__init__.py": "",
    "backend/services/__init__.py": "",
    "backend/database/__init__.py": "",
    "backend/models/__init__.py": "",
    "backend/tests/__init__.py": ""
}

for rel_path, content in files.items():
    full_path = os.path.join(project_root, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Files generated successfully.")
