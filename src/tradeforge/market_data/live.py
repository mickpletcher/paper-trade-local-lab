from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from time import sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.config import Settings, get_settings
from tradeforge.database.models import LiveQuote, Position, Symbol


class QuoteProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizedQuote:
    symbol: str
    provider: str
    quote_timestamp: datetime
    fetched_at: datetime
    last_price: float | None
    bid_price: float | None
    ask_price: float | None
    bid_size: int | None
    ask_size: int | None
    previous_close: float | None
    currency: str | None
    raw_payload_json: str


class QuoteProvider(ABC):
    name: str

    @abstractmethod
    def get_latest_quotes(self, symbols: list[str]) -> list[NormalizedQuote]:
        raise NotImplementedError


class AlpacaSnapshotQuoteProvider(QuoteProvider):
    name = "alpaca"

    def __init__(self, settings: Settings):
        self.base_url = settings.alpaca_data_url.rstrip("/")
        self.feed = settings.alpaca_feed
        self.api_key_id = settings.alpaca_api_key_id
        self.api_secret_key = settings.alpaca_api_secret_key
        self.retry_attempts = settings.quote_retry_attempts
        self.retry_base_seconds = settings.quote_retry_base_seconds
        self.retry_max_seconds = settings.quote_retry_max_seconds

    def get_latest_quotes(self, symbols: list[str]) -> list[NormalizedQuote]:
        if not self.api_key_id or not self.api_secret_key:
            raise QuoteProviderError(
                "Alpaca credentials are not configured. Set TRADEFORGE_ALPACA_API_KEY_ID and TRADEFORGE_ALPACA_API_SECRET_KEY."
            )
        if not symbols:
            return []

        query = urlencode({"symbols": ",".join(symbols), "feed": self.feed, "currency": "USD"})
        request = Request(
            f"{self.base_url}/v2/stocks/snapshots?{query}",
            headers={
                "APCA-API-KEY-ID": self.api_key_id,
                "APCA-API-SECRET-KEY": self.api_secret_key,
                "Accept": "application/json",
            },
        )
        for attempt in range(self.retry_attempts):
            try:
                with urlopen(request, timeout=15) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt + 1 >= self.retry_attempts:
                    raise QuoteProviderError(f"Alpaca quote refresh failed with HTTP {exc.code}.") from exc
            except (URLError, TimeoutError, json.JSONDecodeError) as exc:
                if attempt + 1 >= self.retry_attempts:
                    raise QuoteProviderError(f"Alpaca quote refresh failed: {exc}.") from exc
            sleep(min(self.retry_base_seconds * (2**attempt), self.retry_max_seconds))

        if not isinstance(payload, dict):
            raise QuoteProviderError("Alpaca quote refresh returned an invalid response.")
        snapshots = payload
        fetched_at = datetime.now(UTC)
        normalized: list[NormalizedQuote] = []
        for symbol in symbols:
            snapshot = snapshots.get(symbol)
            if not isinstance(snapshot, dict) or not snapshot:
                continue
            latest_trade = snapshot.get("latestTrade") or {}
            latest_quote = snapshot.get("latestQuote") or {}
            minute_bar = snapshot.get("minuteBar") or {}
            previous_close = _to_float((snapshot.get("prevDailyBar") or {}).get("c"))
            quote_timestamp = _parse_timestamp(
                latest_quote.get("t") or latest_trade.get("t") or minute_bar.get("t") or fetched_at.isoformat()
            )
            normalized.append(
                NormalizedQuote(
                    symbol=symbol.upper(),
                    provider=self.name,
                    quote_timestamp=quote_timestamp,
                    fetched_at=fetched_at,
                    last_price=_to_float(latest_trade.get("p")) or _to_float(minute_bar.get("c")),
                    bid_price=_to_float(latest_quote.get("bp")),
                    ask_price=_to_float(latest_quote.get("ap")),
                    bid_size=_to_int(latest_quote.get("bs")),
                    ask_size=_to_int(latest_quote.get("as")),
                    previous_close=previous_close,
                    currency="USD",
                    raw_payload_json=json.dumps(snapshot, sort_keys=True),
                )
            )
        return normalized


def get_quote_provider(settings: Settings | None = None) -> QuoteProvider:
    current_settings = settings or get_settings()
    provider_name = current_settings.quote_provider.strip().lower()
    if provider_name == "alpaca":
        return AlpacaSnapshotQuoteProvider(current_settings)
    raise QuoteProviderError(f"Unsupported quote provider '{current_settings.quote_provider}'.")


def refresh_live_quotes(session: Session, symbols: list[str], provider: QuoteProvider | None = None) -> list[LiveQuote]:
    normalized_symbols = sorted({symbol.strip().upper() for symbol in symbols if symbol.strip()})
    if not normalized_symbols:
        raise QuoteProviderError("No symbols were provided for quote refresh.")

    symbol_models = list(session.scalars(select(Symbol).where(Symbol.ticker.in_(normalized_symbols))))
    symbol_map = {item.ticker: item for item in symbol_models}
    missing_symbols = [symbol for symbol in normalized_symbols if symbol not in symbol_map]
    if missing_symbols:
        missing_display = ", ".join(missing_symbols)
        raise QuoteProviderError(f"Unknown symbols for quote refresh: {missing_display}.")

    quote_provider = provider or get_quote_provider()
    quotes = quote_provider.get_latest_quotes(normalized_symbols)
    returned_symbols = [quote.symbol.strip().upper() for quote in quotes]
    symbol_counts = Counter(returned_symbols)
    duplicate_symbols = sorted(symbol for symbol, count in symbol_counts.items() if count > 1)
    missing_provider_symbols = sorted(set(normalized_symbols).difference(returned_symbols))
    unexpected_symbols = sorted(set(returned_symbols).difference(normalized_symbols))
    if duplicate_symbols or missing_provider_symbols or unexpected_symbols:
        details = []
        if missing_provider_symbols:
            details.append(f"missing: {', '.join(missing_provider_symbols)}")
        if unexpected_symbols:
            details.append(f"unexpected: {', '.join(unexpected_symbols)}")
        if duplicate_symbols:
            details.append(f"duplicate: {', '.join(duplicate_symbols)}")
        raise QuoteProviderError(f"Quote provider returned an invalid symbol set ({'; '.join(details)}).")
    persisted: list[LiveQuote] = []
    for quote in quotes:
        symbol_model = symbol_map[quote.symbol.strip().upper()]
        existing = session.scalar(
            select(LiveQuote).where(LiveQuote.symbol_id == symbol_model.id, LiveQuote.provider == quote.provider)
        )
        if existing is None:
            existing = LiveQuote(symbol_id=symbol_model.id, provider=quote.provider, quote_timestamp=quote.quote_timestamp)
            session.add(existing)
        existing.quote_timestamp = quote.quote_timestamp
        existing.fetched_at = quote.fetched_at
        existing.last_price = quote.last_price
        existing.bid_price = quote.bid_price
        existing.ask_price = quote.ask_price
        existing.bid_size = quote.bid_size
        existing.ask_size = quote.ask_size
        existing.previous_close = quote.previous_close
        existing.currency = quote.currency
        existing.raw_payload_json = quote.raw_payload_json
        persisted.append(existing)

    session.flush()
    return persisted


def get_default_refresh_symbols(session: Session) -> list[str]:
    symbols = session.scalars(
        select(Symbol.ticker)
        .join(Position, Position.symbol_id == Symbol.id)
        .where(Position.quantity != 0)
        .distinct()
        .order_by(Symbol.ticker.asc())
    ).all()
    return list(symbols)


def serialize_quote(quote: LiveQuote, stale_after_seconds: int) -> dict[str, object]:
    age_seconds = max(0, int((datetime.now(UTC) - _ensure_utc(quote.fetched_at)).total_seconds()))
    bid = quote.bid_price
    ask = quote.ask_price
    mark_price = quote.last_price if quote.last_price is not None else _midpoint(bid, ask)
    return {
        "symbol": quote.symbol.ticker,
        "provider": quote.provider,
        "quote_timestamp": _ensure_utc(quote.quote_timestamp).isoformat().replace("+00:00", "Z"),
        "fetched_at": _ensure_utc(quote.fetched_at).isoformat().replace("+00:00", "Z"),
        "last_price": quote.last_price,
        "bid_price": bid,
        "ask_price": ask,
        "mark_price": mark_price,
        "previous_close": quote.previous_close,
        "currency": quote.currency or "USD",
        "age_seconds": age_seconds,
        "is_stale": age_seconds > stale_after_seconds,
    }


def _parse_timestamp(value: str) -> datetime:
    cleaned = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(cleaned)
    return _ensure_utc(parsed)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _to_int(value: object) -> int | None:
    if value is None:
        return None
    return int(value)


def _midpoint(bid: float | None, ask: float | None) -> float | None:
    if bid is None or ask is None:
        return None
    return round((bid + ask) / 2, 6)
