from __future__ import annotations

from dataclasses import dataclass

from tradeforge.database.models import OrderSide, OrderType, PriceBar
from tradeforge.strategies.base import BaseStrategy, StrategyContext, StrategySignal


@dataclass
class MovingAverageCrossStrategy(BaseStrategy):
    short_window: int = 20
    long_window: int = 50
    order_size: float = 10.0

    name: str = "moving-average-cross"

    def on_bar(self, bar: PriceBar, context: StrategyContext) -> StrategySignal | None:
        bars = context.bars
        if len(bars) < self.long_window + 1:
            return None

        previous = bars[:-1]
        short_prev = self._mean_close(previous[-self.short_window :])
        long_prev = self._mean_close(previous[-self.long_window :])
        short_now = self._mean_close(bars[-self.short_window :])
        long_now = self._mean_close(bars[-self.long_window :])

        crossed_up = short_prev <= long_prev and short_now > long_now
        crossed_down = short_prev >= long_prev and short_now < long_now
        if crossed_up and not context.has_position:
            return StrategySignal(OrderSide.BUY, OrderType.MARKET, self.order_size)
        if crossed_down and context.has_position:
            return StrategySignal(OrderSide.SELL, OrderType.MARKET, self.order_size)
        return None

    @staticmethod
    def _mean_close(bars: list[PriceBar]) -> float:
        return sum(bar.close for bar in bars) / len(bars)
