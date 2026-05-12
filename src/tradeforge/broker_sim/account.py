from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SimAccount:
    starting_cash: float = 100_000.0
    cash: float = 100_000.0

    @classmethod
    def with_starting_cash(cls, starting_cash: float) -> "SimAccount":
        return cls(starting_cash=starting_cash, cash=starting_cash)
