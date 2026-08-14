from __future__ import annotations

from pathlib import Path

from tradeforge.database.models import Position, StrategyRun, Trade


def write_markdown_report(
    run: StrategyRun,
    parameters: dict[str, object],
    metrics: dict[str, object],
    trades: list[Trade],
    positions: list[Position],
    reports_dir: Path = Path("data/reports"),
) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / f"{run.id}.md"
    lines = [
        "# TradeForge Backtest Report",
        "",
        f"Strategy: {run.strategy.name}",
        f"Symbol: {run.symbol.ticker}",
        f"Date range: {run.start_date.date()} to {run.end_date.date()}",
        "",
        "## Parameters",
        "",
    ]
    lines.extend(f"- {key}: {value}" for key, value in parameters.items())
    lines.extend(["", "## Metrics", ""])
    lines.extend(f"- {key}: {value}" for key, value in metrics.items())
    lines.extend(
        [
            "",
            "## Trades",
            "",
            "| Opened | Closed | Qty | Entry | Exit | Realized P/L |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for trade in trades:
        lines.append(
            f"| {trade.opened_at} | {trade.closed_at or ''} | {trade.quantity:g} | "
            f"{trade.entry_price:.2f} | {trade.exit_price or 0:.2f} | {trade.realized_pnl:.2f} |"
        )
    lines.extend(
        ["", "## Final Positions", "", "| Symbol | Quantity | Average Cost | Realized P/L |", "|---|---:|---:|---:|"]
    )
    for position in positions:
        lines.append(
            f"| {position.symbol.ticker} | {position.quantity:g} | {position.average_cost:.2f} | {position.realized_pnl:.2f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
