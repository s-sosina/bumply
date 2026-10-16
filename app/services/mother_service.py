from datetime import timedelta

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import MotherORM
from app.models.domain import MotherCreate, MotherResponse
from app.services.exceptions import MotherNotFoundError

CACHE_KEY = "mother:{mother_id}"
CACHE_TTL_SECONDS = 60 * 5  # 5 minutes

# Computed on every read from lmp_date + today, so they must never be cached.
_COMPUTED_FIELDS = {"gestational_weeks", "trimester"}


def _key(mother_id: str) -> str:
    return CACHE_KEY.format(mother_id=mother_id)


async def _invalidate(redis: Redis, mother_id: str) -> None:
    try:
        await redis.delete(_key(mother_id))
    except RedisError:
        # Cache is a supporting layer: a Redis outage must not fail a successful write.
        pass


async def _get_active(db: AsyncSession, mother_id: str) -> MotherORM | None:
    result = await db.execute(
        select(MotherORM).where(MotherORM.id == mother_id, MotherORM.is_deleted.is_(False))
    )
    return result.scalar_one_or_none()


async def ensure_mother_exists(db: AsyncSession, mother_id: str) -> None:
    """Explicit pre-check, so a missing mother is a clean 404 and not a failed INSERT."""
    result = await db.execute(
        select(MotherORM.id).where(MotherORM.id == mother_id, MotherORM.is_deleted.is_(False))
    )
    if result.scalar_one_or_none() is None:
        raise MotherNotFoundError(mother_id)


async def create_mother(db: AsyncSession, data: MotherCreate) -> MotherResponse:
    due_date = data.due_date or data.lmp_date + timedelta(days=280)
    mother = MotherORM(
        full_name=data.full_name,
        age=data.age,
        lmp_date=data.lmp_date,
        due_date=due_date,
        high_risk=data.high_risk,
        preferred_language=data.preferred_language,
        phone_number=data.phone_number,
    )
    db.add(mother)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("A mother with this phone number may already exist.") from exc
    await db.refresh(mother)
    return MotherResponse.model_validate(mother)


async def get_mother(db: AsyncSession, redis: Redis, mother_id: str) -> MotherResponse | None:
    # 1. Try the cache. A Redis failure just means a cache miss.
    try:
        cached = await redis.get(_key(mother_id))
    except RedisError:
        cached = None
    if cached is not None:
        # Only raw stored fields are cached; gestational_weeks/trimester are recomputed here.
        return MotherResponse.model_validate_json(cached)

    # 2. Miss: Postgres is the source of truth.
    mother = await _get_active(db, mother_id)
    if mother is None:
        return None
    response = MotherResponse.model_validate(mother)

    # 3. Populate the cache with raw fields only.
    try:
        await redis.set(
            _key(mother_id),
            response.model_dump_json(exclude=_COMPUTED_FIELDS),
            ex=CACHE_TTL_SECONDS,
        )
    except RedisError:
        pass
    return response


async def update_mother(
    db: AsyncSession, redis: Redis, mother_id: str, data: MotherCreate
) -> MotherResponse | None:
    """Full replacement (PUT semantics): every field in MotherCreate is overwritten."""
    mother = await _get_active(db, mother_id)
    if mother is None:
        return None

    mother.full_name = data.full_name
    mother.age = data.age
    mother.lmp_date = data.lmp_date
    mother.due_date = data.due_date or data.lmp_date + timedelta(days=280)
    mother.high_risk = data.high_risk
    mother.preferred_language = data.preferred_language
    mother.phone_number = data.phone_number
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise ValueError("A mother with this phone number may already exist.") from exc
    await db.refresh(mother)

    await _invalidate(redis, mother_id)  # only after a successful commit
    return MotherResponse.model_validate(mother)


async def soft_delete_mother(db: AsyncSession, redis: Redis, mother_id: str) -> bool:
    """Medical records are never hard-deleted: flag them and hide from active queries."""
    mother = await _get_active(db, mother_id)
    if mother is None:
        return False
    mother.is_deleted = True
    await db.commit()
    await _invalidate(redis, mother_id)
    return True
