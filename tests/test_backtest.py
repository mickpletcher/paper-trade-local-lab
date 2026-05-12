from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from tradeforge.backtesting.engine import BacktestEngine
from tradeforge.database.models import AccountSnapshot, StrategyRun
from tradeforge.strategies.base import StrategyContext
from tradeforge.strategies.moving_average_cross import MovingAverageCrossStrategy

from tests.conftest import add_bar


def test_moving_average_strategy_signal_generation(session, symbol) -> None:
    closes = [10, 9, 8, 12]
    bars = [add_bar(session, symbol, index + 1, close, close + 1, close - 1, close) for index, close in enumerate(closes)]
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=3, order_size=7)

    signal = strategy.on_bar(bars[-1], StrategyContext(bars=bars, has_position=False))

    assert signal is not None
    assert signal.quantity == 7
    assert signal.side.value == "buy"


def test_backtest_run_completion(session, symbol, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    closes = [10, 9, 8, 12, 13, 8, 7, 11]
    for index, close in enumerate(closes):
        add_bar(session, symbol, index + 1, close, close + 1, close - 1, close)
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=3, order_size=2)
    engine = BacktestEngine(
        session,
        strategy,
        "AAPL",
        datetime(2023, 1, 1, tzinfo=timezone.utc),
        datetime(2023, 1, 8, tzinfo=timezone.utc),
        starting_cash=10_000,
    )

    result = engine.run()

    assert result["strategy_run_id"]
    assert result["metrics"]["ending_equity"] > 0
    assert session.scalar(select(StrategyRun)) is not None
    assert len(session.scalars(select(AccountSnapshot)).all()) == len(closes)
    assert (tmp_path / result["report_path"]).exists()
