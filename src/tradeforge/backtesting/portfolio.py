from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite

from sqlalchemy.orm import Session

from tradeforge.backtesting.engine import BacktestEngine
from tradeforge.runtime.events import Event, EventKind, EventRuntime
from tradeforge.strategies.base import BaseStrategy


class AllocationRule(str, Enum):
    EQUAL = "equal"
    FIXED = "fixed"


@dataclass(frozen=True, slots=True)
class PortfolioRun:
    symbol: str
    allocation: float
    strategy_run_id: str
    ending_equity: float
    total_return: float
    report_path: str


class PortfolioBacktestEngine:
    def __init__(
        self,
        session: Session,
        strategy_factory: Callable[[], BaseStrategy],
        symbols: Sequence[str],
        start_at: datetime,
        end_at: datetime,
        total_cash: float,
        *,
        allocation_rule: AllocationRule = AllocationRule.EQUAL,
        weights: Mapping[str, float] | None = None,
        runtime: EventRuntime | None = None,
    ) -> None:
        normalized_symbols = [symbol.strip().upper() for symbol in symbols]
        if not normalized_symbols or any(not symbol for symbol in normalized_symbols):
            raise ValueError("At least one nonempty symbol is required.")
        if len(set(normalized_symbols)) != len(normalized_symbols):
            raise ValueError("Portfolio symbols must be unique.")
        if not isfinite(total_cash) or total_cash <= 0:
            raise ValueError("total_cash must be finite and positive.")
        self.session = session
        self.strategy_factory = strategy_factory
        self.symbols = normalized_symbols
        self.start_at = start_at
        self.end_at = end_at
        self.total_cash = total_cash
        self.allocations = _build_allocations(normalized_symbols, total_cash, allocation_rule, weights)
        self.runtime = runtime or EventRuntime()

    def run(self) -> dict[str, object]:
        self.runtime.publish(
            Event(
                self.start_at,
                EventKind.SYSTEM,
                {"event": "portfolio_started", "symbols": self.symbols, "total_cash": self.total_cash},
            )
        )
        runs: list[PortfolioRun] = []
        for symbol in self.symbols:
            result = BacktestEngine(
                self.session,
                self.strategy_factory(),
                symbol,
                self.start_at,
                self.end_at,
                starting_cash=self.allocations[symbol],
            ).run()
            metrics = result["metrics"]
            if not isinstance(metrics, dict):
                raise TypeError("Backtest metrics must be a dictionary.")
            run = PortfolioRun(
                symbol=symbol,
                allocation=self.allocations[symbol],
                strategy_run_id=str(result["strategy_run_id"]),
                ending_equity=float(metrics["ending_equity"]),
                total_return=float(metrics["total_return"]),
                report_path=str(result["report_path"]),
            )
            runs.append(run)
            self.runtime.publish(
                Event(
                    self.end_at,
                    EventKind.SYSTEM,
                    {"event": "symbol_completed", "symbol": symbol, "strategy_run_id": run.strategy_run_id},
                )
            )
        processed_events = self.runtime.run()
        ending_equity = sum(run.ending_equity for run in runs)
        return {
            "starting_cash": round(self.total_cash, 2),
            "ending_equity": round(ending_equity, 2),
            "total_return": round((ending_equity - self.total_cash) / self.total_cash, 6),
            "allocations": {symbol: round(value, 2) for symbol, value in self.allocations.items()},
            "runs": [
                {
                    "symbol": run.symbol,
                    "allocation": run.allocation,
                    "strategy_run_id": run.strategy_run_id,
                    "ending_equity": run.ending_equity,
                    "total_return": run.total_return,
                    "report_path": run.report_path,
                }
                for run in runs
            ],
            "events_processed": len(processed_events),
        }


def _build_allocations(
    symbols: Sequence[str],
    total_cash: float,
    rule: AllocationRule,
    weights: Mapping[str, float] | None,
) -> dict[str, float]:
    if rule is AllocationRule.EQUAL:
        weight_map = {symbol: 1 / len(symbols) for symbol in symbols}
    else:
        if weights is None:
            raise ValueError("Fixed allocation requires weights.")
        weight_map = {symbol.strip().upper(): float(value) for symbol, value in weights.items()}
        if set(weight_map) != set(symbols):
            raise ValueError("Fixed allocation weights must match the portfolio symbols exactly.")
        if any(not isfinite(value) or value <= 0 for value in weight_map.values()):
            raise ValueError("Fixed allocation weights must be finite and positive.")
        weight_total = sum(weight_map.values())
        if abs(weight_total - 1.0) > 1e-9:
            raise ValueError("Fixed allocation weights must sum to 1.")
    allocations = {symbol: total_cash * weight_map[symbol] for symbol in symbols}
    rounding_delta = total_cash - sum(allocations.values())
    allocations[symbols[-1]] += rounding_delta
    return allocations
