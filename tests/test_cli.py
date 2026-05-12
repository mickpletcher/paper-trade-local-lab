from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from tradeforge.cli import app


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
    assert payload["metrics"]["number_of_trades"] == 2
    assert payload["metrics"]["ending_equity"] > 0
    assert (tmp_path / payload["report_path"]).exists()

    orders_result = runner.invoke(app, ["show-orders"], env=env, catch_exceptions=False)
    assert orders_result.exit_code == 0
    assert "status=filled" in orders_result.stdout
    assert "status=cancelled" in orders_result.stdout

    assert Path(tmp_path, "data", "tradeforge.db").exists()
