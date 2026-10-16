"""Pydantic domain models: the validated shapes the API accepts and returns.

The SQLAlchemy tables live in app/db/models.py. These two layers are deliberately
separate: this file describes what Bumply speaks, that file describes how it stores it.
"""

from datetime import date, datetime, timedelta, timezone
from enum import Enum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

# Single source of truth for supported languages (en, Yoruba, Hausa, Igbo, Nigerian Pidgin).
# app/db/models.py derives its CHECK constraint from this, so the two can never drift.
Language = Literal["en", "yo", "ha", "ig", "pcm"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def gestational_weeks_from(lmp_date: date, today: date | None = None) -> int:
    """Current gestational week, computed from the LMP date and clamped to 1-42."""
    today = today or utc_now().date()
    return max(1, min(42, (today - lmp_date).days // 7))


def trimester_from(weeks: int) -> int:
    if weeks <= 13:
        return 1
    if weeks <= 26:
        return 2
    return 3


class SeverityLevel(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class SymptomType(str, Enum):
    HEADACHE = "headache"
    NAUSEA = "nausea"
    VOMITING = "vomiting"
    BLEEDING = "bleeding"
    ABDOMINAL_PAIN = "abdominal_pain"
    DIZZINESS = "dizziness"
    FEELING_HOT = "feeling_hot"
    FEELING_COLD = "feeling_cold"
    FEELING_TIRED = "feeling_tired"
    FEELING_ANXIOUS = "feeling_anxious"
    FEELING_DEPRESSED = "feeling_depressed"


# ---------------------------------------------------------------- mothers


class MotherCreate(BaseModel):
    """Input for registering a mother. gestational_weeks is NOT accepted: it is derived."""

    full_name: str = Field(..., min_length=1, max_length=120)
    age: int = Field(..., ge=13, le=60)
    lmp_date: date
    due_date: date | None = None  # defaults to lmp_date + 280 days in the service
    high_risk: bool = False
    preferred_language: Language = "en"
    phone_number: str | None = Field(None, pattern=r"^\+?[0-9]{7,15}$")

    @model_validator(mode="after")
    def _due_date_not_before_lmp(self) -> Self:
        if self.due_date is not None and self.due_date < self.lmp_date:
            raise ValueError("due_date cannot be earlier than lmp_date")
        return self


class MotherResponse(BaseModel):
    """What the API returns. gestational_weeks/trimester are computed on every read."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str
    age: int
    lmp_date: date
    due_date: date
    high_risk: bool
    preferred_language: Language
    phone_number: str | None = None
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def gestational_weeks(self) -> int:
        return gestational_weeks_from(self.lmp_date)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def trimester(self) -> int:
        return trimester_from(self.gestational_weeks)


# ----------------------------------------------------------------- vitals


class VitalsReading(BaseModel):
    mother_id: str
    systolic_bp: int = Field(..., ge=70, le=250)
    diastolic_bp: int = Field(..., ge=40, le=150)
    heart_rate: int = Field(..., ge=40, le=220)
    recorded_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def _systolic_above_diastolic(self) -> Self:
        # Mirrors the check_bp_order DB constraint, so the client gets a 422, not a 500.
        if self.systolic_bp <= self.diastolic_bp:
            raise ValueError("systolic_bp must be greater than diastolic_bp")
        return self


class VitalsResponse(VitalsReading):
    model_config = ConfigDict(from_attributes=True)

    id: str


# --------------------------------------------------------------- symptoms


class SymptomEntry(BaseModel):
    mother_id: str
    description: str = Field(..., min_length=1, max_length=1000)
    severity: SeverityLevel
    symptom_type: SymptomType
    recorded_at: datetime = Field(default_factory=utc_now)


class SymptomResponse(SymptomEntry):
    model_config = ConfigDict(from_attributes=True)

    id: str


# ------------------------------------------------------------------ kicks


class KickCount(BaseModel):
    mother_id: str
    count: int = Field(..., ge=0, le=50)
    duration_minutes: int = Field(..., ge=1, le=120)
    recorded_at: datetime = Field(default_factory=utc_now)


class KickCountResponse(KickCount):
    model_config = ConfigDict(from_attributes=True)

    id: str
