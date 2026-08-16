from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from tests.conftest import add_bar
from tradeforge.automation.environment import inspect_environment, verify_lock_provenance
from tradeforge.automation.locking import MaintenanceLock, MaintenanceLockError
from tradeforge.automation.maintenance import (
    _write_report,
    acknowledge_quarantined_import,
    build_local_health,
    inspect_sqlite_health,
)
from tradeforge.automation.notifications import _send_email, _send_teams, send_escalations
from tradeforge.broker_sim.account import SimAccount
from tradeforge.broker_sim.execution import SimBroker
from tradeforge.broker_sim.orders import OrderRequest
from tradeforge.broker_sim.risk import RiskEngine, RiskLimitError, RiskLimits
from tradeforge.config import Settings
from tradeforge.corporate_actions import apply_corporate_action, record_corporate_action
from tradeforge.database.models import (
    CorporateAction,
    DataQualityEvent,
    ExecutionAuditEvent,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    Trade,
)
from tradeforge.market_data.importer import import_ohlcv_csv
from tradeforge.market_data.live import AlpacaSnapshotQuoteProvider, QuoteCircuitBreaker, QuoteProviderError


def test_risk_engine_rejects_order_and_records_audit(session, symbol) -> None:
    account = SimAccount.with_starting_cash(10_000)
    risk = RiskEngine(
        session,
        account,
        RiskLimits(500, 100, 5_000, 0.25),
        None,
    )
    risk.update_mark(symbol.id, 100)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0, risk_engine=risk)

    with pytest.raises(RiskLimitError, match="maximum notional"):
        broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 6))

    event = session.scalar(select(ExecutionAuditEvent))
    assert event is not None
    assert event.event_type == "rejected"
    assert event.remaining_quantity is None


def test_risk_engine_enforces_kill_switch_and_drawdown(session, symbol) -> None:
    account = SimAccount.with_starting_cash(1_000)
    position = Position(symbol_id=symbol.id, quantity=5, average_cost=100)
    session.add(position)
    session.flush()
    killed = RiskEngine(session, account, RiskLimits(10_000, 100, 10_000, 0.1, True), None)
    with pytest.raises(RiskLimitError, match="kill switch"):
        killed.validate_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 1), 100)

    account.cash = 0
    drawdown = RiskEngine(session, account, RiskLimits(10_000, 100, 10_000, 0.1), None)
    drawdown.update_mark(symbol.id, 100)
    drawdown.update_mark(symbol.id, 50)
    with pytest.raises(RiskLimitError, match="drawdown"):
        drawdown.validate_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 1), 50)
    drawdown.validate_order(OrderRequest(symbol.id, OrderSide.SELL, OrderType.MARKET, 1), 50)


def test_risk_engine_enforces_cumulative_partial_fill_notional(session, symbol) -> None:
    first_bar = add_bar(session, symbol, 1, 110, 111, 109, 110)
    second_bar = add_bar(session, symbol, 2, 110, 111, 109, 110)
    first_bar.volume = 100
    second_bar.volume = 100
    account = SimAccount.with_starting_cash(20_000)
    risk = RiskEngine(session, account, RiskLimits(10_000, 1_000, 100_000, 1), None)
    risk.update_mark(symbol.id, 90)
    broker = SimBroker(
        session,
        account,
        fee_per_order=0,
        slippage_bps=0,
        max_bar_fill_ratio=0.5,
        risk_engine=risk,
    )
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 100),
        submitted_at=first_bar.timestamp,
    )

    assert len(broker.process_bar(first_bar)) == 1
    assert broker.process_bar(second_bar) == []
    assert order.filled_quantity == 50
    assert order.status == OrderStatus.REJECTED.value


def test_execution_audit_tracks_trigger_cancel_and_remaining_quantity(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 105, 95, 101)
    broker = SimBroker(
        session,
        SimAccount.with_starting_cash(10_000),
        fee_per_order=0,
        slippage_bps=0,
        max_bar_fill_ratio=0.01,
    )
    stop = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.STOP, 20, stop_price=102),
        submitted_at=bar.timestamp,
    )
    broker.process_bar(bar)
    broker.cancel_order(stop.id)

    events = list(session.scalars(select(ExecutionAuditEvent).order_by(ExecutionAuditEvent.timestamp)))
    assert [event.event_type for event in events] == ["triggered", "remaining_quantity_changed", "cancelled"]
    assert events[1].remaining_quantity == 10


def test_data_quality_repairs_duplicates_and_records_findings(session, tmp_path) -> None:
    csv_path = tmp_path / "quality.csv"
    csv_path.write_text(
        "date,open,high,low,close,volume\n"
        "2023-01-01,100,110,99,105,1000\n"
        "2023-01-01,101,111,100,106,1100\n"
        "2023-01-10,107,112,105,108,1200\n",
        encoding="utf-8",
    )

    assert import_ohlcv_csv(session, "AAPL", csv_path) == 2
    events = list(session.scalars(select(DataQualityEvent)))
    assert {event.issue_type for event in events} == {
        "timezone_normalized",
        "duplicate_timestamp",
        "timestamp_gap",
    }
    assert {event.repair_action for event in events} == {"assume_utc", "keep_last", "record_only"}


def test_data_quality_rejects_return_outliers(session, tmp_path) -> None:
    csv_path = tmp_path / "outlier.csv"
    csv_path.write_text(
        "date,open,high,low,close,volume\n2023-01-01,100,110,99,100,1000\n2023-01-02,200,210,190,200,1000\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="outliers"):
        import_ohlcv_csv(session, "AAPL", csv_path)


@pytest.mark.parametrize(
    ("action_type", "kwargs", "expected_quantity", "expected_cash"),
    [
        ("split", {"ratio": 2.0}, 20.0, 1_000.0),
        ("dividend", {"cash_amount": 1.5}, 10.0, 1_015.0),
        ("delisting", {"cash_amount": 25.0}, 0.0, 1_250.0),
    ],
)
def test_corporate_actions_adjust_account_and_position(
    session,
    symbol,
    action_type,
    kwargs,
    expected_quantity,
    expected_cash,
) -> None:
    position = Position(symbol_id=symbol.id, quantity=10, average_cost=50)
    session.add(position)
    action = record_corporate_action(
        session,
        symbol.ticker,
        action_type,
        datetime(2026, 8, 16, tzinfo=UTC),
        **kwargs,
    )
    account = SimAccount.with_starting_cash(1_000)
    apply_corporate_action(session, account, position, action, strategy_run_id=None)
    event = session.scalar(select(ExecutionAuditEvent).where(ExecutionAuditEvent.event_type == "corporate_action"))
    assert position.quantity == expected_quantity
    assert account.cash == expected_cash
    assert event is not None
    if action_type == "delisting":
        assert symbol.is_active is False


def test_split_rejects_invalid_ratio_and_adjusts_open_orders(session, symbol) -> None:
    position = Position(symbol_id=symbol.id, quantity=10, average_cost=50)
    order = Order(
        symbol_id=symbol.id,
        side=OrderSide.BUY.value,
        order_type=OrderType.STOP_LIMIT.value,
        quantity=10,
        filled_quantity=4,
        limit_price=100,
        stop_price=90,
        status=OrderStatus.PARTIALLY_FILLED.value,
    )
    session.add_all([position, order])
    invalid = CorporateAction(
        symbol_id=symbol.id,
        action_type="split",
        effective_at=datetime(2026, 8, 16, tzinfo=UTC),
        ratio=None,
    )
    session.add(invalid)
    session.flush()
    with pytest.raises(ValueError, match="positive ratio"):
        apply_corporate_action(session, SimAccount(), position, invalid, strategy_run_id=None)

    valid = CorporateAction(
        symbol_id=symbol.id,
        action_type="split",
        effective_at=datetime(2026, 8, 17, tzinfo=UTC),
        ratio=2,
    )
    session.add(valid)
    session.flush()
    apply_corporate_action(session, SimAccount(), position, valid, strategy_run_id=None)

    assert position.quantity == 20
    assert position.average_cost == 25
    assert order.quantity == 20
    assert order.filled_quantity == 8
    assert order.limit_price == 50
    assert order.stop_price == 45


def test_delisting_closes_trade_and_realizes_pnl(session, symbol) -> None:
    position = Position(symbol_id=symbol.id, quantity=10, average_cost=50)
    trade = Trade(
        symbol_id=symbol.id,
        opened_at=datetime(2026, 8, 1, tzinfo=UTC),
        quantity=10,
        entry_price=49,
        entry_fee=10,
    )
    session.add_all([position, trade])
    action = record_corporate_action(
        session,
        symbol.ticker,
        "delisting",
        datetime(2026, 8, 16, tzinfo=UTC),
        cash_amount=60,
    )
    account = SimAccount.with_starting_cash(1_000)

    apply_corporate_action(session, account, position, action, strategy_run_id=None)

    assert account.cash == 1_600
    assert position.realized_pnl == 100
    assert trade.exit_price == 60
    assert trade.realized_pnl == 100
    assert trade.closed_at == action.effective_at


def test_symbol_change_updates_ticker(session, symbol) -> None:
    position = Position(symbol_id=symbol.id, quantity=0, average_cost=0)
    session.add(position)
    action = record_corporate_action(
        session,
        "AAPL",
        "symbol_change",
        datetime(2026, 8, 16, tzinfo=UTC),
        new_ticker="APPLX",
    )
    apply_corporate_action(session, SimAccount(), position, action, strategy_run_id=None)
    assert symbol.ticker == "APPLX"


def test_quote_circuit_breaker_opens_and_resets(tmp_path) -> None:
    state_path = tmp_path / "circuit.json"
    circuit = QuoteCircuitBreaker(state_path, failure_threshold=2, reset_seconds=300)
    circuit.record_failure()
    circuit.ensure_available()
    circuit.record_failure()
    with pytest.raises(QuoteProviderError, match="circuit is open"):
        circuit.ensure_available()
    circuit.record_success()
    circuit.ensure_available()
    assert not state_path.exists()


def test_quote_circuit_breaker_self_heals_invalid_failure_count(tmp_path) -> None:
    state_path = tmp_path / "circuit.json"
    state_path.write_text('{"failures":"invalid"}\n', encoding="utf-8")
    circuit = QuoteCircuitBreaker(state_path, failure_threshold=2, reset_seconds=300)
    circuit.ensure_available()
    circuit.record_failure()
    assert json.loads(state_path.read_text(encoding="utf-8"))["failures"] == 1


def test_provider_contract_failure_opens_circuit(monkeypatch, tmp_path) -> None:
    response = MagicMock()
    response.read.return_value = b"{}"
    response.__enter__.return_value = response
    monkeypatch.setattr("tradeforge.market_data.live._open_quote_request", lambda request, timeout: response)
    settings = Settings(
        TRADEFORGE_ALPACA_API_KEY_ID="key",
        TRADEFORGE_ALPACA_API_SECRET_KEY="secret",
        TRADEFORGE_QUOTE_CIRCUIT_STATE_PATH=tmp_path / "circuit.json",
        TRADEFORGE_QUOTE_CIRCUIT_FAILURE_THRESHOLD=1,
    )
    provider = AlpacaSnapshotQuoteProvider(settings)
    with pytest.raises(QuoteProviderError, match="symbol mismatch"):
        provider.get_latest_quotes(["AAPL"])
    with pytest.raises(QuoteProviderError, match="circuit is open"):
        provider.get_latest_quotes(["AAPL"])


def test_maintenance_lock_rejects_overlap(tmp_path) -> None:
    lock_path = tmp_path / "maintenance.lock"
    with (
        MaintenanceLock(lock_path, stale_seconds=60),
        pytest.raises(MaintenanceLockError, match="already running"),
        MaintenanceLock(lock_path, stale_seconds=60),
    ):
        pass
    assert not lock_path.exists()


def test_escalations_retry_and_suppress_duplicates(monkeypatch, tmp_path) -> None:
    attempts = 0

    def flaky_send(url, report) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary")

    monkeypatch.setattr("tradeforge.automation.notifications._send_teams", flaky_send)
    monkeypatch.setattr("tradeforge.automation.notifications.sleep", lambda seconds: None)
    settings = Settings(
        TRADEFORGE_FAILURE_TEAMS_WEBHOOK_URL="https://teams.example.test/hook",
        TRADEFORGE_NOTIFICATION_STATE_PATH=tmp_path / "state.json",
    )
    report = {"status": "failed", "error": "same failure"}
    assert send_escalations(settings, report) == {"teams": "sent"}
    assert send_escalations(settings, report) == {"teams": "suppressed_duplicate"}
    assert attempts == 2


def test_lock_provenance_rejects_tampering(tmp_path) -> None:
    lock = tmp_path / "requirements.lock"
    metadata = tmp_path / "provenance.json"
    lock.write_text("sample==1.0\n", encoding="utf-8")
    metadata.write_text(
        json.dumps(
            {
                "attestation": "github-oidc-sigstore",
                "attestation_workflow": ".github/workflows/ci.yml",
                "generation_command": "uv pip compile --universal --python-version 3.11",
                "sha256": "invalid",
                "source_index": "https://pypi.org/simple",
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="digest"):
        verify_lock_provenance(lock, metadata)


def test_lock_provenance_accepts_windows_line_endings(tmp_path) -> None:
    lock = tmp_path / "requirements.lock"
    metadata = tmp_path / "provenance.json"
    lock.write_bytes(b"sample==1.0\r\n")
    metadata.write_text(
        json.dumps(
            {
                "attestation": "github-oidc-sigstore",
                "attestation_workflow": ".github/workflows/ci.yml",
                "generation_command": "uv pip compile --universal --python-version 3.11",
                "sha256": sha256(b"sample==1.0\n").hexdigest(),
                "source_index": "https://pypi.org/simple",
            }
        ),
        encoding="utf-8",
    )

    assert verify_lock_provenance(lock, metadata)["status"] == "verified"


def test_environment_doctor_reports_package_drift(monkeypatch, tmp_path) -> None:
    lock = tmp_path / "requirements.lock"
    lock.write_text("alpha==1.0\nbeta==2.0\n", encoding="utf-8")
    installed = [
        SimpleNamespace(metadata={"Name": "alpha"}, version="0.9"),
        SimpleNamespace(metadata={"Name": "extra"}, version="3.0"),
        SimpleNamespace(metadata={"Name": "pip"}, version="99"),
    ]
    monkeypatch.setattr("tradeforge.automation.environment.distributions", lambda: installed)

    result = inspect_environment(lock)

    assert result["status"] == "drifted"
    assert result["missing"] == ["beta"]
    assert result["mismatched"] == [{"package": "alpha", "expected": "1.0", "installed": "0.9"}]
    assert result["undeclared"] == ["extra"]


def test_environment_doctor_accepts_exact_environment(monkeypatch, tmp_path) -> None:
    lock = tmp_path / "requirements.lock"
    lock.write_text("alpha==1.0\n", encoding="utf-8")
    installed = [SimpleNamespace(metadata={"Name": "alpha"}, version="1.0")]
    monkeypatch.setattr("tradeforge.automation.environment.distributions", lambda: installed)
    assert inspect_environment(lock)["status"] == "healthy"


def test_environment_doctor_skips_distribution_without_name(monkeypatch, tmp_path) -> None:
    lock = tmp_path / "requirements.lock"
    lock.write_text("", encoding="utf-8")
    installed = [SimpleNamespace(metadata={}, version="1.0")]
    monkeypatch.setattr("tradeforge.automation.environment.distributions", lambda: installed)

    result = inspect_environment(lock)

    assert result["status"] == "healthy"
    assert result["installed_count"] == 0


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("source_index", "https://example.test/simple", "approved PyPI"),
        ("attestation", "none", "OIDC signing"),
        ("attestation_workflow", "other.yml", "not approved"),
        ("generation_command", "uv pip compile", "incomplete"),
    ],
)
def test_lock_provenance_rejects_unapproved_metadata(tmp_path, field, value, message) -> None:
    lock = tmp_path / "requirements.lock"
    metadata = tmp_path / "provenance.json"
    lock.write_text("sample==1.0\n", encoding="utf-8")
    payload = {
        "attestation": "github-oidc-sigstore",
        "attestation_workflow": ".github/workflows/ci.yml",
        "generation_command": "uv pip compile --universal --python-version 3.11",
        "sha256": sha256(lock.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "source_index": "https://pypi.org/simple",
    }
    payload[field] = value
    metadata.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        verify_lock_provenance(lock, metadata)


def test_local_health_reports_healthy_automation(tmp_path) -> None:
    database = tmp_path / "tradeforge.db"
    with closing(sqlite3.connect(database)) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
        connection.execute("PRAGMA journal_mode=WAL")
    report_dir = tmp_path / "automation"
    report_dir.mkdir()
    (report_dir / "latest.json").write_text('{"status":"success"}\n', encoding="utf-8")
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    (backup_dir / "tradeforge-1.db").write_bytes(database.read_bytes())
    settings = Settings(
        TRADEFORGE_DATABASE_URL=f"sqlite:///{database.as_posix()}",
        TRADEFORGE_AUTOMATION_REPORT_DIR=report_dir,
        TRADEFORGE_BACKUP_DIR=backup_dir,
        TRADEFORGE_IMPORT_DIR=tmp_path / "imports",
        TRADEFORGE_QUARANTINE_IMPORT_DIR=tmp_path / "quarantine",
        TRADEFORGE_MAINTENANCE_LOCK_PATH=tmp_path / "maintenance.lock",
    )

    result = build_local_health(settings)

    assert result["status"] == "healthy"
    assert result["database"]["integrity"] == "ok"
    assert result["backup_count"] == 1


def test_report_retention_keeps_newest_files(tmp_path) -> None:
    for second in range(3):
        _write_report(
            tmp_path,
            {"status": "success", "sequence": second},
            datetime(2026, 8, 16, 12, 0, second, tzinfo=UTC),
            retention_count=2,
        )
    reports = sorted(tmp_path.glob("maintenance-*.json"))
    assert len(reports) == 2
    assert json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))["sequence"] == 2


def test_report_retention_records_unlink_failures(monkeypatch, tmp_path) -> None:
    old_report = tmp_path / "maintenance-20260816T120000000000Z.json"
    old_report.write_text("{}\n", encoding="utf-8")
    original_unlink = Path.unlink

    def fail_old_report(path: Path, *args, **kwargs) -> None:
        if path == old_report:
            raise PermissionError("locked")
        original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_old_report)
    report: dict[str, object] = {"status": "success"}

    _write_report(
        tmp_path,
        report,
        datetime(2026, 8, 16, 12, 0, 1, tzinfo=UTC),
        retention_count=1,
    )

    assert report["retention_errors"] == [{"path": str(old_report), "error": "PermissionError: locked"}]
    assert json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))["retention_errors"]


def test_quarantine_acknowledgement_moves_file_and_clears_error(tmp_path) -> None:
    quarantine = tmp_path / "quarantine"
    quarantine.mkdir()
    source = quarantine / "failed.csv"
    source.write_text("data", encoding="utf-8")
    error = quarantine / "failed.csv.error.json"
    error.write_text("{}", encoding="utf-8")
    settings = Settings(
        TRADEFORGE_IMPORT_DIR=tmp_path / "imports",
        TRADEFORGE_PROCESSED_IMPORT_DIR=tmp_path / "processed",
        TRADEFORGE_QUARANTINE_IMPORT_DIR=quarantine,
    )

    destination = acknowledge_quarantined_import(settings, "failed.csv", retry=True)

    assert destination == (tmp_path / "imports" / "failed.csv")
    assert destination.is_file()
    assert not error.exists()
    with pytest.raises(ValueError, match="directory path"):
        acknowledge_quarantined_import(settings, "../failed.csv", retry=False)
    with pytest.raises(FileNotFoundError, match="not found"):
        acknowledge_quarantined_import(settings, "missing.csv", retry=False)


def test_quarantine_retry_restores_original_import_filename(tmp_path) -> None:
    quarantine = tmp_path / "quarantine"
    quarantine.mkdir()
    archived_name = "20260816T120000000000Z-AAPL.csv"
    source = quarantine / archived_name
    source.write_text("data", encoding="utf-8")
    error = quarantine / f"{archived_name}.error.json"
    error.write_text('{"file":"AAPL.csv"}', encoding="utf-8")
    settings = Settings(
        TRADEFORGE_IMPORT_DIR=tmp_path / "imports",
        TRADEFORGE_PROCESSED_IMPORT_DIR=tmp_path / "processed",
        TRADEFORGE_QUARANTINE_IMPORT_DIR=quarantine,
    )

    destination = acknowledge_quarantined_import(settings, archived_name, retry=True)

    assert destination == tmp_path / "imports" / "AAPL.csv"
    assert destination.is_file()
    assert not error.exists()


def test_non_sqlite_health_reports_backend_only() -> None:
    engine = MagicMock()
    engine.dialect.name = "postgresql"
    assert inspect_sqlite_health(engine) == {"backend": "postgresql"}


def test_teams_escalation_sends_minimal_message(monkeypatch) -> None:
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
            captured["payload"] = json.loads(request.data)
            captured["timeout"] = timeout
            return Response()

    monkeypatch.setattr("tradeforge.automation.notifications.build_opener", lambda handler: Opener())
    _send_teams("https://teams.example.test/hook", {"started_at": "start", "completed_at": "end"})
    assert captured == {
        "url": "https://teams.example.test/hook",
        "payload": {"text": "TradeForge maintenance failed. Started: start. Completed: end."},
        "timeout": 10,
    }


def test_email_escalation_uses_starttls_and_authentication(monkeypatch) -> None:
    calls: list[object] = []

    class SMTP:
        def __init__(self, host, port, timeout):
            calls.append((host, port, timeout))

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback) -> None:
            return None

        def starttls(self, context) -> None:
            calls.append("starttls")

        def login(self, username, password) -> None:
            calls.append((username, password))

        def send_message(self, message, to_addrs) -> None:
            calls.append((message["Subject"], to_addrs))

    monkeypatch.setattr("tradeforge.automation.notifications.smtplib.SMTP", SMTP)
    settings = Settings(
        TRADEFORGE_SMTP_HOST="smtp.example.test",
        TRADEFORGE_SMTP_USERNAME="user",
        TRADEFORGE_SMTP_PASSWORD="password",
        TRADEFORGE_SMTP_FROM="from@example.test",
        TRADEFORGE_SMTP_TO="one@example.test,two@example.test",
    )
    _send_email(settings, {"started_at": "start", "completed_at": "end"})
    assert calls[0] == ("smtp.example.test", 587, 10)
    assert "starttls" in calls
    assert ("user", "password") in calls
    assert calls[-1] == ("TradeForge maintenance failed", ["one@example.test", "two@example.test"])


def test_email_escalation_requires_complete_configuration() -> None:
    with pytest.raises(ValueError, match="requires"):
        _send_email(Settings(TRADEFORGE_SMTP_HOST="smtp.example.test"), {})


def test_stale_maintenance_lock_is_replaced(tmp_path) -> None:
    lock_path = tmp_path / "maintenance.lock"
    lock_path.write_text("{}", encoding="utf-8")
    os.utime(lock_path, (0, 0))
    with MaintenanceLock(lock_path, stale_seconds=60):
        assert lock_path.exists()
    assert not lock_path.exists()
