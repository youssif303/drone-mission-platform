from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.database.db import get_db
from backend.models.mission import MissionDB, WaypointDB, MissionCreate, MissionResponse, MissionStatus

router = APIRouter(prefix="/missions", tags=["Missions"])

@router.post("", response_model=MissionResponse, status_code=status.HTTP_201_CREATED)
async def create_mission(mission: MissionCreate, db: AsyncSession = Depends(get_db)):
    # Pause any currently active missions so the new mission takes priority
    active_res = await db.execute(select(MissionDB).filter(MissionDB.status == MissionStatus.active))
    for m in active_res.scalars().all():
        m.status = MissionStatus.paused

    db_mission = MissionDB(
        name=mission.name,
        description=mission.description,
        status=MissionStatus.active
    )
    db.add(db_mission)
    await db.commit()
    await db.refresh(db_mission)

    for wp in mission.waypoints:
        db_wp = WaypointDB(
            mission_id=db_mission.id,
            sequence_order=wp.sequence_order,
            latitude=wp.latitude,
            longitude=wp.longitude,
            altitude=wp.altitude
        )
        db.add(db_wp)
    
    await db.commit()
    
    result = await db.execute(select(MissionDB).options(selectinload(MissionDB.waypoints)).filter(MissionDB.id == db_mission.id))
    return result.scalar_one()

@router.get("", response_model=List[MissionResponse])
async def list_missions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MissionDB).options(selectinload(MissionDB.waypoints)).order_by(MissionDB.id.desc()))
    return result.scalars().all()

@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MissionDB).options(selectinload(MissionDB.waypoints)).filter(MissionDB.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission

@router.put("/{mission_id}", response_model=MissionResponse)
async def update_mission(mission_id: int, mission_update: MissionCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MissionDB).options(selectinload(MissionDB.waypoints)).filter(MissionDB.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission.name = mission_update.name
    mission.description = mission_update.description
    
    # Simple replace waypoints
    for wp in mission.waypoints:
        await db.delete(wp)
        
    for wp in mission_update.waypoints:
        db_wp = WaypointDB(
            mission_id=mission.id,
            sequence_order=wp.sequence_order,
            latitude=wp.latitude,
            longitude=wp.longitude,
            altitude=wp.altitude
        )
        db.add(db_wp)
        
    await db.commit()
    
    result = await db.execute(select(MissionDB).options(selectinload(MissionDB.waypoints)).filter(MissionDB.id == mission_id))
    return result.scalar_one()

@router.delete("/{mission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MissionDB).filter(MissionDB.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
        
    await db.delete(mission)
    await db.commit()

async def update_mission_status(mission_id: int, new_status: MissionStatus, db: AsyncSession):
    result = await db.execute(select(MissionDB).options(selectinload(MissionDB.waypoints)).filter(MissionDB.id == mission_id))
    mission = result.scalar_one_or_none()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    mission.status = new_status
    await db.commit()
    await db.refresh(mission)
    return mission

@router.post("/{mission_id}/start", response_model=MissionResponse)
async def start_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    return await update_mission_status(mission_id, MissionStatus.active, db)

@router.post("/{mission_id}/pause", response_model=MissionResponse)
async def pause_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    return await update_mission_status(mission_id, MissionStatus.paused, db)

@router.post("/{mission_id}/abort", response_model=MissionResponse)
async def abort_mission(mission_id: int, db: AsyncSession = Depends(get_db)):
    return await update_mission_status(mission_id, MissionStatus.aborted, db)
