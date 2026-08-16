from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tradeforge.broker_sim.account import SimAccount
from tradeforge.broker_sim.orders import OrderRequest
from tradeforge.database.models import Fill, Order, OrderSide, Position


class RiskLimitError(ValueError):
    pass


@dataclass(frozen=True)
class RiskLimits:
    max_order_notional: float
    max_position_quantity: float
    max_gross_exposure: float
    max_drawdown_ratio: float
    kill_switch: bool = False


class RiskEngine:
    def __init__(
        self,
        session: Session,
        account: SimAccount,
        limits: RiskLimits,
        strategy_run_id: str | None,
    ) -> None:
        self.session = session
        self.account = account
        self.limits = limits
        self.strategy_run_id = strategy_run_id
        self.mark_prices: dict[str, float] = {}
        self.peak_equity = account.starting_cash

    def update_mark(self, symbol_id: str, price: float) -> None:
        if isfinite(price) and price > 0:
            self.mark_prices[symbol_id] = price
            self.peak_equity = max(self.peak_equity, self.current_equity())

    def validate_order(self, request: OrderRequest, reference_price: float | None) -> None:
        if request.side is OrderSide.BUY:
            if self.limits.kill_switch:
                raise RiskLimitError("Risk kill switch is active")
            self._validate_drawdown()
        if reference_price is None:
            return
        self._validate_notional(request.quantity * reference_price)
        position = self._position(request.symbol_id)
        projected_quantity = (
            position.quantity + request.quantity if request.side is OrderSide.BUY else position.quantity
        )
        if projected_quantity > self.limits.max_position_quantity + 1e-9:
            raise RiskLimitError("Order exceeds the maximum position quantity")
        projected_exposure = self.current_gross_exposure()
        if request.side is OrderSide.BUY:
            projected_exposure += request.quantity * reference_price
        else:
            projected_exposure -= min(request.quantity, position.quantity) * reference_price
        if projected_exposure > self.limits.max_gross_exposure + 1e-9:
            raise RiskLimitError("Order exceeds the maximum gross exposure")

    def validate_fill(self, order: Order, quantity: float, price: float) -> None:
        side = OrderSide(order.side)
        if side is OrderSide.BUY:
            if self.limits.kill_switch:
                raise RiskLimitError("Risk kill switch is active")
            self._validate_drawdown()
        prior_notional = self.session.scalar(
            select(func.coalesce(func.sum(Fill.quantity * Fill.price), 0.0)).where(Fill.order_id == order.id)
        )
        self._validate_notional(float(prior_notional or 0.0) + quantity * price)
        position = self._position(order.symbol_id)
        if side is OrderSide.BUY:
            if position.quantity + quantity > self.limits.max_position_quantity + 1e-9:
                raise RiskLimitError("Fill exceeds the maximum position quantity")
            projected_exposure = self.current_gross_exposure() + quantity * price
            if projected_exposure > self.limits.max_gross_exposure + 1e-9:
                raise RiskLimitError("Fill exceeds the maximum gross exposure")

    def current_equity(self) -> float:
        market_value = sum(
            position.quantity * self.mark_prices.get(position.symbol_id, position.average_cost)
            for position in self._positions()
        )
        return self.account.cash + market_value

    def current_gross_exposure(self) -> float:
        return sum(
            abs(position.quantity * self.mark_prices.get(position.symbol_id, position.average_cost))
            for position in self._positions()
        )

    def _validate_notional(self, notional: float) -> None:
        if notional > self.limits.max_order_notional + 1e-9:
            raise RiskLimitError("Order exceeds the maximum notional")

    def _validate_drawdown(self) -> None:
        equity = self.current_equity()
        self.peak_equity = max(self.peak_equity, equity)
        drawdown = 0.0 if self.peak_equity <= 0 else (self.peak_equity - equity) / self.peak_equity
        if drawdown > self.limits.max_drawdown_ratio + 1e-9:
            raise RiskLimitError("Maximum drawdown limit has been breached")

    def _positions(self) -> list[Position]:
        return list(self.session.scalars(select(Position).where(Position.strategy_run_id == self.strategy_run_id)))

    def _position(self, symbol_id: str) -> Position:
        position = self.session.scalar(
            select(Position).where(Position.strategy_run_id == self.strategy_run_id, Position.symbol_id == symbol_id)
        )
        return position or Position(
            symbol_id=symbol_id,
            strategy_run_id=self.strategy_run_id,
            quantity=0.0,
            average_cost=0.0,
            realized_pnl=0.0,
        )
