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

The API is read only and currently unauthenticated. The CLI default and Compose profile bind it to loopback. Do not expose it to an untrusted network.

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
