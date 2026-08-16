from __future__ import annotations

from html import escape

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from tradeforge.database.models import Order, Position, StrategyRun, Symbol


def render_dashboard(session: Session, tenant_id: str | None) -> str:
    symbol_count = len(list(session.scalars(select(Symbol.id))))
    run_statement: Select[tuple[StrategyRun]] = select(StrategyRun).options(
        joinedload(StrategyRun.strategy), joinedload(StrategyRun.symbol)
    )
    position_statement: Select[tuple[Position]] = select(Position).options(joinedload(Position.symbol))
    order_statement: Select[tuple[Order]] = select(Order).options(joinedload(Order.symbol))
    if tenant_id is not None:
        run_statement = run_statement.where(StrategyRun.tenant_id == tenant_id)
        position_statement = position_statement.join(StrategyRun, Position.strategy_run_id == StrategyRun.id).where(
            StrategyRun.tenant_id == tenant_id
        )
        order_statement = order_statement.join(StrategyRun, Order.strategy_run_id == StrategyRun.id).where(
            StrategyRun.tenant_id == tenant_id
        )
    runs = list(session.scalars(run_statement.order_by(StrategyRun.started_at.desc()).limit(50)))
    positions = list(session.scalars(position_statement.order_by(Position.updated_at.desc()).limit(50)))
    orders = list(session.scalars(order_statement.order_by(Order.submitted_at.desc()).limit(50)))
    cards = _cards(symbol_count, len(positions), len(orders), len(runs))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>TradeForge Dashboard</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #172033; background: #f5f7fb; }}
    h1, h2 {{ color: #0b3d5c; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(10rem, 1fr)); gap: 1rem; }}
    .card, table {{ background: white; border: 1px solid #d6dfeb; border-radius: .5rem; }}
    .card {{ padding: 1rem; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
    th, td {{ text-align: left; padding: .65rem; border-bottom: 1px solid #e5ebf2; }}
    th {{ background: #eaf1f7; }}
  </style>
</head>
<body>
  <h1>TradeForge</h1>
  <p>Local paper trading research dashboard. Tenant: {escape(tenant_id or "authentication disabled")}</p>
  <div class="cards">{cards}</div>
  <h2>Positions</h2>
  {_position_table(positions)}
  <h2>Orders</h2>
  {_order_table(orders)}
  <h2>Strategy Runs</h2>
  {_run_table(runs)}
</body>
</html>"""


def _cards(symbols: int, positions: int, orders: int, runs: int) -> str:
    return "".join(
        f'<section class="card"><strong>{escape(label)}</strong><div>{value}</div></section>'
        for label, value in (("Symbols", symbols), ("Positions", positions), ("Orders", orders), ("Runs", runs))
    )


def _position_table(items: list[Position]) -> str:
    rows = "".join(
        f"<tr><td>{escape(item.symbol.ticker)}</td><td>{item.quantity:g}</td>"
        f"<td>{item.average_cost:.2f}</td><td>{item.realized_pnl:.2f}</td></tr>"
        for item in items
    )
    return f"<table><thead><tr><th>Symbol</th><th>Quantity</th><th>Average Cost</th><th>Realized P/L</th></tr></thead><tbody>{rows}</tbody></table>"


def _order_table(items: list[Order]) -> str:
    rows = "".join(
        f"<tr><td>{escape(item.symbol.ticker)}</td><td>{escape(item.side)}</td>"
        f"<td>{item.quantity:g}</td><td>{escape(item.status)}</td></tr>"
        for item in items
    )
    return f"<table><thead><tr><th>Symbol</th><th>Side</th><th>Quantity</th><th>Status</th></tr></thead><tbody>{rows}</tbody></table>"


def _run_table(items: list[StrategyRun]) -> str:
    rows = "".join(
        f"<tr><td>{escape(item.id)}</td><td>{escape(item.strategy.name)}</td>"
        f"<td>{escape(item.symbol.ticker)}</td><td>{escape(item.metrics_json or '{}')}</td></tr>"
        for item in items
    )
    return f"<table><thead><tr><th>ID</th><th>Strategy</th><th>Symbol</th><th>Metrics</th></tr></thead><tbody>{rows}</tbody></table>"
