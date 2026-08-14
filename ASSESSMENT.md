# TradeForge Assessment

## Purpose

TradeForge is a local first paper trading and backtesting lab. It imports historical data, refreshes live quotes for valuation, simulates orders, runs strategies, stores results locally, and exposes CLI and read only API views. It does not place live trades.

## Current State

The MVP supports market, limit, stop, and stop limit orders with cancellation, partial fills, aggregate bar volume limits, configurable commission and slippage, cash and position accounting, and lifecycle trade records. The moving average crossover strategy is the only built in strategy. Backtests operate on one symbol per run.

SQLite persistence is versioned through Alembic. Revision `003_execution_realism` is the current head. Reports are Markdown. Live quotes use an Alpaca adapter with an HTTPS-only endpoint boundary and remain separate from historical execution data.

## Build And Dependencies

The application supports Python 3.11 through 3.13 and uses Typer, FastAPI, SQLAlchemy, Alembic, Pydantic Settings, Uvicorn, Prometheus Client, and HTTPX. Development checks use Pytest, Ruff, Build, Pip Audit, and locked Markdownlint tooling. Container packaging uses Docker and publishes to GHCR from GitHub Actions.

## Automation

GitHub Actions runs lint and format checks, tests, package builds, container validation, documentation checks, dependency review, scheduled vulnerability audits, tag-driven releases, and image publishing. A governance workflow runs on pushes, pull requests, manual dispatch, and a weekly schedule. It fails when a change omits any required living document or when their structure drifts. Actions are commit pinned and updated through Dependabot.

The local equivalent is:

```powershell
./scripts/Test-ProjectGovernance.ps1 -CheckWorkingTree
```

## Known Limitations

* Quote refresh and data import still require manual commands.
* No retry queue, failure notification, or automatic provider failover exists.
* Execution uses bar based approximations and does not model intrabar ordering, time in force, shorting, venues, or market impact.
* The API has no authentication, pagination, or versioning.
* Money is stored as floating point values.
* The Docker base image is tag pinned rather than digest pinned and the image does not yet publish an SBOM or provenance attestation.
* GitHub `main` remains unprotected until the owner approves a solo-maintainer ruleset.
* Secret scanning, push protection, Dependabot security updates, default Actions permissions, webhooks, deploy keys, and package visibility require manual verification because the connected GitHub app cannot read those settings.
* Local container validation requires Docker, which was unavailable during this audit.

## Health

Overall health is good for a local research MVP. The audit suite has 46 passing tests with 86 percent coverage. Ruff lint and format, Bandit, Gitleaks history scanning, Python and npm dependency audits, package builds, Markdown checks, and governance validation pass. GitHub CI and CodeQL are green. Container validation remains delegated to GitHub Actions.
