from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from urllib.request import Request

import pytest
from sqlalchemy import select

from tradeforge.automation.maintenance import (
    MaintenanceError,
    _RejectWebhookRedirects,
    _send_failure_notification,
    backup_sqlite_database,
    run_maintenance,
)
from tradeforge.config import get_settings
from tradeforge.database.models import PriceBar
from tradeforge.database.session import get_engine, session_scope


def test_maintenance_imports_backs_up_and_reports(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")
    import_dir = tmp_path / "data" / "imports"
    import_dir.mkdir(parents=True)
    (import_dir / "AAPL.csv").write_text(
        "date,open,high,low,close,volume\n2023-01-01,100,110,99,105,1000\n",
        encoding="utf-8",
    )

    result = run_maintenance(get_settings(), now=datetime(2026, 8, 14, 12, 0, tzinfo=UTC))

    assert result["status"] == "success"
    assert result["imports"][0]["file"] == "AAPL.csv"
    assert result["imports"][0]["status"] == "imported"
    assert result["imports"][0]["rows_upserted"] == 1
    assert result["restore_drill"]["status"] == "verified"
    assert result["database"]["journal_mode"] == "wal"
    assert not (import_dir / "AAPL.csv").exists()
    assert result["quotes"] == {"requested": [], "refreshed_count": 0}
    assert (tmp_path / result["backup_path"]).is_file()
    latest_report = json.loads((tmp_path / "data" / "automation" / "latest.json").read_text(encoding="utf-8"))
    assert latest_report["status"] == "success"
    with session_scope() as session:
        assert len(session.scalars(select(PriceBar)).all()) == 1


def test_maintenance_reuses_and_disposes_one_engine(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")
    settings = get_settings().model_copy(update={"sqlite_busy_timeout_ms": 1_250})
    engine = get_engine(settings.database_url, settings.sqlite_busy_timeout_ms)
    dispose_spy = MagicMock(wraps=engine.dispose)
    monkeypatch.setattr(engine, "dispose", dispose_spy)
    engine_requests: list[tuple[str, int]] = []

    def tracked_get_engine(database_url: str, sqlite_busy_timeout_ms: int):
        engine_requests.append((database_url, sqlite_busy_timeout_ms))
        return engine

    monkeypatch.setattr("tradeforge.automation.maintenance.get_engine", tracked_get_engine)

    result = run_maintenance(settings, now=datetime(2026, 8, 14, 12, 0, tzinfo=UTC))

    assert result["status"] == "success"
    assert engine_requests == [(settings.database_url, 1_250)]
    dispose_spy.assert_called_once_with()


def test_maintenance_reports_failure_and_notifies(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")
    monkeypatch.setenv("TRADEFORGE_FAILURE_WEBHOOK_URL", "https://alerts.example.test/tradeforge")
    import_dir = tmp_path / "data" / "imports"
    import_dir.mkdir(parents=True)
    (import_dir / "AAPL.csv").write_text(
        "date,open,high,low,close,volume\n2023-01-01,100,90,99,105,1000\n",
        encoding="utf-8",
    )
    notifications: list[dict[str, object]] = []
    monkeypatch.setattr(
        "tradeforge.automation.maintenance._send_failure_notification",
        lambda webhook_url, report: notifications.append({"url": webhook_url, "status": report["status"]}),
    )

    with pytest.raises(MaintenanceError) as exc_info:
        run_maintenance(get_settings(), now=datetime(2026, 8, 14, 12, 0, tzinfo=UTC))

    assert exc_info.value.report_path is not None
    latest_report = json.loads((tmp_path / "data" / "automation" / "latest.json").read_text(encoding="utf-8"))
    assert latest_report["status"] == "failed"
    assert "were quarantined" in latest_report["error"]
    assert "invalid OHLC relationships" in latest_report["imports"][0]["error"]
    assert latest_report["imports"][0]["status"] == "quarantined"
    assert notifications == [{"url": "https://alerts.example.test/tradeforge", "status": "failed"}]


def test_failure_notification_sends_only_minimal_status(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class Response:
        status = 204

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            return None

    class Opener:
        def open(self, request, timeout):
            captured["url"] = request.full_url
            captured["timeout"] = timeout
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return Response()

    def fake_build_opener(*handlers):
        captured["redirect_handler"] = type(handlers[0]).__name__
        return Opener()

    monkeypatch.setattr("tradeforge.automation.maintenance.build_opener", fake_build_opener)
    report = {
        "status": "failed",
        "started_at": "2026-08-15T12:00:00Z",
        "completed_at": "2026-08-15T12:00:01Z",
        "error": "secret local path",
        "imports": [{"file": "private.csv", "symbol": "AAPL"}],
    }

    _send_failure_notification("https://alerts.example.test/tradeforge", report)

    assert captured == {
        "redirect_handler": "_RejectWebhookRedirects",
        "url": "https://alerts.example.test/tradeforge",
        "timeout": 10,
        "payload": {
            "event": "tradeforge_maintenance_failed",
            "status": "failed",
            "started_at": "2026-08-15T12:00:00Z",
            "completed_at": "2026-08-15T12:00:01Z",
        },
    }


@pytest.mark.parametrize(
    "webhook_url",
    [
        "http://alerts.example.test/tradeforge",
        "file:///tmp/alerts",
        "https:///missing-host",
        "https://user:password@alerts.example.test/tradeforge",  # pragma: allowlist secret
        " https://alerts.example.test/tradeforge",
    ],
)
def test_failure_notification_rejects_unsafe_urls(monkeypatch, webhook_url: str) -> None:
    monkeypatch.setattr(
        "tradeforge.automation.maintenance.build_opener",
        lambda *handlers: pytest.fail("unsafe webhook reached the network opener"),
    )

    with pytest.raises(ValueError, match="no whitespace"):
        _send_failure_notification(webhook_url, {"status": "failed"})


def test_failure_notification_rejects_redirects() -> None:
    handler = _RejectWebhookRedirects()

    with pytest.raises(RuntimeError, match="redirects are not allowed"):
        handler.redirect_request(
            Request("https://alerts.example.test/tradeforge"),
            None,
            302,
            "Found",
            {"Location": "http://internal.example.test/"},
            "http://internal.example.test/",
        )


def test_maintenance_creates_custom_sqlite_parent(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///nested/database/tradeforge.db")

    result = run_maintenance(get_settings(), now=datetime(2026, 8, 14, 12, 0, tzinfo=UTC))

    assert result["status"] == "success"
    assert (tmp_path / "nested" / "database" / "tradeforge.db").is_file()


def test_backup_retention_keeps_newest_verified_copies(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    database = tmp_path / "tradeforge.db"
    with session_scope(f"sqlite:///{database.as_posix()}") as session:
        session.execute(select(1))
    backup_dir = tmp_path / "backups"
    start = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)

    for offset in range(3):
        backup_sqlite_database(database, backup_dir, retention_count=2, now=start + timedelta(seconds=offset))

    backups = sorted(backup_dir.glob("tradeforge-*.db"))
    assert len(backups) == 2
    assert "120001" in backups[0].name
    assert "120002" in backups[1].name
