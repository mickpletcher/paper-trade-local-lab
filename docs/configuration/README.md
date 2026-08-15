# Configuration

Copy `.env.example` to `.env` for local development. The populated `.env` file is ignored by Git and Docker build context rules.

## Core Settings

* `TRADEFORGE_DATABASE_URL` defaults to `sqlite:///data/tradeforge.db`.
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

## Live Quote And Automation Settings

* `TRADEFORGE_QUOTE_PROVIDER` currently supports `alpaca`.
* `TRADEFORGE_QUOTE_STALE_AFTER_SECONDS` controls quote staleness reporting.
* `TRADEFORGE_ALPACA_DATA_URL` must be an HTTPS URL with a hostname and no embedded credentials.
* `TRADEFORGE_ALPACA_FEED` selects the Alpaca market-data feed.
* `TRADEFORGE_ALPACA_API_KEY_ID` and `TRADEFORGE_ALPACA_API_SECRET_KEY` hold local provider credentials.

* `TRADEFORGE_QUOTE_RETRY_ATTEMPTS` controls transient provider attempts from 1 through 10.
* `TRADEFORGE_QUOTE_RETRY_BASE_SECONDS` controls exponential backoff from zero through 60 seconds.
* `TRADEFORGE_QUOTE_RETRY_MAX_SECONDS` caps each backoff delay from zero through 300 seconds.
* `TRADEFORGE_IMPORT_DIR` holds scheduled `<TICKER>.csv` inputs.
* `TRADEFORGE_BACKUP_DIR` holds integrity checked SQLite backups.
* `TRADEFORGE_AUTOMATION_REPORT_DIR` holds timestamped and latest JSON run reports.
* `TRADEFORGE_BACKUP_RETENTION_COUNT` keeps the newest 1 through 365 backups.
* `TRADEFORGE_FAILURE_WEBHOOK_URL` optionally receives failed maintenance reports.

Use `.env.example` as the inventory. Never commit `.env` or generated data.

## Secret And Network Boundaries

Do not commit `.env`, place credentials in URLs, or paste secrets into logs and issues. The API and optional metrics endpoint have no authentication, so keep them on loopback or behind an authenticated reverse proxy.

## Cross Links

* [security](../security/README.md)
* [installation](../installation/README.md)
