from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite, sqrt

from tradeforge.database.models import OrderSide


@dataclass(frozen=True, slots=True)
class MarketMicrostructure:
    session_phase: str = "continuous"
    halted: bool = False
    lower_price_limit: float | None = None
    upper_price_limit: float | None = None
    round_lot_size: int = 100
    latency_ms: int = 0
    queue_ahead_quantity: float = 0.0
    daily_volume: float = 1_000_000.0
    market_impact_coefficient: float = 0.0

    def __post_init__(self) -> None:
        if self.session_phase not in {"opening_auction", "continuous", "closing_auction"}:
            raise ValueError("Unsupported session phase.")
        if self.round_lot_size <= 0 or self.latency_ms < 0:
            raise ValueError("round_lot_size must be positive and latency_ms must be nonnegative.")
        for name, value in (
            ("queue_ahead_quantity", self.queue_ahead_quantity),
            ("daily_volume", self.daily_volume),
            ("market_impact_coefficient", self.market_impact_coefficient),
        ):
            if not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative.")
        if self.daily_volume == 0:
            raise ValueError("daily_volume must be positive.")
        if (
            self.lower_price_limit is not None
            and self.upper_price_limit is not None
            and self.lower_price_limit > self.upper_price_limit
        ):
            raise ValueError("lower_price_limit must not exceed upper_price_limit.")

    def simulate_fill(
        self,
        side: OrderSide,
        requested_quantity: float,
        reference_price: float,
        available_quantity: float,
        submitted_at: datetime,
    ) -> "MicrostructureFill":
        if submitted_at.tzinfo is None or submitted_at.utcoffset() is None:
            raise ValueError("submitted_at must be timezone aware.")
        if requested_quantity <= 0 or reference_price <= 0 or available_quantity < 0:
            raise ValueError("Quantities and reference price are invalid.")
        if self.halted:
            return MicrostructureFill(0.0, reference_price, submitted_at, False, self.session_phase, "halted")
        executable = min(requested_quantity, max(available_quantity - self.queue_ahead_quantity, 0.0))
        impact = reference_price * self.market_impact_coefficient * sqrt(executable / self.daily_volume)
        execution_price = reference_price + impact if side is OrderSide.BUY else reference_price - impact
        if self.lower_price_limit is not None:
            execution_price = max(execution_price, self.lower_price_limit)
        if self.upper_price_limit is not None:
            execution_price = min(execution_price, self.upper_price_limit)
        return MicrostructureFill(
            quantity=executable,
            price=execution_price,
            executed_at=submitted_at + timedelta(milliseconds=self.latency_ms),
            odd_lot=0 < executable < self.round_lot_size,
            session_phase=self.session_phase,
            reason="filled" if executable else "queue_blocked",
        )


@dataclass(frozen=True, slots=True)
class MicrostructureFill:
    quantity: float
    price: float
    executed_at: datetime
    odd_lot: bool
    session_phase: str
    reason: str
