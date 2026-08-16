from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from time import monotonic
from typing import Any
from urllib.request import HTTPRedirectHandler, Request, build_opener

from sqlalchemy import Engine

from tradeforge.automation.locking import MaintenanceLock
from tradeforge.automation.notifications import send_escalations
from tradeforge.config import Settings, get_settings, validate_outbound_https_url
from tradeforge.database.migrations import init_db
from tradeforge.database.session import get_engine, session_scope
from tradeforge.market_data.importer import import_ohlcv_csv
from tradeforge.market_data.live import (
    QuoteProvider,
    get_default_refresh_symbols,
    get_quote_provider,
    refresh_live_quotes,
)


class MaintenanceError(RuntimeError):
    def __init__(self, message: str, report_path: Path | None = None):
        super().__init__(message)
        self.report_path = report_path


class _RejectWebhookRedirects(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        raise RuntimeError("Failure webhook redirects are not allowed.")


def run_maintenance(
    settings: Settings | None = None,
    quote_provider: QuoteProvider | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    current_settings = settings or get_settings()
    started_at = _ensure_utc(now or datetime.now(UTC))
    report: dict[str, object] = {
        "status": "running",
        "started_at": _format_timestamp(started_at),
        "imports": [],
        "quotes": {"requested": [], "refreshed_count": 0},
        "backup_path": None,
        "database": {},
        "restore_drill": {},
    }
    report_path: Path | None = None

    engine: Engine | None = None
    try:
        with MaintenanceLock(
            current_settings.maintenance_lock_path,
            current_settings.maintenance_lock_stale_seconds,
        ) as maintenance_lock:
            report["maintenance_lock_wait_ms"] = maintenance_lock.wait_ms
            engine = get_engine(current_settings.database_url, current_settings.sqlite_busy_timeout_ms)
            if current_settings.database_path is not None:
                current_settings.database_path.parent.mkdir(parents=True, exist_ok=True)
            init_db(engine)
            imports, import_failures = _import_pending_files(current_settings, engine, started_at)
            report["imports"] = imports
            if import_failures:
                raise ValueError(f"{len(import_failures)} import file(s) were quarantined.")
            report["quotes"] = _refresh_open_position_quotes(current_settings, quote_provider, engine)
            report["database"] = inspect_sqlite_health(engine)
            backup_path = backup_sqlite_database(
                current_settings.database_path,
                current_settings.backup_dir,
                current_settings.backup_retention_count,
                started_at,
            )
            report["backup_path"] = str(backup_path)
            report["restore_drill"] = restore_backup_drill(backup_path)
            report["status"] = "success"
            report["completed_at"] = _format_timestamp(datetime.now(UTC))
            report_path = _write_report(
                current_settings.automation_report_dir,
                report,
                started_at,
                current_settings.automation_report_retention_count,
            )
            report["report_path"] = str(report_path)
            return report
    except Exception as exc:
        report["status"] = "failed"
        report["completed_at"] = _format_timestamp(datetime.now(UTC))
        report["error"] = f"{type(exc).__name__}: {exc}"
        if current_settings.failure_webhook_url:
            try:
                _send_failure_notification(current_settings.failure_webhook_url, report)
                report["notification"] = "sent"
            except Exception as notification_exc:
                report["notification"] = f"failed: {type(notification_exc).__name__}: {notification_exc}"
        try:
            report["escalations"] = send_escalations(current_settings, report)
        except Exception as escalation_exc:
            report["escalations"] = f"failed: {type(escalation_exc).__name__}: {escalation_exc}"
        try:
            report_path = _write_report(
                current_settings.automation_report_dir,
                report,
                started_at,
                current_settings.automation_report_retention_count,
            )
        except Exception:
            report_path = None
        raise MaintenanceError(str(exc), report_path) from exc
    finally:
        if engine is not None:
            engine.dispose()


def backup_sqlite_database(
    database_path: Path | None,
    backup_dir: Path,
    retention_count: int,
    now: datetime | None = None,
) -> Path:
    if database_path is None:
        raise ValueError("Automated backup currently supports SQLite databases only.")
    source = database_path.resolve()
    if not source.is_file():
        raise FileNotFoundError(f"SQLite database not found: {source}")

    backup_root = backup_dir.resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = _ensure_utc(now or datetime.now(UTC)).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_root / f"tradeforge-{timestamp}.db"
    temporary = destination.with_suffix(".tmp")

    try:
        with (
            closing(sqlite3.connect(source)) as source_connection,
            closing(sqlite3.connect(temporary)) as backup_connection,
        ):
            source_connection.backup(backup_connection)
        with closing(sqlite3.connect(temporary)) as verification_connection:
            integrity = verification_connection.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            raise RuntimeError("SQLite backup integrity verification failed.")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)

    backups = sorted(backup_root.glob("tradeforge-*.db"), key=lambda path: path.name, reverse=True)
    for expired in backups[retention_count:]:
        expired.unlink()
    return destination


def restore_backup_drill(backup_path: Path) -> dict[str, object]:
    started = monotonic()
    with (
        closing(sqlite3.connect(backup_path)) as backup_connection,
        closing(sqlite3.connect(":memory:")) as restored_connection,
    ):
        backup_connection.backup(restored_connection)
        integrity = restored_connection.execute("PRAGMA integrity_check").fetchone()
        table_count = restored_connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        ).fetchone()
    if integrity is None or integrity[0] != "ok":
        raise RuntimeError("SQLite restore drill integrity verification failed.")
    if table_count is None or int(table_count[0]) == 0:
        raise RuntimeError("SQLite restore drill found no application tables.")
    return {
        "status": "verified",
        "recovery_time_ms": int((monotonic() - started) * 1_000),
        "table_count": int(table_count[0]),
    }


def inspect_sqlite_health(engine: Engine) -> dict[str, object]:
    if engine.dialect.name != "sqlite":
        return {"backend": engine.dialect.name}
    connection_started = monotonic()
    with engine.connect() as connection:
        first_connection_ms = round((monotonic() - connection_started) * 1_000, 3)
        journal_mode = connection.exec_driver_sql("PRAGMA journal_mode").scalar_one()
        busy_timeout_ms = connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one()
        connection.commit()
        lock_probe_started = monotonic()
        connection.exec_driver_sql("BEGIN IMMEDIATE")
        connection.exec_driver_sql("ROLLBACK")
        lock_wait_ms = round((monotonic() - lock_probe_started) * 1_000, 3)
        checkpoint = connection.exec_driver_sql("PRAGMA wal_checkpoint(PASSIVE)").one()
    return {
        "backend": "sqlite",
        "first_connection_ms": first_connection_ms,
        "journal_mode": journal_mode,
        "busy_timeout_ms": busy_timeout_ms,
        "lock_wait_ms": lock_wait_ms,
        "wal_checkpoint": {
            "busy": checkpoint[0],
            "log_frames": checkpoint[1],
            "checkpointed_frames": checkpoint[2],
        },
    }


def _import_pending_files(
    settings: Settings,
    engine: Engine,
    started_at: datetime,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    settings.import_dir.mkdir(parents=True, exist_ok=True)
    settings.processed_import_dir.mkdir(parents=True, exist_ok=True)
    settings.quarantine_import_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    failures: list[dict[str, object]] = []
    for csv_path in sorted(settings.import_dir.glob("*.csv"), key=lambda path: path.name.lower()):
        ticker = csv_path.stem.strip().upper()
        try:
            if not ticker:
                raise ValueError(f"Cannot derive a ticker from import filename: {csv_path.name}")
            with session_scope(engine=engine) as session:
                rows = import_ohlcv_csv(session, ticker, csv_path)
        except Exception as exc:
            quarantined = _archive_import(csv_path, settings.quarantine_import_dir, started_at)
            failure: dict[str, object] = {
                "file": csv_path.name,
                "symbol": ticker,
                "status": "quarantined",
                "quarantine_path": str(quarantined),
                "error": f"{type(exc).__name__}: {exc}",
            }
            _atomic_write(quarantined.with_suffix(quarantined.suffix + ".error.json"), json.dumps(failure, indent=2))
            results.append(failure)
            failures.append(failure)
            continue
        archived = _archive_import(csv_path, settings.processed_import_dir, started_at)
        results.append(
            {
                "file": csv_path.name,
                "symbol": ticker,
                "status": "imported",
                "rows_upserted": rows,
                "archive_path": str(archived),
                "sha256": sha256(archived.read_bytes()).hexdigest(),
            }
        )
    return results, failures


def acknowledge_quarantined_import(settings: Settings, filename: str, retry: bool) -> Path:
    if Path(filename).name != filename:
        raise ValueError("Import filename must not contain a directory path.")
    source = (settings.quarantine_import_dir / filename).resolve()
    if source.parent != settings.quarantine_import_dir.resolve() or not source.is_file():
        raise FileNotFoundError(f"Quarantined import not found: {filename}")
    error_path = source.with_suffix(source.suffix + ".error.json")
    destination_root = settings.import_dir if retry else settings.processed_import_dir / "acknowledged"
    destination_root.mkdir(parents=True, exist_ok=True)
    destination_name = _original_import_filename(error_path, source.name) if retry else source.name
    destination = destination_root / destination_name
    if destination.exists():
        raise FileExistsError(f"Import destination already exists: {destination}")
    os.replace(source, destination)
    error_path.unlink(missing_ok=True)
    return destination


def _original_import_filename(error_path: Path, fallback: str) -> str:
    if not error_path.is_file():
        return fallback
    try:
        original = json.loads(error_path.read_text(encoding="utf-8")).get("file")
    except (json.JSONDecodeError, OSError, AttributeError):
        return fallback
    if not isinstance(original, str) or Path(original).name != original or not original.lower().endswith(".csv"):
        return fallback
    return original


def _archive_import(source: Path, destination_root: Path, started_at: datetime) -> Path:
    timestamp = _ensure_utc(started_at).strftime("%Y%m%dT%H%M%S%fZ")
    destination = destination_root.resolve() / f"{timestamp}-{source.name}"
    if destination.exists():
        raise FileExistsError(f"Import archive already exists: {destination}")
    os.replace(source, destination)
    return destination


def _refresh_open_position_quotes(
    settings: Settings,
    quote_provider: QuoteProvider | None,
    engine: Engine,
) -> dict[str, object]:
    with session_scope(engine=engine) as session:
        symbols = get_default_refresh_symbols(session)
        if not symbols:
            return {"requested": [], "refreshed_count": 0}
        provider = quote_provider or get_quote_provider(settings)
        refreshed = refresh_live_quotes(session, symbols, provider)
    return {"requested": symbols, "refreshed_count": len(refreshed)}


def _write_report(report_dir: Path, report: dict[str, object], started_at: datetime, retention_count: int) -> Path:
    report_root = report_dir.resolve()
    report_root.mkdir(parents=True, exist_ok=True)
    timestamp = started_at.strftime("%Y%m%dT%H%M%S%fZ")
    report_path = report_root / f"maintenance-{timestamp}.json"
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    _atomic_write(report_path, serialized)
    _atomic_write(report_root / "latest.json", serialized)
    reports = sorted(report_root.glob("maintenance-*.json"), key=lambda path: path.name, reverse=True)
    retention_errors: list[dict[str, str]] = []
    for expired in reports[retention_count:]:
        try:
            expired.unlink()
        except OSError as exc:
            retention_errors.append({"path": str(expired), "error": f"{type(exc).__name__}: {exc}"})
    if retention_errors:
        report["retention_errors"] = retention_errors
        serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
        _atomic_write(report_path, serialized)
        _atomic_write(report_root / "latest.json", serialized)
    return report_path


def build_local_health(settings: Settings | None = None) -> dict[str, object]:
    current_settings = settings or get_settings()
    database_path = current_settings.database_path
    database: dict[str, object] = {"configured": current_settings.database_url, "exists": False}
    if database_path is not None and database_path.is_file():
        with closing(sqlite3.connect(database_path)) as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()
            journal_mode = connection.execute("PRAGMA journal_mode").fetchone()
        database.update(
            {
                "exists": True,
                "integrity": integrity[0] if integrity else "unknown",
                "journal_mode": journal_mode[0] if journal_mode else "unknown",
            }
        )
    latest_path = current_settings.automation_report_dir / "latest.json"
    try:
        latest_report = json.loads(latest_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        latest_report = None
    backups = sorted(current_settings.backup_dir.glob("tradeforge-*.db"), reverse=True)
    health = {
        "status": "healthy"
        if database.get("integrity") == "ok"
        and isinstance(latest_report, dict)
        and latest_report.get("status") == "success"
        else "attention_required",
        "database": database,
        "latest_maintenance": latest_report,
        "backup_count": len(backups),
        "newest_backup": str(backups[0]) if backups else None,
        "pending_imports": len(list(current_settings.import_dir.glob("*.csv"))),
        "quarantined_imports": len(list(current_settings.quarantine_import_dir.glob("*.csv"))),
        "maintenance_locked": current_settings.maintenance_lock_path.exists(),
    }
    return health


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _send_failure_notification(webhook_url: str, report: dict[str, object]) -> None:
    validated_url = validate_outbound_https_url(webhook_url, "TRADEFORGE_FAILURE_WEBHOOK_URL")
    notification = {
        "event": "tradeforge_maintenance_failed",
        "status": report.get("status"),
        "started_at": report.get("started_at"),
        "completed_at": report.get("completed_at"),
    }
    payload = json.dumps(notification).encode("utf-8")
    request = Request(validated_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with build_opener(_RejectWebhookRedirects()).open(request, timeout=10) as response:
        if response.status >= 400:
            raise RuntimeError(f"Failure webhook returned HTTP {response.status}.")


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _format_timestamp(value: datetime) -> str:
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")
