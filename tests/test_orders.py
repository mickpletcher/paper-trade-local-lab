from __future__ import annotations

from tradeforge.broker_sim.account import SimAccount
from tradeforge.broker_sim.execution import SimBroker
from tradeforge.broker_sim.orders import OrderRequest
from tradeforge.database.models import OrderSide, OrderStatus, OrderType, Position

from tests.conftest import add_bar


def test_market_order_execution_updates_cash_and_position(session, symbol) -> None:
    bar = add_bar(session, symbol, 1, 100, 105, 95, 101)
    account = SimAccount.with_starting_cash(10_000)
    broker = SimBroker(session, account, fee_per_order=1, slippage_bps=0)
    order = broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.MARKET, 10))
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
    buy = broker.submit_order(OrderRequest(symbol.id, OrderSide.BUY, OrderType.LIMIT, 5, limit_price=96))
    sell = broker.submit_order(OrderRequest(symbol.id, OrderSide.SELL, OrderType.LIMIT, 5, limit_price=106))

    fills = broker.process_bar(bar)

    assert len([fill for fill in fills if fill.quantity]) == 1
    assert buy.status == OrderStatus.FILLED.value
    assert sell.status == OrderStatus.OPEN.value
