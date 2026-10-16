"""SQLAlchemy ORM models: how Bumply stores data in PostgreSQL.

Allowed-value CHECK constraints are generated from the domain Enums/Literals, so the
Python layer and the database layer share ONE definition and cannot drift apart.
"""

import uuid
from collections.abc import Iterable
from datetime import date, datetime, timezone
from typing import get_args

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.domain import (
    Language,
    SeverityLevel,
    SymptomType,
    gestational_weeks_from,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid.uuid4())


def _quoted(values: Iterable[str]) -> str:
    return ", ".join(f"'{v}'" for v in values)


def _check_in(column: str, values: Iterable[str]) -> str:
    return f"{column} IN ({_quoted(values)})"


def _check_nullable_in(column: str, values: Iterable[str]) -> str:
    return f"{column} IS NULL OR {column} IN ({_quoted(values)})"


LANGUAGE_VALUES = list(get_args(Language))
SEVERITY_VALUES = [m.value for m in SeverityLevel]
SYMPTOM_TYPE_VALUES = [m.value for m in SymptomType]


class MotherORM(Base):
    __tablename__ = "mothers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    # Dates are the source of truth; gestational_weeks is computed, never stored.
    lmp_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    high_risk: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    preferred_language: Mapped[str] = mapped_column(String(3), nullable=False, default="en")
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True, unique=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    vitals_readings: Mapped[list["VitalsReadingORM"]] = relationship(back_populates="mother")
    symptom_entries: Mapped[list["SymptomEntryORM"]] = relationship(back_populates="mother")
    kick_counts: Mapped[list["KickCountORM"]] = relationship(back_populates="mother")

    __table_args__ = (
        CheckConstraint("age >= 13 AND age <= 60", name="check_mother_age_range"),
        CheckConstraint("due_date >= lmp_date", name="check_due_date_after_lmp"),
        CheckConstraint(_check_in("preferred_language", LANGUAGE_VALUES), name="check_preferred_language"),
    )

    @property
    def gestational_weeks(self) -> int:
        return gestational_weeks_from(self.lmp_date)


class VitalsReadingORM(Base):
    __tablename__ = "vitals_readings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    mother_id: Mapped[str] = mapped_column(
        ForeignKey("mothers.id", ondelete="RESTRICT"), nullable=False
    )
    systolic_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    diastolic_bp: Mapped[int] = mapped_column(Integer, nullable=False)
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    mother: Mapped["MotherORM"] = relationship(back_populates="vitals_readings")

    __table_args__ = (
        CheckConstraint("systolic_bp >= 70 AND systolic_bp <= 250", name="check_systolic_range"),
        CheckConstraint("diastolic_bp >= 40 AND diastolic_bp <= 150", name="check_diastolic_range"),
        CheckConstraint("heart_rate >= 40 AND heart_rate <= 220", name="check_heart_rate_range"),
        CheckConstraint("systolic_bp > diastolic_bp", name="check_bp_order"),
        # The real query pattern: "this mother's readings over time".
        Index("ix_vitals_mother_recorded", "mother_id", "recorded_at"),
    )


class SymptomEntryORM(Base):
    __tablename__ = "symptom_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    mother_id: Mapped[str] = mapped_column(
        ForeignKey("mothers.id", ondelete="RESTRICT"), nullable=False
    )
    symptom_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    mother: Mapped["MotherORM"] = relationship(back_populates="symptom_entries")

    __table_args__ = (
        CheckConstraint(_check_in("symptom_type", SYMPTOM_TYPE_VALUES), name="check_symptom_type"),
        CheckConstraint(_check_nullable_in("severity", SEVERITY_VALUES), name="check_symptom_severity"),
        Index("ix_symptoms_mother_recorded", "mother_id", "recorded_at"),
    )


class KickCountORM(Base):
    __tablename__ = "kick_counts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    mother_id: Mapped[str] = mapped_column(
        ForeignKey("mothers.id", ondelete="RESTRICT"), nullable=False
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    mother: Mapped["MotherORM"] = relationship(back_populates="kick_counts")

    __table_args__ = (
        CheckConstraint("count >= 0 AND count <= 50", name="check_kick_count_range"),
        CheckConstraint("duration_minutes >= 1 AND duration_minutes <= 120", name="check_kick_duration_range"),
        Index("ix_kicks_mother_recorded", "mother_id", "recorded_at"),
    )
