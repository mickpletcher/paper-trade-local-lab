# Database

## Purpose

This section documents schema ownership, migrations, storage behavior, and retention strategy.

## Intended Contents

* schema map
* Alembic workflow
* SQLite behavior
* backup and restore
* future storage direction

## Current SQLite Rules

TradeForge enables foreign key enforcement and a bounded busy timeout on every SQLite connection. File backed databases use WAL so readers can continue while another connection writes. `TRADEFORGE_SQLITE_BUSY_TIMEOUT_MS` defaults to 5000 and accepts zero through 60000 milliseconds.

Schema changes must use the packaged Alembic revisions. Revision `006_tier_three_platform` seeds the default tenant, adds hashed API service identities, assigns strategy runs to tenants, and stores experiment and artifact provenance. Revision `005_tier_one_controls` owns corporate action, data quality, execution audit, and active symbol state.

The API creates one application engine at startup, reuses one session factory for requests, and disposes the engine at shutdown. One maintenance engine is reused for the complete migration, import, and quote sequence and is disposed after success or failure. Explicit engines remain uncached for migrations, CLI work, and isolated tests.

`tradeforge run-maintenance` uses SQLite's online backup API, verifies `PRAGMA integrity_check`, atomically promotes the backup, restores the newest copy into memory, verifies application tables, measures RPO and RTO, and retains configured backup and report counts. `tradeforge run-dr-drill` repeats the measured restore on demand and writes `dr-latest.json`. Health records include connection time, lock probe time, busy timeout, journal mode, and WAL checkpoint state. Backups and reports remain local ignored data.

## Suggested Future Topics

* schema-overview.md
* alembic-workflow.md
* sqlite-operations.md
* backup-restore.md
* storage-roadmap.md

## Naming Conventions

* schema docs use `schema`
* migration docs use `migration` or `alembic`
* operational docs use `operations` or `playbook`

## File Examples

* `schema-overview.md`
* `alembic-workflow.md`
* `backup-restore.md`

## Cross Links

* [configuration](../configuration/README.md)
* [automation](../automation/README.md)
