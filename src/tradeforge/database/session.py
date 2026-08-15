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


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or get_settings().database_url
    parsed_url = make_url(url)
    is_sqlite = parsed_url.get_backend_name() == "sqlite"
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    engine_options: dict[str, object] = {}
    if is_sqlite and parsed_url.database in {None, "", ":memory:"}:
        engine_options["poolclass"] = StaticPool
    elif is_sqlite:
        engine_options["poolclass"] = NullPool
    engine = create_engine(url, connect_args=connect_args, future=True, **engine_options)
    if is_sqlite:

        @event.listens_for(engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection: Any, connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
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


def get_session(database_url: str | None = None) -> Session:
    return sessionmaker(bind=get_engine(database_url), expire_on_commit=False, future=True)()


@contextmanager
def session_scope(database_url: str | None = None) -> Iterator[Session]:
    session = get_session(database_url)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


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
