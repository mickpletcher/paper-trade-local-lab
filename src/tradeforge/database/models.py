from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uuid_str() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"


class OrderStatus(str, Enum):
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Symbol(Base):
    __tablename__ = "symbols"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    ticker: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    price_bars: Mapped[list["PriceBar"]] = relationship(back_populates="symbol")
    live_quotes: Mapped[list["LiveQuote"]] = relationship(back_populates="symbol")


class PriceBar(Base):
    __tablename__ = "price_bars"
    __table_args__ = (
        UniqueConstraint("symbol_id", "timestamp", name="uq_price_bar_symbol_timestamp"),
        Index("ix_price_bars_symbol_timestamp", "symbol_id", "timestamp"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    open: Mapped[float] = mapped_column(Float)
    high: Mapped[float] = mapped_column(Float)
    low: Mapped[float] = mapped_column(Float)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    symbol: Mapped[Symbol] = relationship(back_populates="price_bars")


class Strategy(Base):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class StrategyRun(Base):
    __tablename__ = "strategy_runs"
    __table_args__ = (Index("ix_strategy_runs_strategy_symbol", "strategy_id", "symbol_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    parameters_json: Mapped[str] = mapped_column(Text, default="{}")
    metrics_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    strategy: Mapped[Strategy] = relationship()
    symbol: Mapped[Symbol] = relationship()


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        Index("ix_orders_run_status", "strategy_run_id", "status"),
        Index("ix_orders_symbol_status", "symbol_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    strategy_run_id: Mapped[str | None] = mapped_column(ForeignKey("strategy_runs.id"), nullable=True, index=True)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    side: Mapped[str] = mapped_column(String(8))
    order_type: Mapped[str] = mapped_column(String(16))
    quantity: Mapped[float] = mapped_column(Float)
    limit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default=OrderStatus.OPEN.value, index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    symbol: Mapped[Symbol] = relationship()


class Fill(Base):
    __tablename__ = "fills"
    __table_args__ = (Index("ix_fills_order_timestamp", "order_id", "timestamp"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    strategy_run_id: Mapped[str | None] = mapped_column(ForeignKey("strategy_runs.id"), nullable=True, index=True)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    price: Mapped[float] = mapped_column(Float)
    fee: Mapped[float] = mapped_column(Float, default=0.0)
    slippage: Mapped[float] = mapped_column(Float, default=0.0)


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        UniqueConstraint("strategy_run_id", "symbol_id", name="uq_position_run_symbol"),
        Index("ix_positions_run_symbol", "strategy_run_id", "symbol_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    strategy_run_id: Mapped[str | None] = mapped_column(ForeignKey("strategy_runs.id"), nullable=True, index=True)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    average_cost: Mapped[float] = mapped_column(Float, default=0.0)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    symbol: Mapped[Symbol] = relationship()


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (Index("ix_trades_run_symbol", "strategy_run_id", "symbol_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    strategy_run_id: Mapped[str | None] = mapped_column(ForeignKey("strategy_runs.id"), nullable=True, index=True)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    quantity: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)


class AccountSnapshot(Base):
    __tablename__ = "account_snapshots"
    __table_args__ = (Index("ix_account_snapshots_run_timestamp", "strategy_run_id", "timestamp"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    strategy_run_id: Mapped[str | None] = mapped_column(ForeignKey("strategy_runs.id"), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    cash: Mapped[float] = mapped_column(Float)
    equity: Mapped[float] = mapped_column(Float)
    realized_pnl: Mapped[float] = mapped_column(Float, default=0.0)
    unrealized_pnl: Mapped[float] = mapped_column(Float, default=0.0)


class LiveQuote(Base):
    __tablename__ = "live_quotes"
    __table_args__ = (
        UniqueConstraint("symbol_id", "provider", name="uq_live_quotes_symbol_provider"),
        Index("ix_live_quotes_symbol_provider", "symbol_id", "provider"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    symbol_id: Mapped[str] = mapped_column(ForeignKey("symbols.id"), index=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    quote_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    bid_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    bid_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ask_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(16), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    raw_payload_json: Mapped[str] = mapped_column(Text, default="{}")

    symbol: Mapped[Symbol] = relationship(back_populates="live_quotes")
