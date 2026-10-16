import os

# Settings requires DATABASE_URL. Unit tests never open a connection (engines connect lazily),
# so a placeholder keeps the suite runnable on a machine with no .env or database.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@127.0.0.1:5432/test")
