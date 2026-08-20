"""Quick local dev helper: creates all tables directly from the SQLAlchemy
metadata, for running against SQLite without Docker/Postgres/Alembic.

Production deployments should use `alembic upgrade head` against Postgres
instead — this script is a convenience for local/offline development only.

Usage:
    DATABASE_URL=sqlite+aiosqlite:///./dev.db python scripts/create_db.py
"""
import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from app.db.base import Base
from app.models import *  # noqa: F401,F403 — registers all models on Base.metadata


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print(f"Tables created at {url}")


if __name__ == "__main__":
    asyncio.run(main())
