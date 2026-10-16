from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.domain import KickCount, KickCountResponse
from app.services.exceptions import MotherNotFoundError
from app.services.kick_service import create_kick_count

router = APIRouter()


@router.post("/kicks", response_model=KickCountResponse, status_code=status.HTTP_201_CREATED)
async def create_kick_endpoint(data: KickCount, db: AsyncSession = Depends(get_db)):
    try:
        return await create_kick_count(db, data)
    except MotherNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
