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

Schema changes must use the packaged Alembic revisions. Revision `004_trade_fee_basis` stores entry and exit fees separately from gross trade prices and migrates existing fee inclusive entry prices.

The API creates one application engine at startup, reuses one session factory for requests, and disposes the engine at shutdown. One maintenance engine is reused for the complete migration, import, and quote sequence and is disposed after success or failure. Explicit engines remain uncached for migrations, CLI work, and isolated tests.

`tradeforge run-maintenance` uses SQLite's online backup API, verifies `PRAGMA integrity_check`, atomically promotes the backup, and retains the configured newest copies. Backups and maintenance reports are local ignored data. Automated restore drills remain future work.

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
