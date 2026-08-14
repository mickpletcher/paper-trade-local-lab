from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from tradeforge.database.models import OrderSide, OrderType, PriceBar


@dataclass(frozen=True)
class StrategySignal:
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: float | None = None
    stop_price: float | None = None


@dataclass
class StrategyContext:
    bars: list[PriceBar]
    position_quantity: float = 0.0
    pending_buy_quantity: float = 0.0
    pending_sell_quantity: float = 0.0


class BaseStrategy(ABC):
    name: str

    def get_order_cancellations(self, bar: PriceBar, context: StrategyContext) -> list[OrderSide]:
        return []

    @abstractmethod
    def on_bar(self, bar: PriceBar, context: StrategyContext) -> StrategySignal | None:
        """Return an order signal for the current bar, or None."""
