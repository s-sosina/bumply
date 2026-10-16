from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import KickCountORM
from app.models.domain import KickCount
from app.services.mother_service import ensure_mother_exists


async def create_kick_count(db: AsyncSession, data: KickCount) -> KickCountORM:
    await ensure_mother_exists(db, data.mother_id)
    kick = KickCountORM(**data.model_dump())
    db.add(kick)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise
    await db.refresh(kick)
    return kick
