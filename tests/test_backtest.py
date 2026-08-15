from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from tradeforge.backtesting.engine import BacktestEngine, _build_commission_model, _parse_symbol_slippage_rules
from tradeforge.backtesting.metrics import calculate_metrics
from tradeforge.database.models import (
    AccountSnapshot,
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    Position,
    StrategyRun,
    Trade,
)
from tradeforge.strategies.base import BaseStrategy, StrategyContext, StrategySignal
from tradeforge.strategies.moving_average_cross import MovingAverageCrossStrategy

from tests.conftest import add_bar


def test_moving_average_strategy_signal_generation(session, symbol) -> None:
    closes = [10, 9, 8, 12]
    bars = [
        add_bar(session, symbol, index + 1, close, close + 1, close - 1, close) for index, close in enumerate(closes)
    ]
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=3, order_size=7)

    signal = strategy.on_bar(bars[-1], StrategyContext(bars=bars, position_quantity=0))

    assert signal is not None
    assert signal.quantity == 7
    assert signal.side.value == "buy"


def test_moving_average_strategy_caps_exit_to_position_quantity(session, symbol) -> None:
    closes = [1, 3, 1]
    bars = [
        add_bar(session, symbol, index + 1, close, close + 1, close - 1, close) for index, close in enumerate(closes)
    ]
    strategy = MovingAverageCrossStrategy(short_window=1, long_window=2, order_size=10)

    signal = strategy.on_bar(bars[-1], StrategyContext(bars=bars, position_quantity=2.5))

    assert signal is not None
    assert signal.quantity == 2.5
    assert signal.side is OrderSide.SELL


@pytest.mark.parametrize(
    ("short_window", "long_window", "order_size"),
    [(0, 2, 1), (2, 2, 1), (3, 2, 1), (1, 2, 0), (1, 2, float("inf"))],
)
def test_moving_average_strategy_rejects_invalid_parameters(short_window, long_window, order_size) -> None:
    with pytest.raises(ValueError):
        MovingAverageCrossStrategy(short_window=short_window, long_window=long_window, order_size=order_size)


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
    assert execution_parameters["quantity_increment"] == 1.0
    assert len(session.scalars(select(AccountSnapshot)).all()) == len(closes)
    assert (tmp_path / result["report_path"]).exists()


def test_calculate_metrics_reports_risk_trade_and_benchmark_statistics() -> None:
    timestamps = [datetime(year, 1, 1, tzinfo=timezone.utc) for year in range(2021, 2025)]
    snapshots = [
        AccountSnapshot(timestamp=timestamp, cash=cash, equity=equity)
        for timestamp, cash, equity in zip(
            timestamps,
            (100.0, 90.0, 99.0, 80.0),
            (100.0, 110.0, 99.0, 120.0),
            strict=True,
        )
    ]
    trades = [
        Trade(
            symbol_id="symbol-1",
            opened_at=timestamps[0],
            closed_at=timestamps[1],
            quantity=1,
            entry_price=100,
            realized_pnl=20,
        ),
        Trade(
            symbol_id="symbol-1",
            opened_at=timestamps[1],
            closed_at=timestamps[2],
            quantity=1,
            entry_price=100,
            realized_pnl=-5,
        ),
        Trade(
            symbol_id="symbol-1",
            opened_at=timestamps[2],
            closed_at=timestamps[3],
            quantity=1,
            entry_price=100,
            realized_pnl=10,
        ),
    ]
    position = Position(quantity=0, average_cost=0, realized_pnl=25)

    metrics = calculate_metrics(100, 120, [], trades, position, snapshots, 100, 115)

    assert metrics["total_return"] == 0.2
    assert metrics["cagr"] == pytest.approx(0.0627, abs=0.0001)
    assert metrics["volatility"] == pytest.approx(0.12914)
    assert metrics["sharpe_ratio"] == pytest.approx(0.547899)
    assert metrics["sortino_ratio"] == pytest.approx(1.225102)
    assert metrics["profit_factor"] == 6.0
    assert metrics["average_win"] == 15.0
    assert metrics["average_loss"] == -5.0
    assert metrics["exposure"] == 0.5
    assert metrics["buy_and_hold_return"] == 0.15
    assert metrics["max_drawdown"] == -0.1


def test_calculate_metrics_handles_empty_histories() -> None:
    metrics = calculate_metrics(100, 100, [], [], None, [], 0, 0)

    assert metrics["cagr"] is None
    assert metrics["volatility"] == 0
    assert metrics["sharpe_ratio"] == 0
    assert metrics["sortino_ratio"] == 0
    assert metrics["profit_factor"] is None
    assert metrics["exposure"] == 0
    assert metrics["buy_and_hold_return"] == 0


def test_calculate_metrics_marks_unbounded_ratios_and_cagr_undefined() -> None:
    started_at = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
    snapshots = [
        AccountSnapshot(timestamp=started_at, cash=100, equity=100),
        AccountSnapshot(timestamp=started_at.replace(minute=1), cash=101, equity=101),
    ]

    metrics = calculate_metrics(100, 101, [], [], None, snapshots, 100, 101)

    assert metrics["cagr"] is None
    assert metrics["volatility"] == 0
    assert metrics["sharpe_ratio"] is None
    assert metrics["sortino_ratio"] is None


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


def test_backtest_cancels_partially_filled_entry_before_exit(session, symbol, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    closes = [3, 1, 3, 1, 1]
    for index, close in enumerate(closes):
        bar = add_bar(session, symbol, index + 1, close, close + 1, max(close - 1, 0.1), close)
        if index >= 3:
            bar.volume = 8
    engine = BacktestEngine(
        session,
        MovingAverageCrossStrategy(short_window=1, long_window=2, order_size=10),
        "AAPL",
        datetime(2023, 1, 1, tzinfo=timezone.utc),
        datetime(2023, 1, 5, tzinfo=timezone.utc),
        starting_cash=10_000,
    )

    engine.run()

    orders = session.scalars(select(Order).order_by(Order.submitted_at.asc())).all()
    position = session.scalar(select(Position))
    assert position is not None
    assert position.quantity == 0
    assert [(order.side, order.filled_quantity, order.status) for order in orders] == [
        (OrderSide.BUY.value, 2, OrderStatus.CANCELLED.value),
        (OrderSide.SELL.value, 2, OrderStatus.FILLED.value),
    ]


def test_backtest_cancels_unfilled_entry_when_signal_reverses(session, symbol, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    closes = [3, 1, 3, 1, 1]
    for index, close in enumerate(closes):
        bar = add_bar(session, symbol, index + 1, close, close + 1, max(close - 1, 0.1), close)
        if index == 3:
            bar.volume = 0
    engine = BacktestEngine(
        session,
        MovingAverageCrossStrategy(short_window=1, long_window=2, order_size=10),
        "AAPL",
        datetime(2023, 1, 1, tzinfo=timezone.utc),
        datetime(2023, 1, 5, tzinfo=timezone.utc),
        starting_cash=10_000,
    )

    engine.run()

    order = session.scalar(select(Order))
    position = session.scalar(select(Position))
    assert order is not None
    assert position is not None
    assert order.filled_quantity == 0
    assert order.status == OrderStatus.CANCELLED.value
    assert position.quantity == 0


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
