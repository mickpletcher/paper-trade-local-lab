from __future__ import annotations

from dataclasses import dataclass

from tradeforge.database.models import OrderSide, OrderType


@dataclass(frozen=True)
class OrderRequest:
    symbol_id: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: float | None = None
    strategy_run_id: str | None = None

    def validate(self) -> None:
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        if self.order_type is OrderType.LIMIT and self.limit_price is None:
            raise ValueError("Limit orders require a limit price")
