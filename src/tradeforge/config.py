from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///data/tradeforge.db", alias="TRADEFORGE_DATABASE_URL")
    starting_cash: float = Field(default=100_000.0, gt=0, alias="TRADEFORGE_STARTING_CASH")
    fee_per_order: float = Field(default=1.0, ge=0, alias="TRADEFORGE_FEE_PER_ORDER")
    commission_model: str = Field(default="fixed", alias="TRADEFORGE_COMMISSION_MODEL")
    commission_per_share: float = Field(default=0.0, ge=0, alias="TRADEFORGE_COMMISSION_PER_SHARE")
    commission_minimum: float = Field(default=0.0, ge=0, alias="TRADEFORGE_COMMISSION_MINIMUM")
    slippage_bps: float = Field(default=1.0, ge=0, lt=10_000, alias="TRADEFORGE_SLIPPAGE_BPS")
    symbol_slippage_rules_json: str = Field(default="{}", alias="TRADEFORGE_SYMBOL_SLIPPAGE_RULES_JSON")
    max_bar_fill_ratio: float = Field(default=0.25, ge=0, le=1, alias="TRADEFORGE_MAX_BAR_FILL_RATIO")
    quote_provider: str = Field(default="alpaca", alias="TRADEFORGE_QUOTE_PROVIDER")
    quote_stale_after_seconds: int = Field(default=30, ge=0, alias="TRADEFORGE_QUOTE_STALE_AFTER_SECONDS")
    quote_retry_attempts: int = Field(default=3, ge=1, le=10, alias="TRADEFORGE_QUOTE_RETRY_ATTEMPTS")
    quote_retry_base_seconds: float = Field(default=1.0, ge=0, le=60, alias="TRADEFORGE_QUOTE_RETRY_BASE_SECONDS")
    quote_retry_max_seconds: float = Field(default=30.0, ge=0, le=300, alias="TRADEFORGE_QUOTE_RETRY_MAX_SECONDS")
    alpaca_data_url: str = Field(default="https://data.alpaca.markets", alias="TRADEFORGE_ALPACA_DATA_URL")
    alpaca_feed: str = Field(default="iex", alias="TRADEFORGE_ALPACA_FEED")
    alpaca_api_key_id: str | None = Field(default=None, alias="TRADEFORGE_ALPACA_API_KEY_ID")
    alpaca_api_secret_key: str | None = Field(default=None, alias="TRADEFORGE_ALPACA_API_SECRET_KEY")
    log_level: str = Field(default="INFO", alias="TRADEFORGE_LOG_LEVEL")
    log_format: str = Field(default="json", alias="TRADEFORGE_LOG_FORMAT")
    enable_metrics: bool = Field(default=False, alias="TRADEFORGE_ENABLE_METRICS")
    import_dir: Path = Field(default=Path("data/imports"), alias="TRADEFORGE_IMPORT_DIR")
    backup_dir: Path = Field(default=Path("data/backups"), alias="TRADEFORGE_BACKUP_DIR")
    automation_report_dir: Path = Field(default=Path("data/automation"), alias="TRADEFORGE_AUTOMATION_REPORT_DIR")
    backup_retention_count: int = Field(default=7, ge=1, le=365, alias="TRADEFORGE_BACKUP_RETENTION_COUNT")
    failure_webhook_url: str | None = Field(default=None, alias="TRADEFORGE_FAILURE_WEBHOOK_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", allow_inf_nan=False)

    @property
    def database_path(self) -> Path | None:
        if not self.database_url.startswith("sqlite:///"):
            return None
        return Path(self.database_url.removeprefix("sqlite:///"))


def get_settings() -> Settings:
    os.environ.setdefault("PYTHONUTF8", "1")
    return Settings()
