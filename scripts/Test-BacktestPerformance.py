from __future__ import annotations

import argparse
import json

from tradeforge.backtesting.performance import AnalyticsTask, benchmark_vectorized_path, run_parallel_analytics


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=100_000)
    parser.add_argument("--max-seconds", type=float, default=5.0)
    arguments = parser.parse_args()
    prices = [100 + (index % 250) * 0.01 for index in range(arguments.rows)]
    vectorized = benchmark_vectorized_path(prices, 20, 50, arguments.max_seconds)
    task_prices = tuple(prices[:1_000])
    parallel = run_parallel_analytics(
        [
            AnalyticsTask("ALPHA", task_prices, window=20),
            AnalyticsTask("BETA", task_prices, window=20),
        ],
        max_workers=2,
    )
    if set(parallel) != {"ALPHA", "BETA"}:
        raise RuntimeError("Multiprocessing analytics returned an incomplete symbol set.")
    print(json.dumps({"vectorized": vectorized, "parallel_symbols": sorted(parallel)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
