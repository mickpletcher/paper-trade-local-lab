from __future__ import annotations

import math

from tests.conftest import add_bar
from tradeforge.broker_sim.account import SimAccount
from tradeforge.broker_sim.execution import FixedCommissionModel, PerShareCommissionModel, SimBroker
from tradeforge.broker_sim.orders import OrderRequest
from tradeforge.database.models import OrderSide, OrderStatus, OrderType, Position, Trade


def test_market_order_execution_updates_cash_and_position(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 105, 95, 101)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=1, slippage_bps=0)
    order = broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 10), submitted_at=bar.timestamp)

    fills = broker.process_bar(bar)

    position = session.query(Position).one()
    assert order.status == OrderStatus.FILLED.value
    assert fills[0].price == 100
    assert account.cash == 8999
    assert position.quantity == 10
    assert position.average_cost == 100.1


def test_limit_order_execution_respects_candle_range(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 105, 95, 101)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0)
    buy = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.LIMIT, 5, limit_price=96), submitted_at=bar.timestamp
    )
    sell = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.SELL, OrderType.LIMIT, 5, limit_price=106), submitted_at=bar.timestamp
    )

    fills = broker.process_bar(bar)

    assert len([fill for fill in fills if fill.quantity]) == 1
    assert buy.status == OrderStatus.FILLED.value
    assert sell.status == OrderStatus.OPEN.value


def test_sell_order_without_inventory_is_rejected(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 105, 95, 101)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0)
    sell = broker.submit_order(OrderRequest(symbol.id, OrderSide.SELL, OrderType.MARKET, 5), submitted_at=bar.timestamp)

    fills = broker.process_bar(bar)

    assert fills == []
    assert sell.status == OrderStatus.REJECTED.value
    assert account.cash == 10_000


def test_sell_order_larger_than_position_is_rejected(session, symbol) -> None:
    entry_bar = add_bar(session, symbol, 1, 100, 105, 95, 101)
    exit_bar = add_bar(session, symbol, 2, 102, 106, 99, 104)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0)
    broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 3), submitted_at=entry_bar.timestamp)
    broker.process_bar(entry_bar)
    sell = broker.submit_order(OrderRequest(symbol.id, OrderSide.SELL, OrderType.MARKET, 5), submitted_at=exit_bar.timestamp)

    fills = broker.process_bar(exit_bar)

    position = session.query(Position).one()
    assert fills == []
    assert sell.status == OrderStatus.REJECTED.value
    assert position.quantity == 3
    assert account.cash == 9_700


def test_stop_order_triggers_after_stop_is_crossed(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 106, 99, 105)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0)
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.STOP, 5, stop_price=104), submitted_at=bar.timestamp
    )

    fills = broker.process_bar(bar)

    assert len(fills) == 1
    assert fills[0].price == 104
    assert order.triggered_at == bar.timestamp
    assert order.status == OrderStatus.FILLED.value


def test_stop_limit_order_triggers_then_waits_for_limit_fill(session, symbol) -> None:
    trigger_bar = add_bar(session, symbol, 1, 106, 107, 105, 106)
    fill_bar = add_bar(session, symbol, 2, 104, 106, 101, 102)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0)
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.STOP_LIMIT, 4, limit_price=103, stop_price=105),
        submitted_at=trigger_bar.timestamp,
    )

    first_pass = broker.process_bar(trigger_bar)
    second_pass = broker.process_bar(fill_bar)

    assert first_pass == []
    assert order.triggered_at == trigger_bar.timestamp
    assert len(second_pass) == 1
    assert second_pass[0].price == 103
    assert order.status == OrderStatus.FILLED.value


def test_partial_fill_respects_bar_volume_and_carries_remaining_quantity(session, symbol) -> None:
    first_bar = add_bar(session, symbol, 1, 100, 101, 99, 100)
    first_bar.volume = 40
    second_bar = add_bar(session, symbol, 2, 101, 102, 100, 101)
    second_bar.volume = 80
    account = SimAccount.with_starting_cash(20_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0, max_bar_fill_ratio=0.25)
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 20), submitted_at=first_bar.timestamp
    )

    first_fills = broker.process_bar(first_bar)
    second_fills = broker.process_bar(second_bar)

    position = session.query(Position).one()
    assert [fill.quantity for fill in first_fills] == [10]
    assert [fill.quantity for fill in second_fills] == [10]
    assert order.filled_quantity == 20
    assert order.status == OrderStatus.FILLED.value
    assert position.quantity == 20


def test_symbol_specific_slippage_and_per_share_commission_are_applied(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 105, 95, 101)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(
        session,
        account,
        commission_model=PerShareCommissionModel(rate_per_share=0.05, minimum_fee=0.5),
        default_slippage_bps=1,
        symbol_slippage_rules={"AAPL": 25},
    )
    order = broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 10), submitted_at=bar.timestamp)

    fills = broker.process_bar(bar)

    assert fills[0].price == 100.25
    assert fills[0].fee == 0.5
    assert order.status == OrderStatus.FILLED.value


def test_cancel_order_marks_open_order_cancelled(session, symbol) -> None:
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, commission_model=FixedCommissionModel(fee_per_order=0), slippage_bps=0)
    order = broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.LIMIT, 5, limit_price=90))

    cancelled = broker.cancel_order(order.id)

    assert cancelled is True
    assert order.status == OrderStatus.CANCELLED.value


def test_bar_fill_ratio_is_one_aggregate_budget(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 101, 99, 100)
    bar.volume = 100
    account = SimAccount.with_starting_cash(20_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0, max_bar_fill_ratio=0.25)
    broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 25), submitted_at=bar.timestamp)
    broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 25), submitted_at=bar.timestamp)

    fills = broker.process_bar(bar)

    assert sum(fill.quantity for fill in fills) == 25


def test_partially_filled_stop_remains_triggered(session, symbol) -> None:
    trigger_bar = add_bar(session, symbol, 1, 100, 105, 99, 104)
    trigger_bar.volume = 20
    continuation_bar = add_bar(session, symbol, 2, 101, 103, 99, 101)
    continuation_bar.volume = 20
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0, max_bar_fill_ratio=0.25)
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.STOP, 10, stop_price=104), submitted_at=trigger_bar.timestamp
    )

    first_fills = broker.process_bar(trigger_bar)
    second_fills = broker.process_bar(continuation_bar)

    assert [fill.quantity for fill in first_fills] == [5]
    assert [fill.quantity for fill in second_fills] == [5]
    assert second_fills[0].price == 101
    assert order.triggered_at == trigger_bar.timestamp
    assert order.status == OrderStatus.FILLED.value


def test_limit_order_never_fills_above_buy_limit(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 101, 102, 99, 100)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=10, max_bar_fill_ratio=1)
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.LIMIT, 1, limit_price=100), submitted_at=bar.timestamp
    )

    fills = broker.process_bar(bar)

    assert fills[0].price == 100
    assert fills[0].price <= order.limit_price


def test_marketable_limit_receives_open_price_improvement(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 99, 101, 98, 100)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0, max_bar_fill_ratio=1)
    broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.LIMIT, 1, limit_price=100), submitted_at=bar.timestamp
    )

    fills = broker.process_bar(bar)

    assert fills[0].price == 99


def test_fixed_commission_is_charged_once_across_partial_fills(session, symbol) -> None:
    first_bar = add_bar(session, symbol, 1, 100, 101, 99, 100)
    first_bar.volume = 4
    second_bar = add_bar(session, symbol, 2, 100, 101, 99, 100)
    second_bar.volume = 4
    account = SimAccount.with_starting_cash(1_000)
    broker = SimBroker(session, account, fee_per_order=1, slippage_bps=0, max_bar_fill_ratio=0.5)
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 4), submitted_at=first_bar.timestamp
    )

    fills = broker.process_bar(first_bar) + broker.process_bar(second_bar)

    assert [fill.fee for fill in fills] == [1, 0]
    assert order.commission_paid == 1
    assert account.cash == 599


def test_per_share_minimum_is_applied_once_per_order(session, symbol) -> None:
    first_bar = add_bar(session, symbol, 1, 100, 101, 99, 100)
    first_bar.volume = 10
    second_bar = add_bar(session, symbol, 2, 100, 101, 99, 100)
    second_bar.volume = 10
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(
        session,
        account,
        commission_model=PerShareCommissionModel(rate_per_share=0.01, minimum_fee=0.5),
        slippage_bps=0,
        max_bar_fill_ratio=0.5,
    )
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 10), submitted_at=first_bar.timestamp
    )

    fills = broker.process_bar(first_bar) + broker.process_bar(second_bar)

    assert [fill.fee for fill in fills] == [0.5, 0]
    assert order.commission_paid == 0.5


def test_round_trip_pnl_and_trade_history_reconcile(session, symbol) -> None:
    first_bar = add_bar(session, symbol, 1, 100, 101, 99, 100)
    first_bar.volume = 4
    second_bar = add_bar(session, symbol, 2, 100, 101, 99, 100)
    second_bar.volume = 4
    exit_bar = add_bar(session, symbol, 3, 110, 111, 109, 110)
    exit_bar.volume = 4
    final_bar = add_bar(session, symbol, 4, 112, 113, 111, 112)
    final_bar.volume = 4
    account = SimAccount.with_starting_cash(1_000)
    broker = SimBroker(session, account, fee_per_order=1, slippage_bps=0, max_bar_fill_ratio=0.5)
    broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 4), submitted_at=first_bar.timestamp)
    broker.process_bar(first_bar)
    broker.process_bar(second_bar)
    broker.submit_order(OrderRequest(symbol.id, OrderSide.SELL, OrderType.MARKET, 4), submitted_at=exit_bar.timestamp)

    broker.process_bar(exit_bar)
    broker.process_bar(final_bar)

    position = session.query(Position).one()
    trades = session.query(Trade).all()
    assert math.isclose(position.realized_pnl, account.cash - account.starting_cash)
    assert len(trades) == 1
    assert trades[0].closed_at == final_bar.timestamp.replace(tzinfo=None)
    assert trades[0].exit_price == 111
    assert math.isclose(trades[0].realized_pnl, position.realized_pnl)


def test_future_order_does_not_fill_on_earlier_bar(session, symbol) -> None:
    earlier_bar = add_bar(session, symbol, 1, 100, 101, 99, 100)
    submitted_bar = add_bar(session, symbol, 2, 101, 102, 100, 101)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0, max_bar_fill_ratio=1)
    order = broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 1), submitted_at=submitted_bar.timestamp
    )

    assert broker.process_bar(earlier_bar) == []
    assert order.status == OrderStatus.OPEN.value
    assert len(broker.process_bar(submitted_bar)) == 1


def test_broker_only_processes_its_strategy_run_scope(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 101, 99, 100)
    account = SimAccount.with_starting_cash(10_000)
    manual_broker = SimBroker(session, account, fee_per_order=0, slippage_bps=0, max_bar_fill_ratio=1)
    manual_broker.submit_order(
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 1), submitted_at=bar.timestamp
    )
    other_broker = SimBroker(
        session,
        SimAccount.with_starting_cash(10_000),
        fee_per_order=0,
        slippage_bps=0,
        max_bar_fill_ratio=1,
        strategy_run_id="other-run",
    )

    assert other_broker.process_bar(bar) == []
    assert len(manual_broker.process_bar(bar)) == 1


def test_order_validation_rejects_nonfinite_values(symbol) -> None:
    invalid_requests = [
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, float("nan")),
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.LIMIT, 1, limit_price=float("inf")),
        OrderRequest(symbol.id, OrderSide.BUY, OrderType.STOP, 1, stop_price=-1),
    ]

    for request in invalid_requests:
        try:
            request.validate()
        except ValueError:
            continue
        raise AssertionError("Invalid order request was accepted")
