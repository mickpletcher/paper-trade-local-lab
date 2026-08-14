from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from tradeforge.automation.maintenance import MaintenanceError, backup_sqlite_database, run_maintenance
from tradeforge.config import get_settings
from tradeforge.database.models import PriceBar
from tradeforge.database.session import session_scope


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
    assert result["imports"] == [{"file": "AAPL.csv", "symbol": "AAPL", "rows_upserted": 1}]
    assert result["quotes"] == {"requested": [], "refreshed_count": 0}
    assert (tmp_path / result["backup_path"]).is_file()
    latest_report = json.loads((tmp_path / "data" / "automation" / "latest.json").read_text(encoding="utf-8"))
    assert latest_report["status"] == "success"
    with session_scope() as session:
        assert len(session.scalars(select(PriceBar)).all()) == 1


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
    assert "invalid OHLC relationships" in latest_report["error"]
    assert notifications == [{"url": "https://alerts.example.test/tradeforge", "status": "failed"}]


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
