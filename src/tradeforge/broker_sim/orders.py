from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from tradeforge.database.models import OrderSide, OrderType


@dataclass(frozen=True)
class OrderRequest:
    symbol_id: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: float | None = None
    stop_price: float | None = None
    strategy_run_id: str | None = None

    def validate(self) -> None:
        if not isfinite(self.quantity) or self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        if self.order_type is OrderType.LIMIT:
            self._validate_price("Limit orders", self.limit_price, "limit")
        if self.order_type is OrderType.STOP:
            self._validate_price("Stop orders", self.stop_price, "stop")
        if self.order_type is OrderType.STOP_LIMIT:
            self._validate_price("Stop limit orders", self.stop_price, "stop")
            self._validate_price("Stop limit orders", self.limit_price, "limit")

    @staticmethod
    def _validate_price(order_name: str, price: float | None, price_name: str) -> None:
        if price is None:
            raise ValueError(f"{order_name} require a {price_name} price")
        if not isfinite(price) or price <= 0:
            raise ValueError(f"{order_name} require a positive finite {price_name} price")
