from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from importlib.resources import as_file, files
from pathlib import Path
from typing import Optional, cast

import typer
import uvicorn
from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.analytics.advanced import advanced_analytics
from tradeforge.auth.service import create_api_key, create_tenant, revoke_api_key, rotate_api_key
from tradeforge.automation import (
    MaintenanceError,
    acknowledge_quarantined_import,
    build_local_health,
    run_disaster_recovery_drill,
    run_maintenance,
)
from tradeforge.automation.environment import inspect_environment, verify_lock_provenance
from tradeforge.backtesting.engine import BacktestEngine
from tradeforge.backtesting.performance import benchmark_vectorized_path
from tradeforge.backtesting.portfolio import AllocationRule, PortfolioBacktestEngine
from tradeforge.config import get_settings
from tradeforge.connectors.catalog import ConnectorCatalog
from tradeforge.corporate_actions import record_corporate_action
from tradeforge.database.migrations import (
    create_revision,
    get_current_version,
    get_head_version,
    init_db,
)
from tradeforge.database.models import APIKey, Experiment, LiveQuote, Order, Position, PriceBar, StrategyRun, Symbol
from tradeforge.database.session import session_scope
from tradeforge.market_data.importer import import_ohlcv_csv
from tradeforge.market_data.live import (
    QuoteProviderError,
    get_default_refresh_symbols,
    refresh_live_quotes,
    serialize_quote,
)
from tradeforge.plugins.registry import PluginKind, PluginRegistry, create_default_registry
from tradeforge.strategies.base import BaseStrategy
from tradeforge.telemetry import get_logger, log_event, setup_logging
from tradeforge.valuation.service import build_portfolio_valuation

app = typer.Typer(help="TradeForge local paper trading and backtesting CLI.")
setup_logging()
logger = get_logger(__name__)


@app.command("init-db")
def initialize_database() -> None:
    """Create the local SQLite schema."""
    init_db()
    log_event(
        logger,
        logging.INFO,
        "database_upgraded",
        current_version=get_current_version(),
        head_version=get_head_version(),
    )
    typer.echo("Initialized TradeForge database.")


@app.command("db-current")
def db_current() -> None:
    init_db()
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
    log_event(
        logger, logging.INFO, "database_revision_created", message_text=message, path=path, autogenerate=autogenerate
    )
    typer.echo(path)


@app.command("import-csv")
def import_csv(
    symbol: str = typer.Option(..., "--symbol", "-s"),
    file: Path = typer.Option(..., "--file", "-f", exists=True, file_okay=True, dir_okay=False),
) -> None:
    """Import OHLCV CSV data."""
    init_db()
    with session_scope() as session:
        count = import_ohlcv_csv(session, symbol, file)
    typer.echo(f"Imported {count} bars for {symbol.upper()}.")


@app.command("seed-sample-data")
def seed_sample_data(symbol: str = typer.Option("AAPL", "--symbol", "-s")) -> None:
    init_db()
    dataset = files("tradeforge.sample_data").joinpath("aapl_sample.csv")
    with as_file(dataset) as file_path, session_scope() as session:
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
    init_db()
    strategy_name = strategy.strip().lower()
    start_at = _parse_date_option("--start", start)
    end_at = _parse_date_option("--end", end)
    if start_at >= end_at:
        raise typer.BadParameter("The start date must be earlier than the end date.")
    normalized_symbol = symbol.strip().upper()
    try:
        strategy_obj = _build_strategy(strategy_name, short_window, long_window, order_size)
    except (KeyError, TypeError, ValueError) as exc:
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
    log_event(
        logger, logging.INFO, "backtest_completed", strategy_run_id=result["strategy_run_id"], metrics=result["metrics"]
    )
    typer.echo(json.dumps(result, indent=2))


@app.command("run-portfolio-backtest")
def run_portfolio_backtest(
    symbol: list[str] = typer.Option(..., "--symbol", "-s", help="Repeat for every portfolio symbol."),
    start: str = typer.Option(..., "--start"),
    end: str = typer.Option(..., "--end"),
    total_cash: float | None = typer.Option(None, "--total-cash"),
    allocation: AllocationRule = typer.Option(AllocationRule.EQUAL, "--allocation"),
    weights_json: str | None = typer.Option(None, "--weights-json"),
    short_window: int = typer.Option(20, "--short-window"),
    long_window: int = typer.Option(50, "--long-window"),
    order_size: float = typer.Option(10.0, "--order-size"),
) -> None:
    """Run allocated single-strategy backtests across multiple symbols."""
    init_db()
    start_at = _parse_date_option("--start", start)
    end_at = _parse_date_option("--end", end)
    if start_at >= end_at:
        raise typer.BadParameter("The start date must be earlier than the end date.")
    try:
        raw_weights = json.loads(weights_json) if weights_json is not None else None
        if raw_weights is not None and not isinstance(raw_weights, dict):
            raise ValueError("--weights-json must be a JSON object.")
        weights = cast(dict[str, float] | None, raw_weights)

        def strategy_factory() -> BaseStrategy:
            return _build_strategy("moving-average-cross", short_window, long_window, order_size)

        with session_scope() as session:
            for ticker in symbol:
                _ensure_symbol_exists(session, ticker.strip().upper())
            result = PortfolioBacktestEngine(
                session,
                strategy_factory,
                symbol,
                start_at,
                end_at,
                total_cash if total_cash is not None else get_settings().starting_cash,
                allocation_rule=allocation,
                weights=weights,
            ).run()
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(result, indent=2))


@app.command("list-plugins")
def list_plugins() -> None:
    """List built in and explicitly allowlisted entry point plugins."""
    registry = _configured_plugin_registry()
    typer.echo(
        json.dumps(
            [
                {"kind": item.kind.value, "name": item.name, "version": item.version, "source": item.source}
                for item in registry.list()
            ],
            indent=2,
        )
    )


@app.command("list-connectors")
def list_connectors() -> None:
    """List read only and paper signal connector adapters."""
    typer.echo(
        json.dumps(
            [
                {
                    "name": item.name,
                    "transport": item.transport,
                    "capabilities": item.capabilities,
                    "live_order_routing": item.live_order_routing,
                }
                for item in ConnectorCatalog().list()
            ],
            indent=2,
        )
    )


@app.command("analyze-symbol")
def analyze_symbol(
    symbol: str = typer.Option(..., "--symbol"),
    benchmark_symbol: str | None = typer.Option(None, "--benchmark-symbol"),
    window: int = typer.Option(20, "--window"),
) -> None:
    """Calculate rolling risk, beta, and market regimes for stored bars."""
    init_db()
    with session_scope() as session:
        asset_series = _load_close_series(session, symbol)
        if benchmark_symbol is None:
            prices = [close for _, close in asset_series]
            benchmark_prices = None
        else:
            benchmark_series = _load_close_series(session, benchmark_symbol)
            prices, benchmark_prices = _align_close_series(asset_series, benchmark_series, symbol, benchmark_symbol)
    try:
        payload = advanced_analytics(prices, benchmark_prices, window=window)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(payload, indent=2))


@app.command("benchmark-performance")
def benchmark_performance(
    rows: int = typer.Option(25_000, "--rows", min=100),
    maximum_seconds: float = typer.Option(2.0, "--maximum-seconds", min=0.01),
) -> None:
    """Enforce the vectorized moving average performance budget."""
    prices = [100 + (index % 100) * 0.1 for index in range(rows)]
    try:
        payload = benchmark_vectorized_path(prices, 20, 50, maximum_seconds)
    except (RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(payload, indent=2))


@app.command("refresh-quotes")
def refresh_quotes(
    symbol: list[str] = typer.Option(None, "--symbol", "-s", help="Repeat to refresh specific symbols."),
) -> None:
    """Refresh latest quotes for open positions or the requested symbols."""
    init_db()
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


@app.command("run-dr-drill")
def run_dr_drill() -> None:
    """Restore the latest backup and evaluate recovery objectives."""
    try:
        result = run_disaster_recovery_drill()
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(result, indent=2))
    if not result["objectives_met"]:
        raise typer.Exit(code=1)


@app.command("create-tenant")
def create_tenant_command(name: str = typer.Option(..., "--name")) -> None:
    """Create an isolated API and research tenant."""
    init_db()
    try:
        with session_scope() as session:
            tenant = create_tenant(session, name)
            payload = {"id": tenant.id, "name": tenant.name}
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(payload, indent=2))


@app.command("create-api-key")
def create_api_key_command(
    tenant_id: str = typer.Option(..., "--tenant-id"),
    name: str = typer.Option(..., "--name"),
    role: str = typer.Option("viewer", "--role"),
    expires_in_days: int | None = typer.Option(None, "--expires-in-days", min=1),
) -> None:
    """Create a least privilege API service identity and print its secret once."""
    init_db()
    expiration = (
        datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        if expires_in_days is not None
        else datetime.now(timezone.utc) + timedelta(days=get_settings().api_key_rotation_days)
    )
    try:
        with session_scope() as session:
            api_key, secret = create_api_key(session, tenant_id, name, role, expiration)
            payload = {
                "id": api_key.id,
                "tenant_id": api_key.tenant_id,
                "role": api_key.role,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at is not None else None,
                "api_key": secret,
            }
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(payload, indent=2))


@app.command("rotate-api-key")
def rotate_api_key_command(
    api_key_id: str = typer.Option(..., "--api-key-id"),
    expires_in_days: int | None = typer.Option(None, "--expires-in-days", min=1),
) -> None:
    """Revoke one API key and issue a replacement secret."""
    init_db()
    days = expires_in_days or get_settings().api_key_rotation_days
    try:
        with session_scope() as session:
            api_key, secret = rotate_api_key(
                session,
                api_key_id,
                datetime.now(timezone.utc) + timedelta(days=days),
            )
            payload = {
                "id": api_key.id,
                "tenant_id": api_key.tenant_id,
                "role": api_key.role,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at is not None else None,
                "api_key": secret,
            }
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(payload, indent=2))


@app.command("revoke-api-key")
def revoke_api_key_command(api_key_id: str = typer.Option(..., "--api-key-id")) -> None:
    """Revoke an API service identity immediately."""
    init_db()
    try:
        with session_scope() as session:
            api_key = revoke_api_key(session, api_key_id)
            revoked_at = api_key.revoked_at.isoformat() if api_key.revoked_at is not None else None
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps({"id": api_key_id, "revoked_at": revoked_at}, indent=2))


@app.command("show-api-keys")
def show_api_keys(tenant_id: str | None = typer.Option(None, "--tenant-id")) -> None:
    """Show API key metadata without secret values."""
    init_db()
    with session_scope() as session:
        statement = select(APIKey).order_by(APIKey.created_at.desc())
        if tenant_id is not None:
            statement = statement.where(APIKey.tenant_id == tenant_id)
        payload = [
            {
                "id": item.id,
                "tenant_id": item.tenant_id,
                "name": item.name,
                "role": item.role,
                "expires_at": item.expires_at.isoformat() if item.expires_at is not None else None,
                "revoked_at": item.revoked_at.isoformat() if item.revoked_at is not None else None,
            }
            for item in session.scalars(statement)
        ]
    typer.echo(json.dumps(payload, indent=2))


@app.command("show-experiments")
def show_experiments(tenant_id: str | None = typer.Option(None, "--tenant-id")) -> None:
    """Show immutable strategy experiment metadata and dataset checksums."""
    init_db()
    with session_scope() as session:
        statement = select(Experiment).order_by(Experiment.created_at.desc())
        if tenant_id is not None:
            statement = statement.where(Experiment.tenant_id == tenant_id)
        payload = [
            {
                "id": item.id,
                "tenant_id": item.tenant_id,
                "strategy_run_id": item.strategy_run_id,
                "strategy_version": item.strategy_version,
                "dataset_sha256": item.dataset_sha256,
                "created_at": item.created_at.isoformat(),
            }
            for item in session.scalars(statement)
        ]
    typer.echo(json.dumps(payload, indent=2))


@app.command("record-corporate-action")
def record_corporate_action_command(
    symbol: str = typer.Option(..., "--symbol"),
    action_type: str = typer.Option(..., "--type"),
    effective_at: str = typer.Option(..., "--effective-at"),
    ratio: float | None = typer.Option(None, "--ratio"),
    cash_amount: float | None = typer.Option(None, "--cash-amount"),
    new_ticker: str | None = typer.Option(None, "--new-ticker"),
) -> None:
    """Record a split, dividend, symbol change, or delisting."""
    init_db()
    try:
        effective = _parse_date_option("--effective-at", effective_at)
        with session_scope() as session:
            action = record_corporate_action(
                session,
                symbol,
                action_type,
                effective,
                ratio=ratio,
                cash_amount=cash_amount,
                new_ticker=new_ticker,
            )
            action_id = action.id
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(action_id)


@app.command("acknowledge-import")
def acknowledge_import(
    filename: str = typer.Option(..., "--file"),
    retry: bool = typer.Option(False, "--retry", help="Move the quarantined file back to the pending queue."),
) -> None:
    """Acknowledge a quarantined import and optionally retry it."""
    try:
        destination = acknowledge_quarantined_import(get_settings(), filename, retry)
    except (FileNotFoundError, FileExistsError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(str(destination))


@app.command("health")
def health() -> None:
    """Report local database, backup, import, and maintenance health."""
    payload = build_local_health()
    typer.echo(json.dumps(payload, indent=2))
    if payload["status"] != "healthy":
        raise typer.Exit(code=1)


@app.command("doctor")
def doctor(
    lock_file: Path = typer.Option(Path("requirements.lock"), "--lock-file"),
    provenance_file: Path = typer.Option(Path("requirements.lock.provenance.json"), "--provenance-file"),
) -> None:
    """Report undeclared or version drifted packages and verify lock provenance."""
    environment = inspect_environment(lock_file)
    try:
        provenance = verify_lock_provenance(lock_file, provenance_file)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        provenance = {"status": "invalid", "error": str(exc)}
    payload = {"environment": environment, "provenance": provenance}
    typer.echo(json.dumps(payload, indent=2))
    if environment["status"] != "healthy" or provenance["status"] != "verified":
        raise typer.Exit(code=1)


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
    init_db()
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
    init_db()
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
    init_db()
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
    init_db()
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
    init_db()
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


def _ensure_symbol_exists(session: Session, symbol: str) -> None:
    if session.scalar(select(Symbol.id).where(Symbol.ticker == symbol)) is None:
        raise typer.BadParameter(f"Unknown symbol '{symbol}'. Import or seed market data before running a backtest.")


def _build_strategy(strategy_name: str, short_window: int, long_window: int, order_size: float) -> BaseStrategy:
    plugin = _configured_plugin_registry().get(PluginKind.STRATEGY, strategy_name)
    factory = cast(Callable[..., object], plugin)
    strategy = factory(short_window=short_window, long_window=long_window, order_size=order_size)
    if not isinstance(strategy, BaseStrategy):
        raise TypeError(f"Strategy plugin did not return BaseStrategy: {strategy_name}")
    return strategy


def _configured_plugin_registry() -> PluginRegistry:
    registry = create_default_registry()
    try:
        allowlist = json.loads(get_settings().plugin_allowlist_json)
    except json.JSONDecodeError as exc:
        raise ValueError("TRADEFORGE_PLUGIN_ALLOWLIST_JSON must contain valid JSON.") from exc
    if not isinstance(allowlist, list) or any(not isinstance(name, str) for name in allowlist):
        raise ValueError("TRADEFORGE_PLUGIN_ALLOWLIST_JSON must be a JSON list of plugin names.")
    registry.discover(set(allowlist))
    return registry


def _load_close_series(session: Session, symbol: str) -> list[tuple[datetime, float]]:
    normalized = symbol.strip().upper()
    _ensure_symbol_exists(session, normalized)
    values = [
        (timestamp, close)
        for timestamp, close in session.execute(
            select(PriceBar.timestamp, PriceBar.close)
            .join(Symbol, PriceBar.symbol_id == Symbol.id)
            .where(Symbol.ticker == normalized)
            .order_by(PriceBar.timestamp.asc())
        )
    ]
    if len(values) < 2:
        raise typer.BadParameter(f"Symbol '{normalized}' needs at least two bars for analytics.")
    return values


def _align_close_series(
    asset: list[tuple[datetime, float]],
    benchmark: list[tuple[datetime, float]],
    asset_symbol: str,
    benchmark_symbol: str,
) -> tuple[list[float], list[float]]:
    asset_by_timestamp = dict(asset)
    benchmark_by_timestamp = dict(benchmark)
    timestamps = sorted(asset_by_timestamp.keys() & benchmark_by_timestamp.keys())
    if len(timestamps) < 2:
        raise typer.BadParameter(
            f"Symbols '{asset_symbol.strip().upper()}' and '{benchmark_symbol.strip().upper()}' "
            "need at least two matching bar timestamps for beta."
        )
    return (
        [asset_by_timestamp[timestamp] for timestamp in timestamps],
        [benchmark_by_timestamp[timestamp] for timestamp in timestamps],
    )


if __name__ == "__main__":
    app()
