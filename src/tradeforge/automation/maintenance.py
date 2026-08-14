from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from urllib.request import Request, urlopen

from tradeforge.config import Settings, get_settings
from tradeforge.database.migrations import init_db
from tradeforge.database.session import get_engine, session_scope
from tradeforge.market_data.importer import import_ohlcv_csv
from tradeforge.market_data.live import QuoteProvider, get_default_refresh_symbols, get_quote_provider, refresh_live_quotes


class MaintenanceError(RuntimeError):
    def __init__(self, message: str, report_path: Path | None = None):
        super().__init__(message)
        self.report_path = report_path


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
    }
    report_path: Path | None = None

    try:
        if current_settings.database_path is not None:
            current_settings.database_path.parent.mkdir(parents=True, exist_ok=True)
        init_db(get_engine(current_settings.database_url))
        report["imports"] = _import_pending_files(current_settings)
        report["quotes"] = _refresh_open_position_quotes(current_settings, quote_provider)
        backup_path = backup_sqlite_database(
            current_settings.database_path,
            current_settings.backup_dir,
            current_settings.backup_retention_count,
            started_at,
        )
        report["backup_path"] = str(backup_path)
        report["status"] = "success"
        report["completed_at"] = _format_timestamp(datetime.now(UTC))
        report_path = _write_report(current_settings.automation_report_dir, report, started_at)
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
            report_path = _write_report(current_settings.automation_report_dir, report, started_at)
        except Exception:
            report_path = None
        raise MaintenanceError(str(exc), report_path) from exc


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
        with closing(sqlite3.connect(source)) as source_connection, closing(
            sqlite3.connect(temporary)
        ) as backup_connection:
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


def _import_pending_files(settings: Settings) -> list[dict[str, object]]:
    settings.import_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, object]] = []
    for csv_path in sorted(settings.import_dir.glob("*.csv"), key=lambda path: path.name.lower()):
        ticker = csv_path.stem.strip().upper()
        if not ticker:
            raise ValueError(f"Cannot derive a ticker from import filename: {csv_path.name}")
        with session_scope(settings.database_url) as session:
            rows = import_ohlcv_csv(session, ticker, csv_path)
        results.append({"file": csv_path.name, "symbol": ticker, "rows_upserted": rows})
    return results


def _refresh_open_position_quotes(
    settings: Settings,
    quote_provider: QuoteProvider | None,
) -> dict[str, object]:
    with session_scope(settings.database_url) as session:
        symbols = get_default_refresh_symbols(session)
        if not symbols:
            return {"requested": [], "refreshed_count": 0}
        provider = quote_provider or get_quote_provider(settings)
        refreshed = refresh_live_quotes(session, symbols, provider)
    return {"requested": symbols, "refreshed_count": len(refreshed)}


def _write_report(report_dir: Path, report: dict[str, object], started_at: datetime) -> Path:
    report_root = report_dir.resolve()
    report_root.mkdir(parents=True, exist_ok=True)
    timestamp = started_at.strftime("%Y%m%dT%H%M%S%fZ")
    report_path = report_root / f"maintenance-{timestamp}.json"
    serialized = json.dumps(report, indent=2, sort_keys=True) + "\n"
    _atomic_write(report_path, serialized)
    _atomic_write(report_root / "latest.json", serialized)
    return report_path


def _atomic_write(path: Path, content: str) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _send_failure_notification(webhook_url: str, report: dict[str, object]) -> None:
    payload = json.dumps({"event": "tradeforge_maintenance_failed", "report": report}).encode("utf-8")
    request = Request(webhook_url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        if response.status >= 400:
            raise RuntimeError(f"Failure webhook returned HTTP {response.status}.")


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _format_timestamp(value: datetime) -> str:
    return _ensure_utc(value).isoformat().replace("+00:00", "Z")
