from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class InternationalEquity:
    symbol: str
    exchange: str
    currency: str
    country_code: str
    lot_size: float = 1.0

    def __post_init__(self) -> None:
        if not self.symbol.strip() or not self.exchange.strip():
            raise ValueError("Equity symbol and exchange are required.")
        if len(self.currency.strip()) != 3 or len(self.country_code.strip()) != 2:
            raise ValueError("Currency and country must use three and two letter codes.")
        _positive("lot_size", self.lot_size)

    def base_currency_value(self, quantity: float, local_price: float, fx_rate: float) -> float:
        _finite("quantity", quantity)
        _positive("local_price", local_price)
        _positive("fx_rate", fx_rate)
        return quantity * local_price * fx_rate


@dataclass(frozen=True, slots=True)
class FixedIncomeInstrument:
    face_value: float
    coupon_rate: float
    maturity_years: float
    payments_per_year: int = 2
    credit_spread_bps: float = 0.0

    def __post_init__(self) -> None:
        _positive("face_value", self.face_value)
        _nonnegative("coupon_rate", self.coupon_rate)
        _positive("maturity_years", self.maturity_years)
        if self.payments_per_year <= 0:
            raise ValueError("payments_per_year must be positive.")
        _nonnegative("credit_spread_bps", self.credit_spread_bps)

    def price(self, risk_free_yield: float) -> float:
        _nonnegative("risk_free_yield", risk_free_yield)
        periods = max(round(self.maturity_years * self.payments_per_year), 1)
        period_yield = (risk_free_yield + self.credit_spread_bps / 10_000) / self.payments_per_year
        coupon = self.face_value * self.coupon_rate / self.payments_per_year
        if period_yield == 0:
            return self.face_value + coupon * periods
        discount = 1 + period_yield
        return sum(coupon / discount**period for period in range(1, periods + 1)) + self.face_value / discount**periods


@dataclass(frozen=True, slots=True)
class RateInstrument:
    notional: float
    fixed_rate: float
    term_years: float

    def __post_init__(self) -> None:
        _positive("notional", self.notional)
        _finite("fixed_rate", self.fixed_rate)
        _positive("term_years", self.term_years)

    def mark_to_market(self, floating_rate: float) -> float:
        _finite("floating_rate", floating_rate)
        return self.notional * (floating_rate - self.fixed_rate) * self.term_years


@dataclass(frozen=True, slots=True)
class CreditInstrument:
    notional: float
    default_probability: float
    recovery_rate: float

    def __post_init__(self) -> None:
        _positive("notional", self.notional)
        _ratio("default_probability", self.default_probability)
        _ratio("recovery_rate", self.recovery_rate)

    @property
    def expected_loss(self) -> float:
        return self.notional * self.default_probability * (1 - self.recovery_rate)


@dataclass(frozen=True, slots=True)
class VolatilityInstrument:
    notional: float
    strike: float
    multiplier: float = 1.0

    def __post_init__(self) -> None:
        _positive("notional", self.notional)
        _nonnegative("strike", self.strike)
        _positive("multiplier", self.multiplier)

    def payoff(self, realized_volatility: float) -> float:
        _nonnegative("realized_volatility", realized_volatility)
        return self.notional * self.multiplier * (realized_volatility - self.strike)


@dataclass(frozen=True, slots=True)
class IndexDerivative:
    index_name: str
    entry_price: float
    multiplier: float

    def __post_init__(self) -> None:
        if not self.index_name.strip():
            raise ValueError("index_name is required.")
        _positive("entry_price", self.entry_price)
        _positive("multiplier", self.multiplier)

    def profit_and_loss(self, exit_price: float, contracts: int = 1) -> float:
        _positive("exit_price", exit_price)
        if contracts == 0:
            raise ValueError("contracts must not be zero.")
        return (exit_price - self.entry_price) * self.multiplier * contracts


def _finite(name: str, value: float) -> None:
    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")


def _positive(name: str, value: float) -> None:
    if not isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be finite and positive.")


def _nonnegative(name: str, value: float) -> None:
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative.")


def _ratio(name: str, value: float) -> None:
    if not isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{name} must be between 0 and 1.")
