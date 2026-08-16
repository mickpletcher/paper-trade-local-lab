from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///data/tradeforge.db", alias="TRADEFORGE_DATABASE_URL")
    sqlite_busy_timeout_ms: int = Field(
        default=5_000,
        ge=0,
        le=60_000,
        alias="TRADEFORGE_SQLITE_BUSY_TIMEOUT_MS",
    )
    starting_cash: float = Field(default=100_000.0, gt=0, alias="TRADEFORGE_STARTING_CASH")
    fee_per_order: float = Field(default=1.0, ge=0, alias="TRADEFORGE_FEE_PER_ORDER")
    commission_model: str = Field(default="fixed", alias="TRADEFORGE_COMMISSION_MODEL")
    commission_per_share: float = Field(default=0.0, ge=0, alias="TRADEFORGE_COMMISSION_PER_SHARE")
    commission_minimum: float = Field(default=0.0, ge=0, alias="TRADEFORGE_COMMISSION_MINIMUM")
    slippage_bps: float = Field(default=1.0, ge=0, lt=10_000, alias="TRADEFORGE_SLIPPAGE_BPS")
    symbol_slippage_rules_json: str = Field(default="{}", alias="TRADEFORGE_SYMBOL_SLIPPAGE_RULES_JSON")
    max_bar_fill_ratio: float = Field(default=0.25, ge=0, le=1, alias="TRADEFORGE_MAX_BAR_FILL_RATIO")
    quantity_increment: float = Field(default=1.0, gt=0, alias="TRADEFORGE_QUANTITY_INCREMENT")
    risk_max_order_notional: float = Field(
        default=1_000_000.0,
        gt=0,
        alias="TRADEFORGE_RISK_MAX_ORDER_NOTIONAL",
    )
    risk_max_position_quantity: float = Field(
        default=100_000.0,
        gt=0,
        alias="TRADEFORGE_RISK_MAX_POSITION_QUANTITY",
    )
    risk_max_gross_exposure: float = Field(
        default=1_000_000.0,
        gt=0,
        alias="TRADEFORGE_RISK_MAX_GROSS_EXPOSURE",
    )
    risk_max_drawdown_ratio: float = Field(
        default=0.25,
        gt=0,
        le=1,
        alias="TRADEFORGE_RISK_MAX_DRAWDOWN_RATIO",
    )
    risk_kill_switch: bool = Field(default=False, alias="TRADEFORGE_RISK_KILL_SWITCH")
    data_quality_max_gap_days: int = Field(default=4, ge=1, le=365, alias="TRADEFORGE_DATA_QUALITY_MAX_GAP_DAYS")
    data_quality_max_return_ratio: float = Field(
        default=0.75,
        gt=0,
        alias="TRADEFORGE_DATA_QUALITY_MAX_RETURN_RATIO",
    )
    quote_provider: str = Field(default="alpaca", alias="TRADEFORGE_QUOTE_PROVIDER")
    quote_stale_after_seconds: int = Field(default=30, ge=0, alias="TRADEFORGE_QUOTE_STALE_AFTER_SECONDS")
    quote_retry_attempts: int = Field(default=3, ge=1, le=10, alias="TRADEFORGE_QUOTE_RETRY_ATTEMPTS")
    quote_retry_base_seconds: float = Field(default=1.0, ge=0, le=60, alias="TRADEFORGE_QUOTE_RETRY_BASE_SECONDS")
    quote_retry_max_seconds: float = Field(default=30.0, ge=0, le=300, alias="TRADEFORGE_QUOTE_RETRY_MAX_SECONDS")
    quote_retry_jitter_seconds: float = Field(
        default=0.5,
        ge=0,
        le=60,
        alias="TRADEFORGE_QUOTE_RETRY_JITTER_SECONDS",
    )
    quote_circuit_failure_threshold: int = Field(
        default=5,
        ge=1,
        le=100,
        alias="TRADEFORGE_QUOTE_CIRCUIT_FAILURE_THRESHOLD",
    )
    quote_circuit_reset_seconds: int = Field(
        default=300,
        ge=1,
        le=86_400,
        alias="TRADEFORGE_QUOTE_CIRCUIT_RESET_SECONDS",
    )
    quote_circuit_state_path: Path = Field(
        default=Path("data/automation/quote-circuit.json"),
        alias="TRADEFORGE_QUOTE_CIRCUIT_STATE_PATH",
    )
    alpaca_data_url: str = Field(default="https://data.alpaca.markets", alias="TRADEFORGE_ALPACA_DATA_URL")
    alpaca_feed: str = Field(default="iex", alias="TRADEFORGE_ALPACA_FEED")
    alpaca_api_key_id: str | None = Field(default=None, alias="TRADEFORGE_ALPACA_API_KEY_ID")
    alpaca_api_secret_key: str | None = Field(default=None, alias="TRADEFORGE_ALPACA_API_SECRET_KEY")
    log_level: str = Field(default="INFO", alias="TRADEFORGE_LOG_LEVEL")
    log_format: str = Field(default="json", alias="TRADEFORGE_LOG_FORMAT")
    enable_metrics: bool = Field(default=False, alias="TRADEFORGE_ENABLE_METRICS")
    import_dir: Path = Field(default=Path("data/imports"), alias="TRADEFORGE_IMPORT_DIR")
    processed_import_dir: Path = Field(
        default=Path("data/imports/processed"),
        alias="TRADEFORGE_PROCESSED_IMPORT_DIR",
    )
    quarantine_import_dir: Path = Field(
        default=Path("data/imports/quarantine"),
        alias="TRADEFORGE_QUARANTINE_IMPORT_DIR",
    )
    backup_dir: Path = Field(default=Path("data/backups"), alias="TRADEFORGE_BACKUP_DIR")
    automation_report_dir: Path = Field(default=Path("data/automation"), alias="TRADEFORGE_AUTOMATION_REPORT_DIR")
    backup_retention_count: int = Field(default=7, ge=1, le=365, alias="TRADEFORGE_BACKUP_RETENTION_COUNT")
    automation_report_retention_count: int = Field(
        default=30,
        ge=1,
        le=10_000,
        alias="TRADEFORGE_AUTOMATION_REPORT_RETENTION_COUNT",
    )
    maintenance_lock_path: Path = Field(
        default=Path("data/automation/maintenance.lock"),
        alias="TRADEFORGE_MAINTENANCE_LOCK_PATH",
    )
    maintenance_lock_stale_seconds: int = Field(
        default=7_200,
        ge=60,
        le=604_800,
        alias="TRADEFORGE_MAINTENANCE_LOCK_STALE_SECONDS",
    )
    failure_webhook_url: str | None = Field(default=None, alias="TRADEFORGE_FAILURE_WEBHOOK_URL")
    failure_teams_webhook_url: str | None = Field(default=None, alias="TRADEFORGE_FAILURE_TEAMS_WEBHOOK_URL")
    smtp_host: str | None = Field(default=None, alias="TRADEFORGE_SMTP_HOST")
    smtp_port: int = Field(default=587, ge=1, le=65_535, alias="TRADEFORGE_SMTP_PORT")
    smtp_username: str | None = Field(default=None, alias="TRADEFORGE_SMTP_USERNAME")
    smtp_password: str | None = Field(default=None, alias="TRADEFORGE_SMTP_PASSWORD")
    smtp_from: str | None = Field(default=None, alias="TRADEFORGE_SMTP_FROM")
    smtp_to: str | None = Field(default=None, alias="TRADEFORGE_SMTP_TO")
    notification_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        alias="TRADEFORGE_NOTIFICATION_RETRY_ATTEMPTS",
    )
    notification_dedupe_seconds: int = Field(
        default=3_600,
        ge=0,
        le=604_800,
        alias="TRADEFORGE_NOTIFICATION_DEDUPE_SECONDS",
    )
    notification_state_path: Path = Field(
        default=Path("data/automation/notification-state.json"),
        alias="TRADEFORGE_NOTIFICATION_STATE_PATH",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", allow_inf_nan=False)

    @property
    def database_path(self) -> Path | None:
        if not self.database_url.startswith("sqlite:///"):
            return None
        return Path(self.database_url.removeprefix("sqlite:///"))


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    os.environ.setdefault("PYTHONUTF8", "1")
    return Settings()


def validate_outbound_https_url(value: str, setting_name: str) -> str:
    validation_message = (
        f"{setting_name} must be an HTTPS URL with a hostname, no whitespace, and no embedded credentials."
    )
    if not value or value != value.strip() or any(character.isspace() for character in value):
        raise ValueError(validation_message)
    parsed_url = urlsplit(value)
    if (
        parsed_url.scheme.lower() != "https"
        or not parsed_url.hostname
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise ValueError(validation_message)
    return value
