import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from backend.config import settings
from backend.database.db import init_db, AsyncSessionLocal
from backend.models.mission import MissionDB, WaypointDB, MissionStatus
from backend.models.track import TrackDB
from backend.models.alert import AlertDB, AlertRuleDB
from backend.api.routes import missions, tracks, alerts, reports, health
from backend.api.websocket import video_feed, detections, drone_telemetry, alerts

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST Routes
app.include_router(missions.router, prefix="/api")
app.include_router(tracks.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(health.router, prefix="/api")

# WebSockets
app.include_router(video_feed.router)
app.include_router(detections.router)
app.include_router(drone_telemetry.router)
app.include_router(alerts.router)

@app.on_event("startup")
async def on_startup():
    await init_db()
    
    # Auto-seed default active mission if empty
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(MissionDB))
        if not result.scalars().first():
            mission = MissionDB(
                name="Alpha Recon Patrol",
                description="Autonomous area perimeter surveillance",
                status=MissionStatus.active
            )
            session.add(mission)
            await session.commit()
            await session.refresh(mission)

            wps = [
                WaypointDB(mission_id=mission.id, sequence_order=1, latitude=48.1340, longitude=11.5800, altitude=50.0, reached=True),
                WaypointDB(mission_id=mission.id, sequence_order=2, latitude=48.1345, longitude=11.5815, altitude=50.0, reached=True),
                WaypointDB(mission_id=mission.id, sequence_order=3, latitude=48.1355, longitude=11.5825, altitude=50.0, reached=False),
                WaypointDB(mission_id=mission.id, sequence_order=4, latitude=48.1360, longitude=11.5830, altitude=50.0, reached=False),
            ]
            session.add_all(wps)
            
            # Sample tracked objects
            t1 = TrackDB(track_id=1, class_name="car", last_lat=48.1348, last_lon=11.5815, last_speed_mps=9.7, last_heading_deg=85.0, total_detections=42, status="confirmed")
            t2 = TrackDB(track_id=2, class_name="person", last_lat=48.1355, last_lon=11.5825, last_speed_mps=1.2, last_heading_deg=12.0, total_detections=18, status="confirmed")
            t3 = TrackDB(track_id=3, class_name="truck", last_lat=48.1360, last_lon=11.5830, last_speed_mps=7.9, last_heading_deg=180.0, total_detections=29, status="confirmed")
            session.add_all([t1, t2, t3])

            await session.commit()

@app.get("/")
async def root():
    return {"app": settings.APP_NAME, "docs": "/docs"}
