from __future__ import annotations

import json

from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from tradeforge.config import get_settings
from tradeforge.database.migrations import init_db
from tradeforge.database.models import LiveQuote, Order, Position, StrategyRun, Symbol
from tradeforge.database.session import session_scope
from tradeforge.market_data.live import serialize_quote
from tradeforge.valuation.service import build_portfolio_valuation

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
    "/quotes",
    summary="List latest live quotes",
    responses={
        200: {
            "description": "Latest live quotes used for local valuation.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "symbol": "AAPL",
                            "provider": "alpaca",
                            "quote_timestamp": "2026-05-12T20:15:00Z",
                            "fetched_at": "2026-05-12T20:15:01Z",
                            "last_price": 188.61,
                            "bid_price": 188.6,
                            "ask_price": 188.62,
                            "mark_price": 188.61,
                            "previous_close": 187.12,
                            "currency": "USD",
                            "age_seconds": 1,
                            "is_stale": False,
                        }
                    ]
                }
            },
        }
    },
)
def quotes() -> list[dict[str, object]]:
    init_db()
    settings = get_settings()
    with session_scope() as session:
        items = session.scalars(select(LiveQuote).options(selectinload(LiveQuote.symbol)).order_by(LiveQuote.fetched_at.desc())).all()
        return [serialize_quote(item, settings.quote_stale_after_seconds) for item in items]


@app.get(
    "/portfolio",
    summary="Show current local portfolio valuation",
    responses={
        200: {
            "description": "Local position valuation using the latest stored quotes.",
            "content": {
                "application/json": {
                    "example": {
                        "cash": 9975.98,
                        "market_value": 377.22,
                        "total_equity": 10353.2,
                        "unrealized_pnl": 6.4,
                        "positions_count": 1,
                        "stale_quotes": 0,
                        "positions": [
                            {
                                "symbol": "AAPL",
                                "strategy_run_id": "61d7e6bf-2bf7-41ad-a5da-7f4ac01f2201",
                                "quantity": 2.0,
                                "average_cost": 185.41,
                                "realized_pnl": 0.0,
                                "quote_provider": "alpaca",
                                "quote_timestamp": "2026-05-12T20:15:00Z",
                                "fetched_at": "2026-05-12T20:15:01Z",
                                "age_seconds": 1,
                                "is_stale": False,
                                "mark_price": 188.61,
                                "market_value": 377.22,
                                "unrealized_pnl": 6.4,
                            }
                        ],
                    }
                }
            },
        }
    },
)
def portfolio() -> dict[str, object]:
    init_db()
    settings = get_settings()
    with session_scope() as session:
        return build_portfolio_valuation(session, settings.quote_stale_after_seconds)


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
