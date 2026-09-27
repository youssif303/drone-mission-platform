import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database.db import get_db
from backend.models.mission import MissionDB
from backend.models.track import TrackDB
from backend.models.alert import AlertDB
from backend.services.report_generator import ReportGenerator

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{mission_id}")
@router.get("/mission/{mission_id}")
async def generate_report(mission_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MissionDB).options(selectinload(MissionDB.waypoints)).filter(MissionDB.id == mission_id))
    mission = result.scalar_one_or_none()
    
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    tracks_result = await db.execute(select(TrackDB))
    tracks = tracks_result.scalars().all()
    
    alerts_result = await db.execute(select(AlertDB))
    alerts = alerts_result.scalars().all()
    
    generator = ReportGenerator()
    pdf_bytes = generator.generate_pdf(mission, tracks, alerts)
    
    return StreamingResponse(
        io.BytesIO(pdf_bytes), 
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=mission_report_{mission_id}.pdf"}
    )
