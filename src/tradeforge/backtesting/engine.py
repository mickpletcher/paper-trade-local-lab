from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.backtesting.metrics import calculate_metrics
from tradeforge.broker_sim.account import SimAccount
from tradeforge.broker_sim.execution import SimBroker
from tradeforge.broker_sim.orders import OrderRequest
from tradeforge.broker_sim.portfolio import get_or_create_position
from tradeforge.config import get_settings
from tradeforge.database.models import AccountSnapshot, Fill, Position, PriceBar, Strategy, StrategyRun, Symbol, Trade
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
        self.starting_cash = starting_cash if starting_cash is not None else settings.starting_cash
        self.fee_per_order = settings.fee_per_order
        self.slippage_bps = settings.slippage_bps

    def run(self) -> dict[str, object]:
        symbol = self.session.scalar(select(Symbol).where(Symbol.ticker == self.symbol_ticker))
        if symbol is None:
            raise ValueError(f"Unknown symbol: {self.symbol_ticker}")
        bars = list(
            self.session.scalars(
                select(PriceBar)
                .where(PriceBar.symbol_id == symbol.id, PriceBar.timestamp >= self.start, PriceBar.timestamp <= self.end)
                .order_by(PriceBar.timestamp.asc())
            )
        )
        if len(bars) < 2:
            raise ValueError("Backtest requires at least two price bars")

        strategy_model = self._get_or_create_strategy()
        parameters = {
            key: value
            for key, value in vars(self.strategy).items()
            if isinstance(value, (str, int, float, bool)) and key != "name"
        }
        run = StrategyRun(
            strategy_id=strategy_model.id,
            symbol_id=symbol.id,
            start_date=self.start,
            end_date=self.end,
            parameters_json=json.dumps(parameters),
        )
        self.session.add(run)
        self.session.flush()

        account = SimAccount.with_starting_cash(self.starting_cash)
        broker = SimBroker(self.session, account, self.fee_per_order, self.slippage_bps)
        history: list[PriceBar] = []
        snapshots: list[AccountSnapshot] = []

        for bar in bars:
            broker.process_bar(bar)
            position = get_or_create_position(self.session, symbol.id, run.id)
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
            signal = self.strategy.on_bar(bar, StrategyContext(bars=history, has_position=position.quantity > 0))
            if signal is not None:
                broker.submit_order(
                    OrderRequest(
                        symbol_id=symbol.id,
                        strategy_run_id=run.id,
                        side=signal.side,
                        order_type=signal.order_type,
                        quantity=signal.quantity,
                        limit_price=signal.limit_price,
                    ),
                    submitted_at=bar.timestamp,
                )

        broker.process_bar(bars[-1])
        position = get_or_create_position(self.session, symbol.id, run.id)
        ending_equity = account.cash + position.quantity * bars[-1].close
        fills = list(self.session.scalars(select(Fill).where(Fill.strategy_run_id == run.id)))
        trades = list(self.session.scalars(select(Trade).where(Trade.strategy_run_id == run.id)))
        metrics = calculate_metrics(self.starting_cash, ending_equity, fills, trades, position, snapshots, bars[-1].close)
        run.completed_at = datetime.now(timezone.utc)
        run.metrics_json = json.dumps(metrics)
        self.session.flush()
        positions = list(self.session.scalars(select(Position).where(Position.strategy_run_id == run.id)))
        report_path = write_markdown_report(run, parameters, metrics, trades, positions)
        self.session.commit()
        return {"strategy_run_id": run.id, "metrics": metrics, "report_path": str(report_path)}

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
