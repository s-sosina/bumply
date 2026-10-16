from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.domain import VitalsReading, VitalsResponse
from app.services.exceptions import MotherNotFoundError
from app.services.vitals_service import create_vitals

router = APIRouter()


@router.post("/vitals", response_model=VitalsResponse, status_code=status.HTTP_201_CREATED)
async def create_vitals_endpoint(data: VitalsReading, db: AsyncSession = Depends(get_db)):
    try:
        return await create_vitals(db, data)
    except MotherNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
