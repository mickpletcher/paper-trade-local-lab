from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from importlib.resources import as_file, files
from pathlib import Path

import typer
from sqlalchemy import select

from tradeforge.backtesting.engine import BacktestEngine
from tradeforge.database.migrations import init_db as create_schema
from tradeforge.database.models import Order, Position, StrategyRun
from tradeforge.database.session import session_scope
from tradeforge.market_data.importer import import_ohlcv_csv
from tradeforge.strategies.moving_average_cross import MovingAverageCrossStrategy

app = typer.Typer(help="TradeForge local paper trading and backtesting CLI.")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@app.command("init-db")
def init_db() -> None:
    """Create the local SQLite schema."""
    create_schema()
    typer.echo("Initialized TradeForge database.")


@app.command("import-csv")
def import_csv(
    symbol: str = typer.Option(..., "--symbol", "-s"),
    file: Path = typer.Option(..., "--file", "-f", exists=True, file_okay=True, dir_okay=False),
) -> None:
    """Import OHLCV CSV data."""
    create_schema()
    with session_scope() as session:
        count = import_ohlcv_csv(session, symbol, file)
    typer.echo(f"Imported {count} bars for {symbol.upper()}.")


@app.command("seed-sample-data")
def seed_sample_data(symbol: str = typer.Option("AAPL", "--symbol", "-s")) -> None:
    create_schema()
    dataset = files("tradeforge.sample_data").joinpath("aapl_sample.csv")
    with as_file(dataset) as file_path:
        with session_scope() as session:
            count = import_ohlcv_csv(session, symbol, file_path)
    typer.echo(f"Seeded {count} sample bars for {symbol.upper()}.")


@app.command("run-backtest")
def run_backtest(
    strategy: str = typer.Option(..., "--strategy"),
    symbol: str = typer.Option(..., "--symbol"),
    start: str = typer.Option(..., "--start"),
    end: str = typer.Option(..., "--end"),
    short_window: int = typer.Option(20, "--short-window"),
    long_window: int = typer.Option(50, "--long-window"),
    order_size: float = typer.Option(10.0, "--order-size"),
) -> None:
    """Run a historical strategy backtest."""
    create_schema()
    if strategy != "moving-average-cross":
        raise typer.BadParameter("Only moving-average-cross is available in the MVP.")
    strategy_obj = MovingAverageCrossStrategy(short_window=short_window, long_window=long_window, order_size=order_size)
    with session_scope() as session:
        result = BacktestEngine(session, strategy_obj, symbol, _parse_date(start), _parse_date(end)).run()
    typer.echo(json.dumps(result, indent=2))


@app.command("show-positions")
def show_positions() -> None:
    """Show current simulated positions."""
    create_schema()
    with session_scope() as session:
        positions = session.scalars(select(Position)).all()
        if not positions:
            typer.echo("No positions.")
            return
        for position in positions:
            typer.echo(
                f"{position.symbol.ticker} qty={position.quantity:g} avg_cost={position.average_cost:.2f} "
                f"realized_pnl={position.realized_pnl:.2f}"
            )


@app.command("show-orders")
def show_orders() -> None:
    """Show simulated orders."""
    create_schema()
    with session_scope() as session:
        orders = session.scalars(select(Order).order_by(Order.submitted_at.desc())).all()
        if not orders:
            typer.echo("No orders.")
            return
        for order in orders:
            typer.echo(
                f"{order.submitted_at} {order.symbol.ticker} {order.side} {order.order_type} "
                f"qty={order.quantity:g} status={order.status}"
            )


@app.command("show-pnl")
def show_pnl() -> None:
    """Show completed strategy run P/L summaries."""
    create_schema()
    with session_scope() as session:
        runs = session.scalars(select(StrategyRun).order_by(StrategyRun.started_at.desc())).all()
        if not runs:
            typer.echo("No strategy runs.")
            return
        for run in runs:
            metrics = json.loads(run.metrics_json or "{}")
            typer.echo(
                f"{run.id} {run.strategy.name} {run.symbol.ticker} "
                f"ending_equity={metrics.get('ending_equity', 'n/a')} total_return={metrics.get('total_return', 'n/a')}"
            )


def _parse_date(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


if __name__ == "__main__":
    app()
