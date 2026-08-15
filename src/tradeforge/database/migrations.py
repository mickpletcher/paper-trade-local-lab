from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import Engine, inspect

from tradeforge.config import get_settings
from tradeforge.database.session import get_engine

ALEMBIC_ROOT = Path(__file__).resolve().parents[1] / "alembic"


def init_db(engine: Engine | None = None) -> None:
    target_engine = engine or get_engine()
    if target_engine.url.get_backend_name() == "sqlite" and target_engine.url.database not in {None, "", ":memory:"}:
        Path(target_engine.url.database).parent.mkdir(parents=True, exist_ok=True)
    config = _build_alembic_config(target_engine.url.render_as_string(hide_password=False))
    with target_engine.begin() as connection:
        _bootstrap_legacy_revision(connection, config)
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def get_current_version(engine: Engine | None = None) -> str | None:
    target_engine = engine or get_engine()
    with target_engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def get_head_version(database_url: str | None = None) -> str:
    config = _build_alembic_config(database_url or get_settings().database_url)
    script = ScriptDirectory.from_config(config)
    return script.get_current_head()


def create_revision(message: str, autogenerate: bool = True, database_url: str | None = None) -> str | None:
    config = _build_alembic_config(database_url or get_settings().database_url)
    script = command.revision(config, message=message, autogenerate=autogenerate)
    return None if script is None else script.path


def _build_alembic_config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(ALEMBIC_ROOT))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _bootstrap_legacy_revision(connection, config: Config) -> None:
    tables = set(inspect(connection).get_table_names())
    if "symbols" not in tables:
        return
    current_revision = MigrationContext.configure(connection).get_current_revision()
    if current_revision is not None:
        return
    legacy_revision = "002_live_quotes" if "live_quotes" in tables else "001_core_schema"
    config.attributes["connection"] = connection
    command.stamp(config, legacy_revision)
