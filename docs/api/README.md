# API

## Purpose

This section documents HTTP contracts, compatibility boundaries, and future versioning strategy.

## Intended Contents

* endpoint inventory
* payload examples
* versioning approach
* error handling
* metrics and health endpoints

## Current Runtime Contract

Alembic migrations run once during FastAPI startup. `/health` executes a database probe and returns HTTP 503 when storage is unavailable. `/portfolio` accepts `strategy_run_id`; without it, valuation selects the newest run. Unknown run IDs return HTTP 404.

The API is read only. `/dashboard` provides escaped server rendered summaries and `/experiments` provides research provenance. API authentication is disabled by default for loopback use.

Set `TRADEFORGE_API_AUTH_ENABLED=true` to require the configured API key header, which defaults to `X-TradeForge-Key`. `/health`, `/docs`, `/openapi.json`, and `/redoc` stay public. Viewer keys access read only tenant data. Operator and admin keys may also access enabled metrics.

Positions, orders, runs, experiments, dashboard records, and valuation are tenant scoped. Symbols and quotes are shared reference data. The database stores only hashes of opaque API secrets. Create, rotate, inspect, and revoke service identities with the matching CLI commands.

Authentication does not add TLS. The CLI default and Compose profile bind to loopback. Use an HTTPS reverse proxy for any approved network exposure.

## Suggested Future Topics

* endpoint-reference.md
* response-examples.md
* versioning-policy.md
* error-contract.md
* observability-endpoints.md

## Naming Conventions

* contract docs use `contract` or `policy`
* endpoint docs use `reference`
* examples stay close to the owning endpoint family

## File Examples

* `endpoint-reference.md`
* `versioning-policy.md`
* `observability-endpoints.md`

## Cross Links

* [architecture](../architecture/README.md)
* [automation](../automation/README.md)
