# Bumply: Nigeria-first pregnancy companion (backend)

Rebuilt state: end of Phase 2, Sprint 3. Sprint 4 (Authentication & RBAC) has not been started.

## Setup on a fresh machine (Git Bash on Windows)

1. Install PostgreSQL locally, and Redis (WSL/Ubuntu is fine). Make sure both are running.
2. Create the database role and database (psql as a superuser):
   ```sql
   CREATE ROLE bumply_user LOGIN PASSWORD 'choose_a_password';
   CREATE DATABASE bumply OWNER bumply_user;
   ```
3. Create and activate a virtual environment (the folder is `venv`, not `.venv`):
   ```bash
   python -m venv venv
   source venv/Scripts/activate
   pip install -r requirements.txt
   ```
4. Configure environment: `cp .env.example .env`, then put your real password in `DATABASE_URL`.
5. Create the tables: `alembic upgrade head`
6. Run the tests: `pytest -v`
7. Run the API: `uvicorn app.main:app --reload`, then open http://127.0.0.1:8000/docs

## Layout

| Path | Purpose |
|---|---|
| `app/api/v1/` | HTTP routes only (versioned under `/v1`) |
| `app/services/` | Business logic and DB/cache access; routes stay thin |
| `app/models/domain.py` | Pydantic models: what the API accepts and returns |
| `app/db/models.py` | SQLAlchemy models: how data is stored in Postgres |
| `app/core/` | Settings, Redis client, security (empty: Sprint 4) |
| `app/agents/` | Reserved for the Phase 6 agent layer |
| `alembic/` | Database migrations |
| `tests/` | Mirrors `app/` |

## Design rules worth remembering

- Allowed-value CHECK constraints are generated from the domain Enums/Literal, so Python and Postgres share one definition.
- `gestational_weeks` and `trimester` are computed from `lmp_date`; they are never stored and never cached.
- Postgres is the source of truth. Redis is a cache: if it is down, requests still work.
- A write that references a missing mother returns 404; 409 is reserved for real conflicts (e.g. duplicate phone).
