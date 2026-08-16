# Configuration

Copy `.env.example` to `.env` for local development. The populated `.env` file is ignored by Git and Docker build context rules.

Effective settings are cached for the process lifetime. Restart the CLI or API process after changing environment variables or `.env`.

## Core Settings

* `TRADEFORGE_DATABASE_URL` defaults to `sqlite:///data/tradeforge.db`.
* `TRADEFORGE_SQLITE_BUSY_TIMEOUT_MS` sets the bounded SQLite lock wait from zero through 60000 milliseconds and defaults to 5000.
* `TRADEFORGE_STARTING_CASH` sets the simulated opening balance and must be greater than zero.
* `TRADEFORGE_LOG_LEVEL` controls application log verbosity.
* `TRADEFORGE_LOG_FORMAT` accepts the supported text or JSON logging mode.
* `TRADEFORGE_ENABLE_METRICS` enables the unauthenticated `/metrics` endpoint and defaults to `false`.

## Current Execution Settings

* `TRADEFORGE_STARTING_CASH` must be greater than zero.
* `TRADEFORGE_COMMISSION_MODEL` must be `fixed` or `per_share`.
* `TRADEFORGE_FEE_PER_ORDER` is charged once when a fixed commission order receives its first fill.
* `TRADEFORGE_COMMISSION_PER_SHARE` and `TRADEFORGE_COMMISSION_MINIMUM` are reconciled across all fills for one order.
* `TRADEFORGE_SLIPPAGE_BPS` applies the default adverse fill adjustment.
* `TRADEFORGE_SYMBOL_SLIPPAGE_RULES_JSON` maps uppercase tickers to nonnegative basis point overrides.
* `TRADEFORGE_MAX_BAR_FILL_RATIO` must be between zero and one and limits aggregate fills against each bar.
* `TRADEFORGE_QUANTITY_INCREMENT` defaults to `1` for whole share execution. Set a smaller positive increment only when deliberately testing fractional shares.

Invalid, negative, nonfinite, or unsupported execution settings fail before a backtest starts.

Risk policy uses `TRADEFORGE_RISK_MAX_ORDER_NOTIONAL`, `TRADEFORGE_RISK_MAX_POSITION_QUANTITY`, `TRADEFORGE_RISK_MAX_GROSS_EXPOSURE`, `TRADEFORGE_RISK_MAX_DRAWDOWN_RATIO`, and `TRADEFORGE_RISK_KILL_SWITCH`.

## Live Quote And Automation Settings

* `TRADEFORGE_QUOTE_PROVIDER` currently supports `alpaca`.
* `TRADEFORGE_QUOTE_STALE_AFTER_SECONDS` controls staleness against the provider's market timestamp. Quote output separately reports retrieval age as `fetch_age_seconds`.
* `TRADEFORGE_ALPACA_DATA_URL` must be an HTTPS URL with a hostname and no embedded credentials. Alpaca requests refuse redirects.
* `TRADEFORGE_ALPACA_FEED` selects the Alpaca market-data feed.
* `TRADEFORGE_ALPACA_API_KEY_ID` and `TRADEFORGE_ALPACA_API_SECRET_KEY` hold local provider credentials.

* `TRADEFORGE_QUOTE_RETRY_ATTEMPTS` controls transient provider attempts from 1 through 10.
* `TRADEFORGE_QUOTE_RETRY_BASE_SECONDS` controls exponential backoff from zero through 60 seconds.
* `TRADEFORGE_QUOTE_RETRY_MAX_SECONDS` caps each backoff delay from zero through 300 seconds.
* `TRADEFORGE_QUOTE_RETRY_JITTER_SECONDS` randomizes retry delays.
* `TRADEFORGE_QUOTE_CIRCUIT_FAILURE_THRESHOLD`, `TRADEFORGE_QUOTE_CIRCUIT_RESET_SECONDS`, and `TRADEFORGE_QUOTE_CIRCUIT_STATE_PATH` control persistent outage isolation.
* `TRADEFORGE_DATA_QUALITY_MAX_GAP_DAYS` and `TRADEFORGE_DATA_QUALITY_MAX_RETURN_RATIO` control import findings and rejection.
* `TRADEFORGE_IMPORT_DIR` holds scheduled `<TICKER>.csv` inputs.
* `TRADEFORGE_PROCESSED_IMPORT_DIR` and `TRADEFORGE_QUARANTINE_IMPORT_DIR` separate completed and failed input lifecycles.
* `TRADEFORGE_BACKUP_DIR` holds integrity checked SQLite backups.
* `TRADEFORGE_AUTOMATION_REPORT_DIR` holds timestamped and latest JSON run reports.
* `TRADEFORGE_BACKUP_RETENTION_COUNT` keeps the newest 1 through 365 backups.
* `TRADEFORGE_AUTOMATION_REPORT_RETENTION_COUNT` bounds timestamped maintenance reports.
* `TRADEFORGE_MAINTENANCE_LOCK_PATH` and `TRADEFORGE_MAINTENANCE_LOCK_STALE_SECONDS` control concurrency.
* `TRADEFORGE_FAILURE_WEBHOOK_URL` optionally receives minimal failure status. It must use HTTPS, include a hostname, and contain no embedded credentials.
* `TRADEFORGE_FAILURE_TEAMS_WEBHOOK_URL` and the `TRADEFORGE_SMTP_*` settings enable escalations.
* `TRADEFORGE_NOTIFICATION_RETRY_ATTEMPTS`, `TRADEFORGE_NOTIFICATION_DEDUPE_SECONDS`, and `TRADEFORGE_NOTIFICATION_STATE_PATH` control delivery safety.

Use `.env.example` as the inventory. Never commit `.env` or generated data.

## Secret And Network Boundaries

Do not commit `.env`, place credentials in URLs, or paste secrets into logs and issues. The API and optional metrics endpoint have no authentication, so keep them on loopback or behind an authenticated reverse proxy.

## Cross Links

* [security](../security/README.md)
* [installation](../installation/README.md)
