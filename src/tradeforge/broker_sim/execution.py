from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import ROUND_FLOOR, Decimal
from math import floor, isfinite

from sqlalchemy.orm import Session

from tradeforge.broker_sim.account import SimAccount
from tradeforge.broker_sim.orders import OrderRequest
from tradeforge.broker_sim.portfolio import PositionUpdate, apply_fill_to_position, get_or_create_position
from tradeforge.broker_sim.risk import RiskEngine, RiskLimitError
from tradeforge.database.models import (
    ExecutionAuditEvent,
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    PriceBar,
    Trade,
)


class CommissionModel:
    def total_fee(self, quantity: float, price: float) -> float:
        raise NotImplementedError


@dataclass(frozen=True)
class FixedCommissionModel(CommissionModel):
    fee_per_order: float = 1.0

    def __post_init__(self) -> None:
        _validate_nonnegative_finite("fee_per_order", self.fee_per_order)

    def total_fee(self, quantity: float, price: float) -> float:
        return self.fee_per_order if quantity > 0 else 0.0


@dataclass(frozen=True)
class PerShareCommissionModel(CommissionModel):
    rate_per_share: float
    minimum_fee: float = 0.0

    def __post_init__(self) -> None:
        _validate_nonnegative_finite("rate_per_share", self.rate_per_share)
        _validate_nonnegative_finite("minimum_fee", self.minimum_fee)

    def total_fee(self, quantity: float, price: float) -> float:
        return max(quantity * self.rate_per_share, self.minimum_fee) if quantity > 0 else 0.0


@dataclass(frozen=True)
class MatchedExecution:
    reference_price: float
    execution_price: float
    fillable_quantity: float


class SimBroker:
    def __init__(
        self,
        session: Session,
        account: SimAccount,
        fee_per_order: float = 1.0,
        slippage_bps: float = 1.0,
        commission_model: CommissionModel | None = None,
        default_slippage_bps: float | None = None,
        symbol_slippage_rules: dict[str, float] | None = None,
        max_bar_fill_ratio: float = 0.25,
        quantity_increment: float = 1.0,
        strategy_run_id: str | None = None,
        risk_engine: RiskEngine | None = None,
    ):
        resolved_slippage = slippage_bps if default_slippage_bps is None else default_slippage_bps
        _validate_slippage_bps("default_slippage_bps", resolved_slippage)
        if not isfinite(max_bar_fill_ratio) or not 0 <= max_bar_fill_ratio <= 1:
            raise ValueError("max_bar_fill_ratio must be between 0 and 1")
        if not isfinite(quantity_increment) or quantity_increment <= 0:
            raise ValueError("quantity_increment must be a positive finite number")

        self.session = session
        self.account = account
        self.commission_model = commission_model or FixedCommissionModel(fee_per_order=fee_per_order)
        self.default_slippage_bps = resolved_slippage
        self.symbol_slippage_rules = {key.upper(): value for key, value in (symbol_slippage_rules or {}).items()}
        for ticker, bps in self.symbol_slippage_rules.items():
            if not ticker.strip():
                raise ValueError("Symbol slippage rule tickers cannot be empty")
            _validate_slippage_bps(f"symbol_slippage_rules[{ticker}]", bps)
        self.max_bar_fill_ratio = max_bar_fill_ratio
        self.quantity_increment = quantity_increment
        self.strategy_run_id = strategy_run_id
        self.risk_engine = risk_engine

    def submit_order(self, request: OrderRequest, submitted_at: datetime | None = None) -> Order:
        request.validate()
        if abs(self._quantize_quantity(request.quantity) - request.quantity) > 1e-9:
            raise ValueError(f"Order quantity must be a multiple of {self.quantity_increment:g}")
        if request.strategy_run_id != self.strategy_run_id:
            raise ValueError("Order strategy run does not match the broker execution scope")
        reference_price = request.limit_price or request.stop_price
        if reference_price is None and self.risk_engine is not None:
            reference_price = self.risk_engine.mark_prices.get(request.symbol_id)
        if self.risk_engine is not None:
            try:
                self.risk_engine.validate_order(request, reference_price)
            except RiskLimitError as exc:
                self._audit(
                    "rejected",
                    submitted_at,
                    reason=str(exc),
                    symbol_id=request.symbol_id,
                    payload={"side": request.side.value, "quantity": request.quantity},
                )
                self.session.flush()
                raise
        order = Order(
            strategy_run_id=request.strategy_run_id,
            symbol_id=request.symbol_id,
            side=request.side.value,
            order_type=request.order_type.value,
            quantity=request.quantity,
            limit_price=request.limit_price,
            stop_price=request.stop_price,
            submitted_at=submitted_at or datetime.now(timezone.utc),
        )
        self.session.add(order)
        self.session.flush()
        return order

    def process_bar(self, bar: PriceBar) -> list[Fill]:
        if self.risk_engine is not None:
            self.risk_engine.update_mark(bar.symbol_id, bar.close)
        fills: list[Fill] = []
        available_volume = float(floor(max(float(bar.volume), 0.0) * self.max_bar_fill_ratio))
        open_orders = (
            self.session.query(Order)
            .filter(
                Order.symbol_id == bar.symbol_id,
                Order.strategy_run_id == self.strategy_run_id,
                Order.status.in_([OrderStatus.OPEN.value, OrderStatus.PARTIALLY_FILLED.value]),
                Order.submitted_at <= bar.timestamp,
            )
            .order_by(Order.submitted_at.asc(), Order.id.asc())
            .all()
        )
        for order in open_orders:
            match = self._match_execution(order, bar, available_volume)
            if match is None:
                continue
            fill = self._fill_order(order, bar, match)
            if fill is not None:
                fills.append(fill)
                available_volume = max(0.0, available_volume - fill.quantity)
        self.session.flush()
        return fills

    def cancel_order(self, order_id: str) -> bool:
        order = self.session.get(Order, order_id)
        if (
            order is None
            or order.strategy_run_id != self.strategy_run_id
            or order.status not in {OrderStatus.OPEN.value, OrderStatus.PARTIALLY_FILLED.value}
        ):
            return False
        order.status = OrderStatus.CANCELLED.value
        self._audit("cancelled", reason="cancel_order", order=order)
        self.session.flush()
        return True

    def cancel_open_orders(self, symbol_id: str | None = None, side: OrderSide | None = None) -> int:
        query = self.session.query(Order).filter(
            Order.strategy_run_id == self.strategy_run_id,
            Order.status.in_([OrderStatus.OPEN.value, OrderStatus.PARTIALLY_FILLED.value]),
        )
        if symbol_id is not None:
            query = query.filter(Order.symbol_id == symbol_id)
        if side is not None:
            query = query.filter(Order.side == side.value)
        orders = query.all()
        for order in orders:
            order.status = OrderStatus.CANCELLED.value
            self._audit("cancelled", reason="cancel_open_orders", order=order)
        self.session.flush()
        return len(orders)

    def get_pending_quantities(self, symbol_id: str) -> dict[OrderSide, float]:
        orders = (
            self.session.query(Order)
            .filter(
                Order.symbol_id == symbol_id,
                Order.strategy_run_id == self.strategy_run_id,
                Order.status.in_([OrderStatus.OPEN.value, OrderStatus.PARTIALLY_FILLED.value]),
            )
            .all()
        )
        quantities = {OrderSide.BUY: 0.0, OrderSide.SELL: 0.0}
        for order in orders:
            quantities[OrderSide(order.side)] += max(order.quantity - order.filled_quantity, 0.0)
        return quantities

    def _match_execution(self, order: Order, bar: PriceBar, available_volume: float) -> MatchedExecution | None:
        remaining_quantity = max(order.quantity - order.filled_quantity, 0.0)
        if remaining_quantity <= 0:
            order.status = OrderStatus.FILLED.value
            return None

        side = OrderSide(order.side)
        order_type = OrderType(order.order_type)
        reference_price: float | None

        if order_type is OrderType.STOP:
            stop_price = _required_order_price(order.stop_price, "stop")
            if order.triggered_at is None:
                if not self._stop_triggered(side, stop_price, bar):
                    return None
                order.triggered_at = bar.timestamp
                self._audit("triggered", bar.timestamp, order=order)
                reference_price = self._stop_reference_price(side, stop_price, bar)
            else:
                reference_price = bar.open
        elif order_type is OrderType.STOP_LIMIT:
            stop_price = _required_order_price(order.stop_price, "stop")
            limit_price = _required_order_price(order.limit_price, "limit")
            if order.triggered_at is None:
                if not self._stop_triggered(side, stop_price, bar):
                    return None
                order.triggered_at = bar.timestamp
                self._audit("triggered", bar.timestamp, order=order)
            reference_price = self._limit_reference_price(side, limit_price, bar)
        elif order_type is OrderType.MARKET:
            reference_price = bar.open
        else:
            reference_price = self._limit_reference_price(side, _required_order_price(order.limit_price, "limit"), bar)

        if reference_price is None:
            return None

        execution_price = self._execution_price(order, side, reference_price)
        fillable_quantity = self._resolve_fill_quantity(order, execution_price, remaining_quantity, available_volume)
        if fillable_quantity <= 0:
            return None

        return MatchedExecution(
            reference_price=reference_price,
            execution_price=execution_price,
            fillable_quantity=fillable_quantity,
        )

    def _resolve_fill_quantity(
        self,
        order: Order,
        execution_price: float,
        remaining_quantity: float,
        available_volume: float,
    ) -> float:
        if available_volume <= 0:
            return 0.0
        fillable_quantity = self._quantize_quantity(min(remaining_quantity, available_volume))
        if OrderSide(order.side) is OrderSide.BUY:
            fillable_quantity = self._cap_buy_quantity_to_cash(order, fillable_quantity, execution_price)
        return fillable_quantity

    def _cap_buy_quantity_to_cash(self, order: Order, quantity: float, execution_price: float) -> float:
        if quantity <= 0:
            return 0.0
        if self._buy_cost(order, quantity, execution_price) <= self.account.cash:
            return quantity

        low = 0.0
        high = quantity
        for _ in range(64):
            midpoint = (low + high) / 2
            if self._buy_cost(order, midpoint, execution_price) <= self.account.cash:
                low = midpoint
            else:
                high = midpoint
        capped_quantity = self._quantize_quantity(low)
        if capped_quantity <= 0:
            return 0.0
        if self._buy_cost(order, capped_quantity, execution_price) > self.account.cash + 1e-9:
            capped_quantity = self._quantize_quantity(capped_quantity - self.quantity_increment)
        return max(capped_quantity, 0.0)

    def _quantize_quantity(self, quantity: float) -> float:
        decimal_quantity = Decimal(str(max(quantity, 0.0)))
        decimal_increment = Decimal(str(self.quantity_increment))
        steps = (decimal_quantity / decimal_increment).to_integral_value(rounding=ROUND_FLOOR)
        return float(steps * decimal_increment)

    def _buy_cost(self, order: Order, quantity: float, execution_price: float) -> float:
        return quantity * execution_price + self._commission_for_fill(order, quantity, execution_price)

    def _commission_for_fill(self, order: Order, quantity: float, price: float) -> float:
        cumulative_quantity = order.filled_quantity + quantity
        cumulative_fee = self.commission_model.total_fee(cumulative_quantity, price)
        return max(cumulative_fee - order.commission_paid, 0.0)

    def _limit_reference_price(self, side: OrderSide, limit_price: float, bar: PriceBar) -> float | None:
        if side is OrderSide.BUY:
            if bar.open <= limit_price:
                return bar.open
            return limit_price if bar.low <= limit_price else None
        if bar.open >= limit_price:
            return bar.open
        return limit_price if bar.high >= limit_price else None

    def _stop_triggered(self, side: OrderSide, stop_price: float, bar: PriceBar) -> bool:
        if side is OrderSide.BUY:
            return bar.high >= stop_price
        return bar.low <= stop_price

    def _stop_reference_price(self, side: OrderSide, stop_price: float, bar: PriceBar) -> float:
        if side is OrderSide.BUY:
            return max(bar.open, stop_price)
        return min(bar.open, stop_price)

    def _execution_price(self, order: Order, side: OrderSide, reference_price: float) -> float:
        slipped_price = self._with_slippage(reference_price, side, order.symbol.ticker)
        if OrderType(order.order_type) in {OrderType.LIMIT, OrderType.STOP_LIMIT}:
            limit_price = _required_order_price(order.limit_price, "limit")
            return min(slipped_price, limit_price) if side is OrderSide.BUY else max(slipped_price, limit_price)
        return slipped_price

    def _with_slippage(self, price: float, side: OrderSide, ticker: str) -> float:
        bps = self.symbol_slippage_rules.get(ticker.upper(), self.default_slippage_bps)
        adjustment = price * (bps / 10_000)
        return price + adjustment if side is OrderSide.BUY else price - adjustment

    def _fill_order(self, order: Order, bar: PriceBar, match: MatchedExecution) -> Fill | None:
        side = OrderSide(order.side)
        quantity = match.fillable_quantity
        fee = self._commission_for_fill(order, quantity, match.execution_price)
        gross = match.execution_price * quantity
        position = get_or_create_position(self.session, order.symbol_id, order.strategy_run_id)

        if self.risk_engine is not None:
            try:
                self.risk_engine.validate_fill(order, quantity, match.execution_price)
            except RiskLimitError as exc:
                order.status = OrderStatus.REJECTED.value
                self._audit("rejected", bar.timestamp, reason=str(exc), order=order)
                return None

        if side is OrderSide.BUY:
            total_cost = gross + fee
            if total_cost > self.account.cash + 1e-9:
                order.status = (
                    OrderStatus.PARTIALLY_FILLED.value if order.filled_quantity > 0 else OrderStatus.REJECTED.value
                )
                self._audit("rejected", bar.timestamp, reason="insufficient_cash", order=order)
                return None
            self.account.cash -= total_cost
        else:
            remaining_position = max(position.quantity, 0.0)
            remaining_order_quantity = max(order.quantity - order.filled_quantity, 0.0)
            if remaining_order_quantity > remaining_position + 1e-9:
                order.status = (
                    OrderStatus.PARTIALLY_FILLED.value if order.filled_quantity > 0 else OrderStatus.REJECTED.value
                )
                self._audit("rejected", bar.timestamp, reason="oversized_sell", order=order)
                return None
            quantity = min(quantity, remaining_position)
            if quantity <= 0:
                order.status = OrderStatus.REJECTED.value
                self._audit("rejected", bar.timestamp, reason="no_position", order=order)
                return None
            fee = self._commission_for_fill(order, quantity, match.execution_price)
            gross = match.execution_price * quantity
            self.account.cash += gross - fee

        update = apply_fill_to_position(position, side, quantity, match.execution_price, fee)
        fill = Fill(
            order_id=order.id,
            strategy_run_id=order.strategy_run_id,
            symbol_id=order.symbol_id,
            timestamp=bar.timestamp,
            side=side.value,
            quantity=quantity,
            price=match.execution_price,
            fee=fee,
            slippage=abs(match.execution_price - match.reference_price),
        )
        self.session.add(fill)
        self._record_trade_fill(order, bar, side, quantity, match.execution_price, fee, update, position.quantity)

        order.filled_quantity += quantity
        order.commission_paid += fee
        remaining_quantity = max(order.quantity - order.filled_quantity, 0.0)
        if remaining_quantity <= 1e-9:
            order.filled_quantity = order.quantity
            order.status = OrderStatus.FILLED.value
            order.filled_at = bar.timestamp
        else:
            order.status = OrderStatus.PARTIALLY_FILLED.value
        self._audit("remaining_quantity_changed", bar.timestamp, remaining_quantity=remaining_quantity, order=order)
        return fill

    def _audit(
        self,
        event_type: str,
        timestamp: datetime | None = None,
        *,
        reason: str | None = None,
        remaining_quantity: float | None = None,
        order: Order | None = None,
        symbol_id: str | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        self.session.add(
            ExecutionAuditEvent(
                order_id=None if order is None else order.id,
                strategy_run_id=self.strategy_run_id if order is None else order.strategy_run_id,
                symbol_id=symbol_id if order is None else order.symbol_id,
                timestamp=timestamp or datetime.now(timezone.utc),
                event_type=event_type,
                reason=reason,
                remaining_quantity=remaining_quantity,
                payload_json=json.dumps(payload or {}, sort_keys=True),
            )
        )

    def _record_trade_fill(
        self,
        order: Order,
        bar: PriceBar,
        side: OrderSide,
        quantity: float,
        price: float,
        fee: float,
        update: PositionUpdate,
        remaining_position: float,
    ) -> None:
        trade = (
            self.session.query(Trade)
            .filter(
                Trade.strategy_run_id == order.strategy_run_id,
                Trade.symbol_id == order.symbol_id,
                Trade.closed_at.is_(None),
            )
            .order_by(Trade.opened_at.asc())
            .first()
        )

        if side is OrderSide.BUY:
            if trade is None:
                self.session.add(
                    Trade(
                        strategy_run_id=order.strategy_run_id,
                        symbol_id=order.symbol_id,
                        opened_at=bar.timestamp,
                        quantity=quantity,
                        entry_price=price,
                        entry_fee=fee,
                    )
                )
                return
            total_quantity = trade.quantity + quantity
            trade.entry_price = (trade.entry_price * trade.quantity + price * quantity) / total_quantity
            trade.entry_fee += fee
            trade.quantity = total_quantity
            return

        if trade is None:
            return
        total_closed_quantity = max(trade.quantity - remaining_position, 0.0)
        previous_closed_quantity = max(total_closed_quantity - quantity, 0.0)
        if previous_closed_quantity > 0 and trade.exit_price is not None:
            trade.exit_price = (trade.exit_price * previous_closed_quantity + price * quantity) / total_closed_quantity
        else:
            trade.exit_price = price
        trade.exit_fee += fee
        trade.realized_pnl += update.realized_pnl_delta
        if remaining_position <= 1e-9:
            trade.closed_at = bar.timestamp


def _validate_nonnegative_finite(name: str, value: float) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a nonnegative finite number")


def _required_order_price(value: float | None, price_type: str) -> float:
    if value is None:
        raise ValueError(f"{price_type} price is required for this order type")
    return value


def _validate_slippage_bps(name: str, value: float) -> None:
    _validate_nonnegative_finite(name, value)
    if value >= 10_000:
        raise ValueError(f"{name} must be less than 10000")
