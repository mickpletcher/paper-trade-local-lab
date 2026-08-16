from __future__ import annotations

import json
from datetime import datetime, timezone
from math import isfinite

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.backtesting.metrics import calculate_metrics
from tradeforge.broker_sim.account import SimAccount
from tradeforge.broker_sim.execution import FixedCommissionModel, PerShareCommissionModel, SimBroker
from tradeforge.broker_sim.orders import OrderRequest
from tradeforge.broker_sim.portfolio import get_or_create_position
from tradeforge.broker_sim.risk import RiskEngine, RiskLimits
from tradeforge.config import Settings, get_settings
from tradeforge.corporate_actions import apply_corporate_action
from tradeforge.database.models import (
    AccountSnapshot,
    CorporateAction,
    Fill,
    OrderSide,
    Position,
    PriceBar,
    Strategy,
    StrategyRun,
    Symbol,
    Trade,
)
from tradeforge.experiments.service import track_strategy_run
from tradeforge.reporting.reports import write_markdown_report
from tradeforge.strategies.base import BaseStrategy, StrategyContext


class BacktestEngine:
    def __init__(
        self,
        session: Session,
        strategy: BaseStrategy,
        symbol: str,
        start: datetime,
        end: datetime,
        starting_cash: float | None = None,
    ):
        settings = get_settings()
        self.session = session
        self.strategy = strategy
        self.symbol_ticker = symbol.upper()
        self.start = _ensure_utc(start)
        self.end = _ensure_utc(end)
        self.tenant_id = settings.default_tenant_id
        self.starting_cash = starting_cash if starting_cash is not None else settings.starting_cash
        self.commission_model = _build_commission_model(settings)
        self.default_slippage_bps = settings.slippage_bps
        self.symbol_slippage_rules = _parse_symbol_slippage_rules(settings.symbol_slippage_rules_json)
        self.max_bar_fill_ratio = settings.max_bar_fill_ratio
        self.quantity_increment = settings.quantity_increment
        self.risk_limits = RiskLimits(
            max_order_notional=settings.risk_max_order_notional,
            max_position_quantity=settings.risk_max_position_quantity,
            max_gross_exposure=settings.risk_max_gross_exposure,
            max_drawdown_ratio=settings.risk_max_drawdown_ratio,
            kill_switch=settings.risk_kill_switch,
        )

    def run(self) -> dict[str, object]:
        symbol = self.session.scalar(select(Symbol).where(Symbol.ticker == self.symbol_ticker))
        if symbol is None:
            raise ValueError(f"Unknown symbol: {self.symbol_ticker}")
        bars = list(
            self.session.scalars(
                select(PriceBar)
                .where(
                    PriceBar.symbol_id == symbol.id, PriceBar.timestamp >= self.start, PriceBar.timestamp <= self.end
                )
                .order_by(PriceBar.timestamp.asc())
            )
        )
        if len(bars) < 2:
            raise ValueError("Backtest requires at least two price bars")

        strategy_model = self._get_or_create_strategy()
        parameters: dict[str, object] = {
            key: value
            for key, value in vars(self.strategy).items()
            if isinstance(value, (str, int, float, bool)) and key != "name"
        }
        parameters["execution"] = {
            "commission": _commission_parameters(self.commission_model),
            "default_slippage_bps": self.default_slippage_bps,
            "symbol_slippage_rules": self.symbol_slippage_rules,
            "max_bar_fill_ratio": self.max_bar_fill_ratio,
            "quantity_increment": self.quantity_increment,
        }
        run = StrategyRun(
            tenant_id=self.tenant_id,
            strategy_id=strategy_model.id,
            symbol_id=symbol.id,
            start_date=self.start,
            end_date=self.end,
            parameters_json=json.dumps(parameters),
        )
        self.session.add(run)
        self.session.flush()

        account = SimAccount.with_starting_cash(self.starting_cash)
        risk_engine = RiskEngine(
            self.session,
            account,
            self.risk_limits,
            run.id,
        )
        broker = SimBroker(
            self.session,
            account,
            commission_model=self.commission_model,
            default_slippage_bps=self.default_slippage_bps,
            symbol_slippage_rules=self.symbol_slippage_rules,
            max_bar_fill_ratio=self.max_bar_fill_ratio,
            quantity_increment=self.quantity_increment,
            strategy_run_id=run.id,
            risk_engine=risk_engine,
        )
        history: list[PriceBar] = []
        snapshots: list[AccountSnapshot] = []
        actions = list(
            self.session.scalars(
                select(CorporateAction)
                .where(
                    CorporateAction.symbol_id == symbol.id,
                    CorporateAction.effective_at >= self.start,
                    CorporateAction.effective_at <= self.end,
                )
                .order_by(CorporateAction.effective_at.asc())
            )
        )
        action_cursor = 0

        for bar in bars:
            position = get_or_create_position(self.session, symbol.id, run.id)
            while action_cursor < len(actions) and actions[action_cursor].effective_at <= bar.timestamp:
                apply_corporate_action(
                    self.session,
                    account,
                    position,
                    actions[action_cursor],
                    strategy_run_id=run.id,
                )
                action_cursor += 1
            if symbol.is_active:
                broker.process_bar(bar)
            else:
                broker.cancel_open_orders(symbol_id=symbol.id)
            equity = account.cash + position.quantity * bar.close
            unrealized = (bar.close - position.average_cost) * position.quantity if position.quantity else 0.0
            snapshot = AccountSnapshot(
                strategy_run_id=run.id,
                timestamp=bar.timestamp,
                cash=account.cash,
                equity=equity,
                realized_pnl=position.realized_pnl,
                unrealized_pnl=unrealized,
            )
            self.session.add(snapshot)
            snapshots.append(snapshot)

            history.append(bar)
            if not symbol.is_active:
                continue
            pending = broker.get_pending_quantities(symbol.id)
            context = StrategyContext(
                bars=history,
                position_quantity=position.quantity,
                pending_buy_quantity=pending[OrderSide.BUY],
                pending_sell_quantity=pending[OrderSide.SELL],
            )
            for cancellation_side in self.strategy.get_order_cancellations(bar, context):
                broker.cancel_open_orders(symbol_id=symbol.id, side=cancellation_side)
            signal = self.strategy.on_bar(
                bar,
                context,
            )
            if signal is not None:
                opposite_side = OrderSide.SELL if signal.side is OrderSide.BUY else OrderSide.BUY
                broker.cancel_open_orders(symbol_id=symbol.id, side=opposite_side)
                broker.submit_order(
                    OrderRequest(
                        symbol_id=symbol.id,
                        strategy_run_id=run.id,
                        side=signal.side,
                        order_type=signal.order_type,
                        quantity=signal.quantity,
                        limit_price=signal.limit_price,
                        stop_price=signal.stop_price,
                    ),
                    submitted_at=bar.timestamp,
                )

        broker.cancel_open_orders(symbol_id=symbol.id)
        position = get_or_create_position(self.session, symbol.id, run.id)
        ending_equity = account.cash + position.quantity * bars[-1].close
        fills = list(self.session.scalars(select(Fill).where(Fill.strategy_run_id == run.id)))
        trades = list(self.session.scalars(select(Trade).where(Trade.strategy_run_id == run.id)))
        metrics = calculate_metrics(
            self.starting_cash,
            ending_equity,
            fills,
            trades,
            position,
            snapshots,
            bars[0].close,
            bars[-1].close,
        )
        run.completed_at = datetime.now(timezone.utc)
        run.metrics_json = json.dumps(metrics)
        self.session.flush()
        positions = list(self.session.scalars(select(Position).where(Position.strategy_run_id == run.id)))
        report_path = write_markdown_report(run, parameters, metrics, trades, positions)
        experiment = track_strategy_run(self.session, run.id, "builtin-1", {"report": report_path})
        self.session.commit()
        return {
            "strategy_run_id": run.id,
            "experiment_id": experiment.id,
            "metrics": metrics,
            "report_path": str(report_path),
        }

    def _get_or_create_strategy(self) -> Strategy:
        strategy = self.session.scalar(select(Strategy).where(Strategy.name == self.strategy.name))
        if strategy is not None:
            return strategy
        strategy = Strategy(name=self.strategy.name, description=self.strategy.__class__.__name__)
        self.session.add(strategy)
        self.session.flush()
        return strategy


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _build_commission_model(settings: Settings) -> FixedCommissionModel | PerShareCommissionModel:
    model_name = settings.commission_model.strip().lower()
    if model_name == "per_share":
        return PerShareCommissionModel(
            rate_per_share=settings.commission_per_share, minimum_fee=settings.commission_minimum
        )
    if model_name == "fixed":
        return FixedCommissionModel(fee_per_order=settings.fee_per_order)
    raise ValueError("TRADEFORGE_COMMISSION_MODEL must be 'fixed' or 'per_share'.")


def _commission_parameters(model: FixedCommissionModel | PerShareCommissionModel) -> dict[str, float | str]:
    if isinstance(model, PerShareCommissionModel):
        return {
            "model": "per_share",
            "rate_per_share": model.rate_per_share,
            "minimum_fee": model.minimum_fee,
        }
    return {"model": "fixed", "fee_per_order": model.fee_per_order}


def _parse_symbol_slippage_rules(raw_rules: str) -> dict[str, float]:
    try:
        payload = json.loads(raw_rules or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError("TRADEFORGE_SYMBOL_SLIPPAGE_RULES_JSON must contain valid JSON.") from exc
    if not isinstance(payload, dict):
        raise ValueError("TRADEFORGE_SYMBOL_SLIPPAGE_RULES_JSON must be a JSON object keyed by ticker.")
    rules: dict[str, float] = {}
    for symbol, raw_bps in payload.items():
        ticker = str(symbol).strip().upper()
        if not ticker:
            raise ValueError("TRADEFORGE_SYMBOL_SLIPPAGE_RULES_JSON cannot contain an empty ticker.")
        try:
            bps = float(raw_bps)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Slippage for {ticker} must be numeric.") from exc
        if not isfinite(bps) or not 0 <= bps < 10_000:
            raise ValueError(f"Slippage for {ticker} must be between 0 and 10000 basis points.")
        rules[ticker] = bps
    return rules
