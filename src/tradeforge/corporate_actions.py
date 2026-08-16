from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.broker_sim.account import SimAccount
from tradeforge.database.models import (
    CorporateAction,
    ExecutionAuditEvent,
    Order,
    OrderStatus,
    Position,
    Symbol,
    Trade,
)

SUPPORTED_ACTIONS = {"split", "dividend", "symbol_change", "delisting"}


def record_corporate_action(
    session: Session,
    ticker: str,
    action_type: str,
    effective_at: datetime,
    *,
    ratio: float | None = None,
    cash_amount: float | None = None,
    new_ticker: str | None = None,
) -> CorporateAction:
    normalized_type = action_type.strip().lower()
    if normalized_type not in SUPPORTED_ACTIONS:
        raise ValueError(f"Unsupported corporate action: {action_type}")
    symbol = session.scalar(select(Symbol).where(Symbol.ticker == ticker.strip().upper()))
    if symbol is None:
        raise ValueError(f"Unknown symbol: {ticker}")
    if normalized_type == "split" and (ratio is None or ratio <= 0):
        raise ValueError("Split actions require a positive ratio")
    if normalized_type == "dividend" and (cash_amount is None or cash_amount < 0):
        raise ValueError("Dividend actions require a nonnegative cash amount")
    if normalized_type == "symbol_change" and not (new_ticker or "").strip():
        raise ValueError("Symbol change actions require a new ticker")
    action = CorporateAction(
        symbol_id=symbol.id,
        action_type=normalized_type,
        effective_at=_ensure_utc(effective_at),
        ratio=ratio,
        cash_amount=cash_amount,
        new_ticker=None if new_ticker is None else new_ticker.strip().upper(),
    )
    session.add(action)
    session.flush()
    return action


def apply_corporate_action(
    session: Session,
    account: SimAccount,
    position: Position,
    action: CorporateAction,
    *,
    strategy_run_id: str | None,
    mark_applied: bool = False,
) -> None:
    payload: dict[str, object] = {"corporate_action_id": action.id, "action_type": action.action_type}
    if action.action_type == "split":
        ratio = action.ratio
        if ratio is None or ratio <= 0:
            raise ValueError("Split action requires a positive ratio")
        position.quantity *= ratio
        if position.average_cost:
            position.average_cost /= ratio
        adjusted_orders = list(
            session.scalars(
                select(Order).where(
                    Order.strategy_run_id == strategy_run_id,
                    Order.symbol_id == action.symbol_id,
                    Order.status.in_([OrderStatus.OPEN.value, OrderStatus.PARTIALLY_FILLED.value]),
                )
            )
        )
        for order in adjusted_orders:
            order.quantity *= ratio
            order.filled_quantity *= ratio
            if order.limit_price is not None:
                order.limit_price /= ratio
            if order.stop_price is not None:
                order.stop_price /= ratio
        payload["ratio"] = ratio
        payload["adjusted_order_count"] = len(adjusted_orders)
    elif action.action_type == "dividend":
        cash_credit = position.quantity * (action.cash_amount or 0.0)
        account.cash += cash_credit
        payload["cash_credit"] = cash_credit
    elif action.action_type == "symbol_change":
        if action.new_ticker is None:
            raise ValueError("Symbol change action has no new ticker")
        action.symbol.ticker = action.new_ticker
        payload["new_ticker"] = action.new_ticker
    elif action.action_type == "delisting":
        liquidation_price = 0.0 if action.cash_amount is None else action.cash_amount
        if liquidation_price < 0:
            raise ValueError("Delisting liquidation price must be nonnegative")
        liquidation_quantity = max(position.quantity, 0.0)
        realized_pnl = (liquidation_price - position.average_cost) * liquidation_quantity
        account.cash += liquidation_quantity * liquidation_price
        position.realized_pnl += realized_pnl
        _close_open_trade_for_delisting(
            session,
            position,
            liquidation_quantity,
            liquidation_price,
            realized_pnl,
            action.effective_at,
        )
        position.quantity = 0.0
        position.average_cost = 0.0
        action.symbol.is_active = False
        payload["liquidation_price"] = liquidation_price
        payload["liquidation_quantity"] = liquidation_quantity
        payload["realized_pnl"] = realized_pnl
    else:
        raise ValueError(f"Unsupported corporate action: {action.action_type}")

    session.add(
        ExecutionAuditEvent(
            strategy_run_id=strategy_run_id,
            symbol_id=action.symbol_id,
            timestamp=action.effective_at,
            event_type="corporate_action",
            payload_json=json.dumps(payload, sort_keys=True),
        )
    )
    if mark_applied:
        action.applied_at = datetime.now(timezone.utc)
    session.flush()


def _close_open_trade_for_delisting(
    session: Session,
    position: Position,
    liquidation_quantity: float,
    liquidation_price: float,
    realized_pnl: float,
    effective_at: datetime,
) -> None:
    trade = session.scalar(
        select(Trade)
        .where(
            Trade.strategy_run_id == position.strategy_run_id,
            Trade.symbol_id == position.symbol_id,
            Trade.closed_at.is_(None),
        )
        .order_by(Trade.opened_at.asc())
    )
    if trade is None:
        return
    previous_closed_quantity = max(trade.quantity - liquidation_quantity, 0.0)
    if liquidation_quantity > 0:
        if previous_closed_quantity > 0 and trade.exit_price is not None:
            trade.exit_price = (
                trade.exit_price * previous_closed_quantity + liquidation_price * liquidation_quantity
            ) / trade.quantity
        else:
            trade.exit_price = liquidation_price
    trade.realized_pnl += realized_pnl
    trade.closed_at = effective_at


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
