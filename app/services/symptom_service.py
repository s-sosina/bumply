from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SymptomEntryORM
from app.models.domain import SymptomEntry
from app.services.mother_service import ensure_mother_exists


async def create_symptom(db: AsyncSession, data: SymptomEntry) -> SymptomEntryORM:
    await ensure_mother_exists(db, data.mother_id)
    entry = SymptomEntryORM(
        mother_id=data.mother_id,
        symptom_type=data.symptom_type.value,
        description=data.description,
        severity=data.severity.value,
        recorded_at=data.recorded_at,
    )
    db.add(entry)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise
    await db.refresh(entry)
    return entry
