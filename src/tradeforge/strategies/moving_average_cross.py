from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from tradeforge.database.models import OrderSide, OrderType, PriceBar
from tradeforge.strategies.base import BaseStrategy, StrategyContext, StrategySignal


@dataclass
class MovingAverageCrossStrategy(BaseStrategy):
    short_window: int = 20
    long_window: int = 50
    order_size: float = 10.0

    name: str = "moving-average-cross"

    def __post_init__(self) -> None:
        if self.short_window <= 0 or self.long_window <= 0:
            raise ValueError("Moving average windows must be positive")
        if self.short_window >= self.long_window:
            raise ValueError("short_window must be less than long_window")
        if not isfinite(self.order_size) or self.order_size <= 0:
            raise ValueError("order_size must be a positive finite number")

    def on_bar(self, bar: PriceBar, context: StrategyContext) -> StrategySignal | None:
        crossed_up, crossed_down = self._crossovers(context.bars)
        if not crossed_up and not crossed_down:
            return None
        if crossed_up and context.position_quantity <= 0 and context.pending_buy_quantity <= 0:
            return StrategySignal(OrderSide.BUY, OrderType.MARKET, self.order_size)
        if crossed_down and context.position_quantity > 0 and context.pending_sell_quantity <= 0:
            return StrategySignal(OrderSide.SELL, OrderType.MARKET, min(self.order_size, context.position_quantity))
        return None

    def get_order_cancellations(self, bar: PriceBar, context: StrategyContext) -> list[OrderSide]:
        crossed_up, crossed_down = self._crossovers(context.bars)
        if crossed_down and context.pending_buy_quantity > 0:
            return [OrderSide.BUY]
        if crossed_up and context.pending_sell_quantity > 0:
            return [OrderSide.SELL]
        return []

    def _crossovers(self, bars: list[PriceBar]) -> tuple[bool, bool]:
        if len(bars) < self.long_window + 1:
            return False, False
        previous = bars[:-1]
        short_prev = self._mean_close(previous[-self.short_window :])
        long_prev = self._mean_close(previous[-self.long_window :])
        short_now = self._mean_close(bars[-self.short_window :])
        long_now = self._mean_close(bars[-self.long_window :])
        return short_prev <= long_prev and short_now > long_now, short_prev >= long_prev and short_now < long_now

    @staticmethod
    def _mean_close(bars: list[PriceBar]) -> float:
        return sum(bar.close for bar in bars) / len(bars)
