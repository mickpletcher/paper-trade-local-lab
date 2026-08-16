from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import pairwise
from math import isfinite, sqrt
from statistics import fmean, pvariance


def rolling_volatility(
    returns: Sequence[float],
    window: int = 20,
    periods_per_year: float = 252.0,
) -> list[float | None]:
    _validate_window(window)
    if not isfinite(periods_per_year) or periods_per_year <= 0:
        raise ValueError("periods_per_year must be finite and positive.")
    values = _finite_values(returns, "returns")
    result: list[float | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            result.append(None)
            continue
        sample = values[index + 1 - window : index + 1]
        result.append(sqrt(pvariance(sample) * periods_per_year))
    return result


def beta(asset_returns: Sequence[float], benchmark_returns: Sequence[float]) -> float | None:
    asset = _finite_values(asset_returns, "asset_returns")
    benchmark = _finite_values(benchmark_returns, "benchmark_returns")
    if len(asset) != len(benchmark):
        raise ValueError("Asset and benchmark returns must have the same length.")
    if len(asset) < 2:
        return None
    benchmark_mean = fmean(benchmark)
    variance = sum((value - benchmark_mean) ** 2 for value in benchmark)
    if variance == 0:
        return None
    asset_mean = fmean(asset)
    covariance = sum(
        (asset_value - asset_mean) * (benchmark_value - benchmark_mean)
        for asset_value, benchmark_value in zip(asset, benchmark, strict=True)
    )
    return covariance / variance


def factor_betas(asset_returns: Sequence[float], factors: Mapping[str, Sequence[float]]) -> dict[str, float | None]:
    return {name: beta(asset_returns, values) for name, values in sorted(factors.items())}


def market_regimes(prices: Sequence[float], window: int = 20, volatility_threshold: float = 0.02) -> list[str]:
    _validate_window(window)
    if not isfinite(volatility_threshold) or volatility_threshold <= 0:
        raise ValueError("volatility_threshold must be finite and positive.")
    values = _finite_values(prices, "prices")
    if any(value <= 0 for value in values):
        raise ValueError("prices must be positive.")
    returns = [(current - previous) / previous for previous, current in pairwise(values)]
    regimes = ["insufficient"] * len(values)
    for price_index in range(window, len(values)):
        sample = returns[price_index - window : price_index]
        average_return = fmean(sample)
        volatility = sqrt(pvariance(sample))
        if volatility >= volatility_threshold:
            regimes[price_index] = "high_volatility"
        elif average_return > 0.001:
            regimes[price_index] = "bull"
        elif average_return < -0.001:
            regimes[price_index] = "bear"
        else:
            regimes[price_index] = "sideways"
    return regimes


def advanced_analytics(
    prices: Sequence[float],
    benchmark_prices: Sequence[float] | None = None,
    factors: Mapping[str, Sequence[float]] | None = None,
    window: int = 20,
) -> dict[str, object]:
    values = _finite_values(prices, "prices")
    asset_returns = _returns(values)
    benchmark_beta: float | None = None
    if benchmark_prices is not None:
        benchmark_beta = beta(asset_returns, _returns(_finite_values(benchmark_prices, "benchmark_prices")))
    volatility = rolling_volatility(asset_returns, window) if asset_returns else []
    return {
        "rolling_volatility": volatility,
        "latest_rolling_volatility": next((value for value in reversed(volatility) if value is not None), None),
        "beta": benchmark_beta,
        "factor_betas": factor_betas(asset_returns, factors or {}),
        "market_regimes": market_regimes(values, window),
    }


def _returns(prices: Sequence[float]) -> list[float]:
    return [(current - previous) / previous for previous, current in pairwise(prices)]


def _finite_values(values: Sequence[float], name: str) -> list[float]:
    normalized = [float(value) for value in values]
    if any(not isfinite(value) for value in normalized):
        raise ValueError(f"{name} must contain only finite values.")
    return normalized


def _validate_window(window: int) -> None:
    if window < 2:
        raise ValueError("window must be at least 2.")
