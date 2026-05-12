from __future__ import annotations

import json

from fastapi import FastAPI
from sqlalchemy import select

from tradeforge.database.migrations import init_db
from tradeforge.database.models import Order, Position, StrategyRun, Symbol
from tradeforge.database.session import session_scope

app = FastAPI(title="TradeForge API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/symbols")
def symbols() -> list[dict[str, str]]:
    init_db()
    with session_scope() as session:
        return [{"id": item.id, "ticker": item.ticker, "name": item.name or ""} for item in session.scalars(select(Symbol))]


@app.get("/positions")
def positions() -> list[dict[str, object]]:
    init_db()
    with session_scope() as session:
        return [
            {
                "id": item.id,
                "symbol": item.symbol.ticker,
                "quantity": item.quantity,
                "average_cost": item.average_cost,
                "realized_pnl": item.realized_pnl,
            }
            for item in session.scalars(select(Position))
        ]


@app.get("/orders")
def orders() -> list[dict[str, object]]:
    init_db()
    with session_scope() as session:
        return [
            {
                "id": item.id,
                "symbol": item.symbol.ticker,
                "side": item.side,
                "order_type": item.order_type,
                "quantity": item.quantity,
                "status": item.status,
            }
            for item in session.scalars(select(Order))
        ]


@app.get("/strategy-runs")
def strategy_runs() -> list[dict[str, object]]:
    init_db()
    with session_scope() as session:
        return [
            {
                "id": item.id,
                "strategy": item.strategy.name,
                "symbol": item.symbol.ticker,
                "started_at": item.started_at,
                "completed_at": item.completed_at,
                "metrics": json.loads(item.metrics_json or "{}"),
            }
            for item in session.scalars(select(StrategyRun))
        ]
