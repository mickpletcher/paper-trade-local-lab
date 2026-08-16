from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from typing import Any

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from tradeforge.config import get_settings


def get_engine(database_url: str | None = None, sqlite_busy_timeout_ms: int | None = None) -> Engine:
    settings = get_settings()
    url = database_url or settings.database_url
    parsed_url = make_url(url)
    is_sqlite = parsed_url.get_backend_name() == "sqlite"
    sqlite_is_memory = is_sqlite and parsed_url.database in {None, "", ":memory:"}
    connect_args: dict[str, object] = {}
    if is_sqlite:
        busy_timeout_ms = settings.sqlite_busy_timeout_ms if sqlite_busy_timeout_ms is None else sqlite_busy_timeout_ms
        if not 0 <= busy_timeout_ms <= 60_000:
            raise ValueError("SQLite busy timeout must be between 0 and 60000 milliseconds.")
        connect_args = {"check_same_thread": False, "timeout": busy_timeout_ms / 1_000}
    engine_options: dict[str, object] = {}
    if sqlite_is_memory:
        engine_options["poolclass"] = StaticPool
    elif is_sqlite:
        engine_options["poolclass"] = NullPool
    engine = create_engine(url, connect_args=connect_args, future=True, **engine_options)
    if is_sqlite:
        if not sqlite_is_memory:

            @event.listens_for(engine, "first_connect")
            def enable_sqlite_wal(dbapi_connection: Any, connection_record: Any) -> None:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.close()

        @event.listens_for(engine, "connect")
        def configure_sqlite_connection(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute(f"PRAGMA busy_timeout={busy_timeout_ms}")
            cursor.close()

    return engine


@lru_cache(maxsize=1)
def get_application_engine() -> Engine:
    return get_engine()


@lru_cache(maxsize=1)
def get_application_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_application_engine(), expire_on_commit=False, future=True)


def dispose_application_engine() -> None:
    get_application_session_factory.cache_clear()
    if get_application_engine.cache_info().currsize:
        get_application_engine().dispose()
    get_application_engine.cache_clear()


def get_session(database_url: str | None = None, *, engine: Engine | None = None) -> Session:
    return sessionmaker(bind=_resolve_engine(database_url, engine), expire_on_commit=False, future=True)()


@contextmanager
def session_scope(database_url: str | None = None, *, engine: Engine | None = None) -> Iterator[Session]:
    owns_engine = engine is None
    session_engine = _resolve_engine(database_url, engine)
    session = sessionmaker(bind=session_engine, expire_on_commit=False, future=True)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        if owns_engine:
            session_engine.dispose()


@contextmanager
def application_session_scope() -> Iterator[Session]:
    session = get_application_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _resolve_engine(database_url: str | None, engine: Engine | None) -> Engine:
    if database_url is not None and engine is not None:
        raise ValueError("Provide either database_url or engine, not both.")
    return engine or get_engine(database_url)
