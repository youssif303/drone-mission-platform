from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.models.mission import MissionDB, MissionStatus

class MissionService:
    @staticmethod
    async def get_active_mission(db: AsyncSession) -> MissionDB:
        result = await db.execute(
            select(MissionDB)
            .options(selectinload(MissionDB.waypoints))
            .filter(MissionDB.status == MissionStatus.active)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_mission(mission_id: int, db: AsyncSession) -> MissionDB:
        result = await db.execute(
            select(MissionDB)
            .options(selectinload(MissionDB.waypoints))
            .filter(MissionDB.id == mission_id)
        )
        return result.scalar_one_or_none()
