from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from app.models import (
    KickCount,
    MotherCreate,
    MotherResponse,
    SeverityLevel,
    SymptomEntry,
    SymptomType,
    VitalsReading,
)


def _today():
    return datetime.now(timezone.utc).date()


# ---------------------------------------------------------------- MotherCreate


def test_mother_create_valid():
    mother = MotherCreate(full_name="Ada Okoro", age=28, lmp_date=_today() - timedelta(weeks=20))
    assert mother.preferred_language == "en"
    assert mother.due_date is None  # defaulted later, in the service


@pytest.mark.parametrize("age", [12, 61])
def test_mother_create_rejects_age_out_of_range(age):
    with pytest.raises(ValidationError):
        MotherCreate(full_name="Test", age=age, lmp_date=_today())


def test_mother_create_rejects_due_date_before_lmp():
    with pytest.raises(ValidationError):
        MotherCreate(
            full_name="Test",
            age=25,
            lmp_date=_today(),
            due_date=_today() - timedelta(days=1),
        )


@pytest.mark.parametrize("language", ["en", "yo", "ha", "ig", "pcm"])
def test_mother_create_accepts_all_five_languages(language):
    mother = MotherCreate(full_name="Test", age=25, lmp_date=_today(), preferred_language=language)
    assert mother.preferred_language == language


def test_mother_create_rejects_unsupported_language():
    with pytest.raises(ValidationError):
        MotherCreate(full_name="Test", age=25, lmp_date=_today(), preferred_language="fr")


# -------------------------------------------------------------- MotherResponse


def _response(weeks: int) -> MotherResponse:
    lmp = _today() - timedelta(weeks=weeks)
    now = datetime.now(timezone.utc)
    return MotherResponse(
        id="m1",
        full_name="Test",
        age=25,
        lmp_date=lmp,
        due_date=lmp + timedelta(days=280),
        high_risk=False,
        preferred_language="en",
        is_deleted=False,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.parametrize(
    "weeks, expected_trimester",
    [(1, 1), (13, 1), (14, 2), (26, 2), (27, 3), (42, 3)],
)
def test_trimester_boundaries(weeks, expected_trimester):
    # lmp_date is derived from "today", so this test never goes stale as the calendar moves.
    response = _response(weeks)
    assert response.gestational_weeks == weeks
    assert response.trimester == expected_trimester


def test_computed_fields_appear_in_serialized_output():
    payload = _response(20).model_dump()
    assert payload["gestational_weeks"] == 20
    assert payload["trimester"] == 2


# --------------------------------------------------------------- VitalsReading


def test_vitals_valid():
    reading = VitalsReading(mother_id="m1", systolic_bp=120, diastolic_bp=80, heart_rate=75)
    assert reading.systolic_bp == 120


@pytest.mark.parametrize(
    "systolic, diastolic, heart_rate",
    [(300, 80, 75), (60, 40, 75), (120, 160, 75), (120, 80, 300)],
)
def test_vitals_rejects_out_of_range_values(systolic, diastolic, heart_rate):
    with pytest.raises(ValidationError):
        VitalsReading(mother_id="m1", systolic_bp=systolic, diastolic_bp=diastolic, heart_rate=heart_rate)


def test_vitals_rejects_systolic_not_above_diastolic():
    with pytest.raises(ValidationError):
        VitalsReading(mother_id="m1", systolic_bp=90, diastolic_bp=90, heart_rate=75)


# --------------------------------------------------------------- SymptomEntry


def test_symptom_valid():
    entry = SymptomEntry(
        mother_id="m1",
        description="Mild headache since morning",
        severity=SeverityLevel.MILD,
        symptom_type=SymptomType.HEADACHE,
    )
    assert entry.symptom_type is SymptomType.HEADACHE


def test_symptom_rejects_unknown_symptom_type():
    with pytest.raises(ValidationError):
        SymptomEntry(mother_id="m1", description="x", severity="mild", symptom_type="blurred_vision")


def test_symptom_rejects_unknown_severity():
    with pytest.raises(ValidationError):
        SymptomEntry(mother_id="m1", description="x", severity="critical", symptom_type="headache")


# ------------------------------------------------------------------ KickCount


def test_kick_count_valid():
    kick = KickCount(mother_id="m1", count=10, duration_minutes=30)
    assert kick.count == 10


@pytest.mark.parametrize("count, duration", [(-1, 30), (51, 30), (10, 0), (10, 121)])
def test_kick_count_rejects_out_of_range(count, duration):
    with pytest.raises(ValidationError):
        KickCount(mother_id="m1", count=count, duration_minutes=duration)
