from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from tradeforge.broker_sim.account import SimAccount
from tradeforge.broker_sim.orders import OrderRequest
from tradeforge.broker_sim.portfolio import apply_fill_to_position, get_or_create_position
from tradeforge.database.models import Fill, Order, OrderSide, OrderStatus, OrderType, PriceBar, Trade


class SimBroker:
    def __init__(self, session: Session, account: SimAccount, fee_per_order: float = 1.0, slippage_bps: float = 1.0):
        self.session = session
        self.account = account
        self.fee_per_order = fee_per_order
        self.slippage_bps = slippage_bps

    def submit_order(self, request: OrderRequest, submitted_at: datetime | None = None) -> Order:
        request.validate()
        order = Order(
            strategy_run_id=request.strategy_run_id,
            symbol_id=request.symbol_id,
            side=request.side.value,
            order_type=request.order_type.value,
            quantity=request.quantity,
            limit_price=request.limit_price,
            submitted_at=submitted_at or datetime.utcnow(),
        )
        self.session.add(order)
        self.session.flush()
        return order

    def process_bar(self, bar: PriceBar) -> list[Fill]:
        fills: list[Fill] = []
        open_orders = (
            self.session.query(Order)
            .filter(Order.symbol_id == bar.symbol_id, Order.status == OrderStatus.OPEN.value)
            .order_by(Order.submitted_at.asc())
            .all()
        )
        for order in open_orders:
            fill_price = self._match_price(order, bar)
            if fill_price is not None:
                fills.append(self._fill_order(order, bar, fill_price))
        self.session.flush()
        return fills

    def _match_price(self, order: Order, bar: PriceBar) -> float | None:
        side = OrderSide(order.side)
        order_type = OrderType(order.order_type)
        if order_type is OrderType.MARKET:
            return self._with_slippage(bar.open, side)
        if side is OrderSide.BUY and bar.low <= float(order.limit_price):
            return self._with_slippage(float(order.limit_price), side)
        if side is OrderSide.SELL and bar.high >= float(order.limit_price):
            return self._with_slippage(float(order.limit_price), side)
        return None

    def _with_slippage(self, price: float, side: OrderSide) -> float:
        adjustment = price * (self.slippage_bps / 10_000)
        return price + adjustment if side is OrderSide.BUY else price - adjustment

    def _fill_order(self, order: Order, bar: PriceBar, price: float) -> Fill:
        side = OrderSide(order.side)
        fee = self.fee_per_order
        gross = price * order.quantity
        if side is OrderSide.BUY:
            total_cost = gross + fee
            if total_cost > self.account.cash:
                order.status = OrderStatus.REJECTED.value
                return Fill(
                    order_id=order.id,
                    strategy_run_id=order.strategy_run_id,
                    symbol_id=order.symbol_id,
                    timestamp=bar.timestamp,
                    side=side.value,
                    quantity=0,
                    price=price,
                    fee=0,
                    slippage=0,
                )
            self.account.cash -= total_cost
        else:
            self.account.cash += gross - fee

        position = get_or_create_position(self.session, order.symbol_id, order.strategy_run_id)
        update = apply_fill_to_position(position, side, order.quantity, price, fee)
        fill = Fill(
            order_id=order.id,
            strategy_run_id=order.strategy_run_id,
            symbol_id=order.symbol_id,
            timestamp=bar.timestamp,
            side=side.value,
            quantity=order.quantity,
            price=price,
            fee=fee,
            slippage=abs(price - (order.limit_price or bar.open)),
        )
        self.session.add(fill)

        if side is OrderSide.BUY:
            self.session.add(
                Trade(
                    strategy_run_id=order.strategy_run_id,
                    symbol_id=order.symbol_id,
                    opened_at=bar.timestamp,
                    quantity=order.quantity,
                    entry_price=price,
                )
            )
        elif update.closed_quantity:
            trade = (
                self.session.query(Trade)
                .filter(Trade.strategy_run_id == order.strategy_run_id, Trade.symbol_id == order.symbol_id, Trade.closed_at.is_(None))
                .order_by(Trade.opened_at.asc())
                .first()
            )
            if trade is not None:
                trade.closed_at = bar.timestamp
                trade.exit_price = price
                trade.realized_pnl = update.realized_pnl_delta

        order.status = OrderStatus.FILLED.value
        order.filled_at = bar.timestamp
        return fill
