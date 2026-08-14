from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from tradeforge.backtesting.engine import BacktestEngine, _build_commission_model, _parse_symbol_slippage_rules
from tradeforge.database.models import AccountSnapshot, Fill, Order, OrderSide, OrderStatus, OrderType, StrategyRun
from tradeforge.strategies.base import BaseStrategy, StrategyContext, StrategySignal
from tradeforge.strategies.moving_average_cross import MovingAverageCrossStrategy

from tests.conftest import add_bar


def test_moving_average_strategy_signal_generation(session, symbol) -> None:
    closes = [10, 9, 8, 12]
    bars = [
        add_bar(session, symbol, index + 1, close, close + 1, close - 1, close) for index, close in enumerate(closes)
    ]
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
    run = session.scalar(select(StrategyRun))
    assert run is not None
    execution_parameters = json.loads(run.parameters_json)["execution"]
    assert execution_parameters["commission"] == {"model": "fixed", "fee_per_order": 1.0}
    assert execution_parameters["max_bar_fill_ratio"] == 0.25
    assert len(session.scalars(select(AccountSnapshot)).all()) == len(closes)
    assert (tmp_path / result["report_path"]).exists()


class LastBarSignalStrategy(BaseStrategy):
    name = "last-bar-signal"

    def on_bar(self, bar, context: StrategyContext) -> StrategySignal | None:
        if len(context.bars) == 2:
            return StrategySignal(side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=1)
        return None


def test_last_bar_signal_is_not_filled_on_same_bar(session, symbol, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    add_bar(session, symbol, 1, 10, 11, 9, 10)
    add_bar(session, symbol, 2, 11, 12, 10, 11)
    engine = BacktestEngine(
        session,
        LastBarSignalStrategy(),
        "AAPL",
        datetime(2023, 1, 1, tzinfo=timezone.utc),
        datetime(2023, 1, 2, tzinfo=timezone.utc),
        starting_cash=10_000,
    )

    result = engine.run()

    order = session.scalar(select(Order))
    fills = session.scalars(select(Fill)).all()
    assert result["metrics"]["number_of_trades"] == 0
    assert order is not None
    assert order.status == OrderStatus.CANCELLED.value
    assert fills == []


def test_unknown_commission_model_is_rejected() -> None:
    settings = SimpleNamespace(
        commission_model="unknown",
        commission_per_share=0.0,
        commission_minimum=0.0,
        fee_per_order=1.0,
    )

    with pytest.raises(ValueError, match="TRADEFORGE_COMMISSION_MODEL"):
        _build_commission_model(settings)


@pytest.mark.parametrize("raw_rules", ['{"AAPL": -1}', '{"AAPL": "not-a-number"}', '{"": 1}'])
def test_invalid_symbol_slippage_rules_are_rejected(raw_rules) -> None:
    with pytest.raises(ValueError):
        _parse_symbol_slippage_rules(raw_rules)
