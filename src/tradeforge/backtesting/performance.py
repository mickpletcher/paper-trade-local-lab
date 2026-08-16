from __future__ import annotations

from collections.abc import Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from time import perf_counter

import pandas as pd

from tradeforge.analytics.advanced import advanced_analytics


def vectorized_moving_average_signals(
    closes: Sequence[float],
    short_window: int,
    long_window: int,
) -> list[int]:
    if short_window <= 0 or long_window <= 0 or short_window >= long_window:
        raise ValueError("Moving average windows must be positive and short_window must be less than long_window.")
    series = pd.Series([float(value) for value in closes], dtype="float64")
    short_average = series.rolling(short_window).mean()
    long_average = series.rolling(long_window).mean()
    previous_short = short_average.shift(1)
    previous_long = long_average.shift(1)
    crossed_above = (previous_short <= previous_long) & (short_average > long_average)
    crossed_below = (previous_short >= previous_long) & (short_average < long_average)
    signals = pd.Series(0, index=series.index, dtype="int64")
    signals[crossed_above] = 1
    signals[crossed_below] = -1
    return [int(value) for value in signals.tolist()]


@dataclass(frozen=True, slots=True)
class AnalyticsTask:
    symbol: str
    prices: tuple[float, ...]
    benchmark_prices: tuple[float, ...] | None = None
    window: int = 20


def run_parallel_analytics(
    tasks: Sequence[AnalyticsTask], max_workers: int | None = None
) -> dict[str, dict[str, object]]:
    if max_workers is not None and max_workers <= 0:
        raise ValueError("max_workers must be positive.")
    normalized = list(tasks)
    if len({task.symbol for task in normalized}) != len(normalized):
        raise ValueError("Analytics task symbols must be unique.")
    if max_workers == 1 or len(normalized) < 2:
        results = [_run_analytics_task(task) for task in normalized]
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            results = list(executor.map(_run_analytics_task, normalized))
    return dict(results)


def benchmark_vectorized_path(
    closes: Sequence[float],
    short_window: int,
    long_window: int,
    maximum_seconds: float,
) -> Mapping[str, float | int]:
    if maximum_seconds <= 0:
        raise ValueError("maximum_seconds must be positive.")
    started = perf_counter()
    signals = vectorized_moving_average_signals(closes, short_window, long_window)
    elapsed = perf_counter() - started
    if elapsed > maximum_seconds:
        raise RuntimeError(f"Vectorized signal generation exceeded {maximum_seconds:g} seconds: {elapsed:.6f}")
    return {"rows": len(signals), "signals": sum(value != 0 for value in signals), "elapsed_seconds": elapsed}


def _run_analytics_task(task: AnalyticsTask) -> tuple[str, dict[str, object]]:
    return task.symbol, advanced_analytics(task.prices, task.benchmark_prices, window=task.window)
