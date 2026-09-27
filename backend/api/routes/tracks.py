from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database.db import get_db
from backend.models.track import TrackDB, TrackResponse, TrackHistoryPoint

router = APIRouter(prefix="/tracks", tags=["Tracks"])

@router.get("", response_model=List[TrackResponse])
async def list_tracks(class_name: Optional[str] = None, status: Optional[str] = None, limit: int = 50, db: AsyncSession = Depends(get_db)):
    query = select(TrackDB)
    if class_name:
        query = query.filter(TrackDB.class_name == class_name)
    if status:
        query = query.filter(TrackDB.status == status)
        
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{track_id}", response_model=TrackResponse)
async def get_track(track_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TrackDB).filter(TrackDB.track_id == track_id))
    track = result.scalar_one_or_none()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return track

@router.get("/{track_id}/history", response_model=List[TrackHistoryPoint])
async def get_track_history(track_id: int, db: AsyncSession = Depends(get_db)):
    # Since TrackHistoryPoint requires trail history that we are not storing 
    # directly in the ORM for this simplified version, let's just return a placeholder 
    # or the last known point. In a real app, there'd be a TrackHistoryDB model.
    result = await db.execute(select(TrackDB).filter(TrackDB.track_id == track_id))
    track = result.scalar_one_or_none()
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
        
    if track.last_lat is not None and track.last_lon is not None:
        return [TrackHistoryPoint(
            latitude=track.last_lat,
            longitude=track.last_lon,
            timestamp=track.last_seen,
            speed_mps=track.last_speed_mps or 0.0,
            heading_deg=track.last_heading_deg or 0.0
        )]
    return []
