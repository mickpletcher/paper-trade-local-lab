from __future__ import annotations

import json

from fastapi import FastAPI
from sqlalchemy import select

from tradeforge.database.migrations import init_db
from tradeforge.database.models import Order, Position, StrategyRun, Symbol
from tradeforge.database.session import session_scope

app = FastAPI(title="TradeForge API", version="0.1.0")


@app.get(
    "/health",
    summary="Service health",
    responses={
        200: {
            "description": "Basic service health response.",
            "content": {"application/json": {"example": {"status": "ok"}}},
        }
    },
)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get(
    "/symbols",
    summary="List imported symbols",
    responses={
        200: {
            "description": "Imported symbols available in the local database.",
            "content": {
                "application/json": {
                    "example": [{"id": "9a4d3fcb-98c5-4a18-9dd6-7dfbaed7f001", "ticker": "AAPL", "name": ""}]
                }
            },
        }
    },
)
def symbols() -> list[dict[str, str]]:
    init_db()
    with session_scope() as session:
        return [{"id": item.id, "ticker": item.ticker, "name": item.name or ""} for item in session.scalars(select(Symbol))]


@app.get(
    "/positions",
    summary="List current simulated positions",
    responses={
        200: {
            "description": "Current local paper positions.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "1736d089-5028-40f6-b753-f3fcba74a201",
                            "symbol": "AAPL",
                            "quantity": 2.0,
                            "average_cost": 12.01,
                            "realized_pnl": 0.0,
                        }
                    ]
                }
            },
        }
    },
)
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


@app.get(
    "/orders",
    summary="List simulated orders",
    responses={
        200: {
            "description": "Stored local simulated orders.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "f4b9d3cb-d8f5-4c4d-a9bb-1828d9722001",
                            "symbol": "AAPL",
                            "side": "buy",
                            "order_type": "market",
                            "quantity": 2.0,
                            "status": "filled",
                        }
                    ]
                }
            },
        }
    },
)
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


@app.get(
    "/strategy-runs",
    summary="List strategy runs",
    responses={
        200: {
            "description": "Completed or in progress local backtest runs.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "61d7e6bf-2bf7-41ad-a5da-7f4ac01f2201",
                            "strategy": "moving-average-cross",
                            "symbol": "AAPL",
                            "started_at": "2026-05-12T20:10:00Z",
                            "completed_at": "2026-05-12T20:10:02Z",
                            "metrics": {
                                "starting_cash": 100000.0,
                                "ending_equity": 100001.98,
                                "total_return": 0.00002,
                            },
                        }
                    ]
                }
            },
        }
    },
)
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
