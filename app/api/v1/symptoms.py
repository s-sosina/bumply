from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.domain import SymptomEntry, SymptomResponse
from app.services.exceptions import MotherNotFoundError
from app.services.symptom_service import create_symptom

router = APIRouter()


@router.post("/symptoms", response_model=SymptomResponse, status_code=status.HTTP_201_CREATED)
async def create_symptom_endpoint(data: SymptomEntry, db: AsyncSession = Depends(get_db)):
    try:
        return await create_symptom(db, data)
    except MotherNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
