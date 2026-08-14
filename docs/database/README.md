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

TradeForge enables SQLite foreign key enforcement on every application engine connection.

Schema changes must use the packaged Alembic revisions. Revision `003_execution_realism` adds stop state, partial fill state, and cumulative commission state to orders.

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
