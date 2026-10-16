from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.kick import router as kicks_router
from app.api.v1.mother import router as mothers_router
from app.api.v1.symptoms import router as symptoms_router
from app.api.v1.vitals import router as vitals_router

app = FastAPI(title="Bumply")

app.include_router(health_router, prefix="/v1", tags=["health"])
app.include_router(mothers_router, prefix="/v1", tags=["mothers"])
app.include_router(vitals_router, prefix="/v1", tags=["vitals"])
app.include_router(symptoms_router, prefix="/v1", tags=["symptoms"])
app.include_router(kicks_router, prefix="/v1", tags=["kicks"])
