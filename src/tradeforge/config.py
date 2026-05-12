from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the local TradeForge app."""

    database_url: str = Field(default="sqlite:///data/tradeforge.db", alias="TRADEFORGE_DATABASE_URL")
    starting_cash: float = Field(default=100_000.0, alias="TRADEFORGE_STARTING_CASH")
    fee_per_order: float = Field(default=1.0, alias="TRADEFORGE_FEE_PER_ORDER")
    slippage_bps: float = Field(default=1.0, alias="TRADEFORGE_SLIPPAGE_BPS")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_path(self) -> Path | None:
        if not self.database_url.startswith("sqlite:///"):
            return None
        return Path(self.database_url.removeprefix("sqlite:///"))


def get_settings() -> Settings:
    os.environ.setdefault("PYTHONUTF8", "1")
    return Settings()
