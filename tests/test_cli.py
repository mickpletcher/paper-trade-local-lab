from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from tradeforge.cli import _parse_date_option, app


def test_init_db_command_name_is_preserved(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["init-db"],
        env={"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"},
        catch_exceptions=False,
    )

    assert result.exit_code == 0
    assert (tmp_path / "data" / "tradeforge.db").is_file()


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


def test_tier_three_research_cli_flow(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}
    for ticker in ("AAPL", "MSFT"):
        result = runner.invoke(app, ["seed-sample-data", "--symbol", ticker], env=env, catch_exceptions=False)
        assert result.exit_code == 0

    portfolio_result = runner.invoke(
        app,
        [
            "run-portfolio-backtest",
            "--symbol",
            "AAPL",
            "--symbol",
            "MSFT",
            "--start",
            "2023-01-01",
            "--end",
            "2023-01-08",
            "--total-cash",
            "20000",
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
    analytics_result = runner.invoke(
        app,
        ["analyze-symbol", "--symbol", "AAPL", "--benchmark-symbol", "MSFT", "--window", "2"],
        env=env,
        catch_exceptions=False,
    )
    experiments_result = runner.invoke(app, ["show-experiments"], env=env, catch_exceptions=False)
    plugins_result = runner.invoke(app, ["list-plugins"], env=env, catch_exceptions=False)
    connectors_result = runner.invoke(app, ["list-connectors"], env=env, catch_exceptions=False)
    benchmark_result = runner.invoke(
        app,
        ["benchmark-performance", "--rows", "1000", "--maximum-seconds", "2"],
        env=env,
        catch_exceptions=False,
    )

    portfolio = json.loads(portfolio_result.stdout)
    analytics = json.loads(analytics_result.stdout)
    experiments = json.loads(experiments_result.stdout)
    assert portfolio["allocations"] == {"AAPL": 10000.0, "MSFT": 10000.0}
    assert len(portfolio["runs"]) == 2
    assert analytics["beta"] == pytest.approx(1)
    assert len(experiments) == 2
    assert any(item["name"] == "moving-average-cross" for item in json.loads(plugins_result.stdout))
    assert any(item["name"] == "tradier" for item in json.loads(connectors_result.stdout))
    assert json.loads(benchmark_result.stdout)["rows"] == 1000


def test_tier_three_identity_and_disaster_recovery_cli_flow(monkeypatch, tmp_path) -> None:
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    env = {"TRADEFORGE_DATABASE_URL": "sqlite:///data/tradeforge.db"}

    tenant_result = runner.invoke(app, ["create-tenant", "--name", "automation"], env=env, catch_exceptions=False)
    tenant_id = json.loads(tenant_result.stdout)["id"]
    key_result = runner.invoke(
        app,
        ["create-api-key", "--tenant-id", tenant_id, "--name", "reader", "--role", "viewer"],
        env=env,
        catch_exceptions=False,
    )
    key_payload = json.loads(key_result.stdout)
    list_result = runner.invoke(app, ["show-api-keys", "--tenant-id", tenant_id], env=env, catch_exceptions=False)
    rotate_result = runner.invoke(
        app,
        ["rotate-api-key", "--api-key-id", key_payload["id"], "--expires-in-days", "30"],
        env=env,
        catch_exceptions=False,
    )
    replacement = json.loads(rotate_result.stdout)
    revoke_result = runner.invoke(
        app,
        ["revoke-api-key", "--api-key-id", replacement["id"]],
        env=env,
        catch_exceptions=False,
    )
    maintenance_result = runner.invoke(app, ["run-maintenance"], env=env, catch_exceptions=False)
    drill_result = runner.invoke(app, ["run-dr-drill"], env=env, catch_exceptions=False)

    assert key_payload["api_key"].startswith("tf_")
    assert "api_key" not in json.loads(list_result.stdout)[0]
    assert replacement["id"] != key_payload["id"]
    assert json.loads(revoke_result.stdout)["revoked_at"] is not None
    assert json.loads(maintenance_result.stdout)["restore_drill"]["objectives_met"] is True
    drill = json.loads(drill_result.stdout)
    assert drill["objectives_met"] is True
    assert (tmp_path / drill["report_path"]).is_file()


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
