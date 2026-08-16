from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Mutation:
    name: str
    file: str
    original: str
    replacement: str
    test: str


MUTATIONS = (
    Mutation(
        "oversized sell guard",
        "src/tradeforge/broker_sim/execution.py",
        "remaining_order_quantity > remaining_position + 1e-9",
        "remaining_order_quantity < remaining_position + 1e-9",
        "tests/test_orders.py",
    ),
    Mutation(
        "total return direction",
        "src/tradeforge/backtesting/metrics.py",
        "ending_equity - starting_cash",
        "starting_cash - ending_equity",
        "tests/test_backtest.py",
    ),
    Mutation(
        "portfolio cash inclusion",
        "src/tradeforge/valuation/service.py",
        "total_cash + total_market_value",
        "total_market_value",
        "tests/test_live_quotes.py",
    ),
)


def main() -> int:
    repo = Path(__file__).resolve().parent.parent
    survivors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="tradeforge-mutations-") as temp_dir:
        root = Path(temp_dir)
        shutil.copytree(repo / "src", root / "src")
        shutil.copytree(repo / "tests", root / "tests")
        shutil.copy2(repo / "pyproject.toml", root / "pyproject.toml")
        for mutation in MUTATIONS:
            target = root / mutation.file
            content = target.read_text(encoding="utf-8")
            if content.count(mutation.original) != 1:
                raise RuntimeError(f"Mutation anchor changed: {mutation.name}")
            target.write_text(content.replace(mutation.original, mutation.replacement), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", mutation.test],
                cwd=root,
                check=False,
            )
            if result.returncode == 0:
                survivors.append(mutation.name)
            target.write_text(content, encoding="utf-8")
    if survivors:
        print(f"Surviving mutations: {', '.join(survivors)}", file=sys.stderr)
        return 1
    print(f"Killed {len(MUTATIONS)} correctness mutations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
