from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from tradeforge.cli import _parse_date_option, app


def test_seed_and_backtest_cli_flow(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}

    seed_result = runner.invoke(app, ["seed-sample-data"], env=env, catch_exceptions=False)
    assert seed_result.exit_code == 0
    assert "Seeded 8 sample bars for AAPL." in seed_result.stdout

    backtest_result = runner.invoke(
        app,
        [
            "run-backtest",
            "--strategy",
            "moving-average-cross",
            "--symbol",
            "AAPL",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-08",
            "--short-window",
            "2",
            "--long-window",
            "3",
            "--order-size",
            "2",
        ],
        env=env,
        catch_exceptions=False,
    )
    assert backtest_result.exit_code == 0
    payload = json.loads(backtest_result.stdout)
    assert payload["metrics"]["number_of_fills"] == 2
    assert payload["metrics"]["number_of_trades"] == 1
    assert payload["metrics"]["ending_equity"] > 0
    assert (tmp_path / payload["report_path"]).exists()

    orders_result = runner.invoke(app, ["show-orders"], env=env, catch_exceptions=False)
    assert orders_result.exit_code == 0
    assert "status=filled" in orders_result.stdout
    assert "status=cancelled" in orders_result.stdout

    assert Path(tmp_path, "data", "tradeforge.db").exists()


def test_run_backtest_rejects_unknown_strategy(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}

    result = runner.invoke(
        app,
        [
            "run-backtest",
            "--strategy",
            "nope",
            "--symbol",
            "AAPL",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-08",
        ],
        env=env,
    )

    assert result.exit_code != 0
    assert "Unknown strategy 'nope'" in result.output


def test_run_backtest_rejects_missing_symbol(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}

    result = runner.invoke(
        app,
        [
            "run-backtest",
            "--strategy",
            "moving-average-cross",
            "--symbol",
            "MSFT",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-08",
        ],
        env=env,
    )

    assert result.exit_code != 0
    assert "Unknown symbol 'MSFT'" in result.output


def test_run_backtest_rejects_invalid_date_range(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}

    result = runner.invoke(
        app,
        [
            "run-backtest",
            "--strategy",
            "moving-average-cross",
            "--symbol",
            "AAPL",
            "--start",
            "2023-01-08",
            "--end",
            "2023-01-01",
        ],
        env=env,
    )

    assert result.exit_code != 0
    assert "start date must be earlier than the end date" in result.output


def test_run_backtest_rejects_invalid_strategy_parameters(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}

    result = runner.invoke(
        app,
        [
            "run-backtest",
            "--strategy",
            "moving-average-cross",
            "--symbol",
            "AAPL",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-08",
            "--short-window",
            "3",
            "--long-window",
            "2",
        ],
        env=env,
    )

    assert result.exit_code == 2
    assert "short_window must be less than long_window" in result.output


def test_run_backtest_rejects_invalid_date_format(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}

    with pytest.raises(typer.BadParameter, match=r"--start must be a valid ISO date or datetime string\."):
        _parse_date_option("--start", "not-a-date")

    result = runner.invoke(
        app,
        [
            "run-backtest",
            "--strategy",
            "moving-average-cross",
            "--symbol",
            "AAPL",
            "--start",
            "not-a-date",
            "--end",
            "2023-01-08",
        ],
        env=env,
    )

    assert result.exit_code == 2


def test_start_api_uses_uvicorn(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    captured: dict[str, object] = {}
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}

    def fake_run(app_path: str, host: str, port: int, reload: bool) -> None:
        captured["app_path"] = app_path
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    monkeypatch.setattr("tradeforge.cli.uvicorn.run", fake_run)

    result = runner.invoke(
        app,
        ["start-api", "--host", "0.0.0.0", "--port", "9000", "--reload"],
        env=env,
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert captured == {
        "app_path": "tradeforge.api.app:app",
        "host": "0.0.0.0",
        "port": 9000,
        "reload": True,
    }


def test_refresh_quotes_uses_requested_symbols(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}
    seen: dict[str, object] = {}

    def fake_refresh_live_quotes(session, symbols):
        seen["symbols"] = symbols
        return [object()]

    seed_result = runner.invoke(app, ["seed-sample-data"], env=env, catch_exceptions=False)
    assert seed_result.exit_code == 0

    monkeypatch.setattr("tradeforge.cli.refresh_live_quotes", fake_refresh_live_quotes)

    result = runner.invoke(app, ["refresh-quotes", "--symbol", "AAPL"], env=env, catch_exceptions=False)

    assert result.exit_code == 0
    assert seen["symbols"] == ["AAPL"]
    assert "Refreshed 1 quotes" in result.stdout
