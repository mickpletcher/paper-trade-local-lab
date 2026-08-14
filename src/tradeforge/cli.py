from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from importlib.resources import as_file, files
from pathlib import Path
from typing import Optional

import typer
from sqlalchemy import select
import uvicorn

from tradeforge.automation import MaintenanceError, run_maintenance
from tradeforge.backtesting.engine import BacktestEngine
from tradeforge.config import get_settings
from tradeforge.database.migrations import create_revision, get_current_version, get_head_version, init_db as create_schema
from tradeforge.database.models import LiveQuote, Order, Position, StrategyRun, Symbol
from tradeforge.database.session import session_scope
from tradeforge.market_data.importer import import_ohlcv_csv
from tradeforge.market_data.live import (
    QuoteProviderError,
    get_default_refresh_symbols,
    refresh_live_quotes,
    serialize_quote,
)
from tradeforge.strategies.moving_average_cross import MovingAverageCrossStrategy
from tradeforge.telemetry import get_logger, log_event, setup_logging
from tradeforge.valuation.service import build_portfolio_valuation

app = typer.Typer(help="TradeForge local paper trading and backtesting CLI.")
setup_logging()
logger = get_logger(__name__)
AVAILABLE_STRATEGIES = {"moving-average-cross"}


@app.command("init-db")
def init_db() -> None:
    """Create the local SQLite schema."""
    create_schema()
    log_event(logger, logging.INFO, "database_upgraded", current_version=get_current_version(), head_version=get_head_version())
    typer.echo("Initialized TradeForge database.")


@app.command("db-current")
def db_current() -> None:
    create_schema()
    typer.echo(
        json.dumps(
            {
                "current_version": get_current_version(),
                "head_version": get_head_version(),
            },
            indent=2,
        )
    )


@app.command("db-revision")
def db_revision(
    message: str = typer.Option(..., "--message", "-m"),
    autogenerate: bool = typer.Option(True, "--autogenerate/--empty"),
) -> None:
    path = create_revision(message=message, autogenerate=autogenerate)
    if path is None:
        raise typer.Exit(code=1)
    log_event(logger, logging.INFO, "database_revision_created", message_text=message, path=path, autogenerate=autogenerate)
    typer.echo(path)


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
    strategy_name = strategy.strip().lower()
    if strategy_name not in AVAILABLE_STRATEGIES:
        available = ", ".join(sorted(AVAILABLE_STRATEGIES))
        raise typer.BadParameter(f"Unknown strategy '{strategy}'. Available strategies: {available}.")
    start_at = _parse_date_option("--start", start)
    end_at = _parse_date_option("--end", end)
    if start_at >= end_at:
        raise typer.BadParameter("The start date must be earlier than the end date.")
    normalized_symbol = symbol.strip().upper()
    try:
        strategy_obj = MovingAverageCrossStrategy(short_window=short_window, long_window=long_window, order_size=order_size)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    log_event(
        logger,
        logging.INFO,
        "backtest_started",
        strategy=strategy_name,
        symbol=normalized_symbol,
        start=start_at.isoformat(),
        end=end_at.isoformat(),
    )
    with session_scope() as session:
        _ensure_symbol_exists(session, normalized_symbol)
        result = BacktestEngine(session, strategy_obj, normalized_symbol, start_at, end_at).run()
    log_event(logger, logging.INFO, "backtest_completed", strategy_run_id=result["strategy_run_id"], metrics=result["metrics"])
    typer.echo(json.dumps(result, indent=2))


@app.command("refresh-quotes")
def refresh_quotes(
    symbol: list[str] = typer.Option(None, "--symbol", "-s", help="Repeat to refresh specific symbols."),
) -> None:
    """Refresh latest quotes for open positions or the requested symbols."""
    create_schema()
    settings = get_settings()
    with session_scope() as session:
        symbols = symbol or get_default_refresh_symbols(session)
        if not symbols:
            raise typer.BadParameter("No symbols were provided and no open positions were found to refresh.")
        try:
            refreshed = refresh_live_quotes(session, symbols)
        except QuoteProviderError as exc:
            raise typer.BadParameter(str(exc)) from exc
    log_event(
        logger,
        logging.INFO,
        "quotes_refreshed",
        provider=settings.quote_provider,
        symbols=[item.upper() for item in symbols],
        refreshed_count=len(refreshed),
    )
    typer.echo(f"Refreshed {len(refreshed)} quotes using {settings.quote_provider}.")


@app.command("run-maintenance")
def run_maintenance_command() -> None:
    """Import queued data, refresh open positions, back up SQLite, and write a run report."""
    try:
        result = run_maintenance()
    except MaintenanceError as exc:
        if exc.report_path is not None:
            typer.echo(f"Maintenance failed. Report: {exc.report_path}", err=True)
        else:
            typer.echo(f"Maintenance failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(json.dumps(result, indent=2))


@app.command("start-api")
def start_api(
    host: str = typer.Option("127.0.0.1", "--host"),
    port: int = typer.Option(8000, "--port"),
    reload: bool = typer.Option(False, "--reload"),
) -> None:
    """Start the local TradeForge API."""
    settings = get_settings()
    log_event(
        logger,
        logging.INFO,
        "api_starting",
        host=host,
        port=port,
        reload=reload,
        metrics_enabled=settings.enable_metrics,
        log_format=settings.log_format,
    )
    uvicorn.run("tradeforge.api.app:app", host=host, port=port, reload=reload)


@app.command("show-quotes")
def show_quotes() -> None:
    """Show the latest stored live quotes."""
    create_schema()
    settings = get_settings()
    with session_scope() as session:
        quotes = session.scalars(select(LiveQuote).order_by(LiveQuote.fetched_at.desc())).all()
        if not quotes:
            typer.echo("No live quotes.")
            return
        payload = [serialize_quote(quote, settings.quote_stale_after_seconds) for quote in quotes]
    typer.echo(json.dumps(payload, indent=2))


@app.command("show-valuation")
def show_valuation(strategy_run_id: Optional[str] = typer.Option(None, "--strategy-run-id")) -> None:
    """Show current local portfolio valuation from the latest quotes."""
    create_schema()
    settings = get_settings()
    with session_scope() as session:
        try:
            payload = build_portfolio_valuation(session, settings.quote_stale_after_seconds, strategy_run_id)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(payload, indent=2))


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


def _parse_date_option(option_name: str, value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise typer.BadParameter(f"{option_name} must be a valid ISO date or datetime string.") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _ensure_symbol_exists(session, symbol: str) -> None:
    if session.scalar(select(Symbol.id).where(Symbol.ticker == symbol)) is None:
        raise typer.BadParameter(f"Unknown symbol '{symbol}'. Import or seed market data before running a backtest.")


if __name__ == "__main__":
    app()
