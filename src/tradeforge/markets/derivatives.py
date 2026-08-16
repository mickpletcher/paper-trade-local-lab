from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite


@dataclass(frozen=True, slots=True)
class CFDContract:
    entry_price: float
    quantity: float
    financing_rate: float = 0.0

    def __post_init__(self) -> None:
        _positive("entry_price", self.entry_price)
        _nonzero("quantity", self.quantity)
        _finite("financing_rate", self.financing_rate)

    def profit_and_loss(self, exit_price: float, holding_days: int = 0) -> float:
        _positive("exit_price", exit_price)
        if holding_days < 0:
            raise ValueError("holding_days must be nonnegative.")
        gross = (exit_price - self.entry_price) * self.quantity
        financing = abs(self.entry_price * self.quantity) * self.financing_rate * holding_days / 365
        return gross - financing


@dataclass(frozen=True, slots=True)
class SpreadLeg:
    entry_price: float
    quantity: float

    def __post_init__(self) -> None:
        _positive("entry_price", self.entry_price)
        _nonzero("quantity", self.quantity)

    def profit_and_loss(self, exit_price: float) -> float:
        _positive("exit_price", exit_price)
        return (exit_price - self.entry_price) * self.quantity


@dataclass(frozen=True, slots=True)
class CalendarSpread:
    near_leg: SpreadLeg
    far_leg: SpreadLeg
    near_expiry: date
    far_expiry: date

    def __post_init__(self) -> None:
        if self.near_expiry >= self.far_expiry:
            raise ValueError("far_expiry must be after near_expiry.")

    def profit_and_loss(self, near_exit: float, far_exit: float) -> float:
        return self.near_leg.profit_and_loss(near_exit) + self.far_leg.profit_and_loss(far_exit)


@dataclass(frozen=True, slots=True)
class OTCMetalPosition:
    metal: str
    ounces: float
    entry_price_per_ounce: float
    storage_bps_per_year: float = 0.0

    def __post_init__(self) -> None:
        if not self.metal.strip():
            raise ValueError("metal is required.")
        _nonzero("ounces", self.ounces)
        _positive("entry_price_per_ounce", self.entry_price_per_ounce)
        if self.storage_bps_per_year < 0:
            raise ValueError("storage_bps_per_year must be nonnegative.")

    def profit_and_loss(self, exit_price_per_ounce: float, holding_days: int = 0) -> float:
        _positive("exit_price_per_ounce", exit_price_per_ounce)
        if holding_days < 0:
            raise ValueError("holding_days must be nonnegative.")
        gross = (exit_price_per_ounce - self.entry_price_per_ounce) * self.ounces
        storage = (
            abs(self.entry_price_per_ounce * self.ounces) * self.storage_bps_per_year / 10_000 * holding_days / 365
        )
        return gross - storage


@dataclass(frozen=True, slots=True)
class PredictionContract:
    entry_probability: float
    quantity: float
    outcome: bool

    def __post_init__(self) -> None:
        if not isfinite(self.entry_probability) or not 0 <= self.entry_probability <= 1:
            raise ValueError("entry_probability must be between 0 and 1.")
        _nonzero("quantity", self.quantity)

    @property
    def settlement_profit_and_loss(self) -> float:
        settlement = 1.0 if self.outcome else 0.0
        return (settlement - self.entry_probability) * self.quantity


def _finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")


def _positive(name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive.")


def _nonzero(name: str, value: float) -> None:
    if not isfinite(value) or value == 0:
        raise ValueError(f"{name} must be finite and nonzero.")
