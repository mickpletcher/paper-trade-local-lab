from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine

from tradeforge.config import get_settings
from tradeforge.database.models import Base
from tradeforge.database.session import get_engine


def init_db(engine: Engine | None = None) -> None:
    settings = get_settings()
    if engine is None and settings.database_path is not None:
        Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine or get_engine())
