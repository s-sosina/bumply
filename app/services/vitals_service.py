from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import VitalsReadingORM
from app.models.domain import VitalsReading
from app.services.mother_service import ensure_mother_exists


async def create_vitals(db: AsyncSession, data: VitalsReading) -> VitalsReadingORM:
    await ensure_mother_exists(db, data.mother_id)
    reading = VitalsReadingORM(**data.model_dump())
    db.add(reading)
    try:
        await db.commit()
    except IntegrityError:
        # Backstop only: Pydantic already rejects out-of-range / mis-ordered values.
        await db.rollback()
        raise
    await db.refresh(reading)
    return reading
