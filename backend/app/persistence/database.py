from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


def data_directory() -> Path:
    override = os.getenv("AUTORDS_DATA_DIR")
    base = Path(override) if override else Path(os.getenv("LOCALAPPDATA", Path.home())) / "AutoRDS"
    for name in ("rulesets", "models", "backups", "logs", "exports"):
        (base / name).mkdir(parents=True, exist_ok=True)
    return base


DATABASE_PATH = data_directory() / "autords.db"
DATABASE_URL = os.getenv("AUTORDS_DATABASE_URL", f"sqlite:///{DATABASE_PATH.as_posix()}")


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, future=True)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def init_database() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(engine)
