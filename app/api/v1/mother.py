from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis
from app.db.session import get_db
from app.models.domain import MotherCreate, MotherResponse
from app.services.mother_service import (
    create_mother,
    get_mother,
    soft_delete_mother,
    update_mother,
)

router = APIRouter()


@router.post("/mothers", response_model=MotherResponse, status_code=status.HTTP_201_CREATED)
async def create_mother_endpoint(data: MotherCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await create_mother(db, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/mothers/{mother_id}", response_model=MotherResponse)
async def get_mother_by_id(
    mother_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    mother = await get_mother(db, redis, mother_id)
    if mother is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mother not found.")
    return mother


@router.put("/mothers/{mother_id}", response_model=MotherResponse)
async def update_mother_endpoint(
    mother_id: str,
    data: MotherCreate,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    try:
        mother = await update_mother(db, redis, mother_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if mother is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mother not found.")
    return mother


@router.delete("/mothers/{mother_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mother_endpoint(
    mother_id: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    if not await soft_delete_mother(db, redis, mother_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mother not found.")
