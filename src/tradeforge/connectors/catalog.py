from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from urllib.parse import quote, urlsplit


@dataclass(frozen=True, slots=True)
class ConnectorDescriptor:
    name: str
    transport: str
    default_base_url: str | None
    quote_path: str | None
    auth_header: str | None
    capabilities: tuple[str, ...]
    live_order_routing: bool = False


@dataclass(frozen=True, slots=True)
class ConnectorRequest:
    method: str
    url: str
    headers: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class NormalizedConnectorQuote:
    connector: str
    symbol: str
    timestamp: datetime
    last_price: float
    bid_price: float | None = None
    ask_price: float | None = None


class ConnectorCatalog:
    def __init__(self) -> None:
        self._items = {item.name: item for item in _builtin_descriptors()}

    def list(self) -> list[ConnectorDescriptor]:
        return [self._items[name] for name in sorted(self._items)]

    def get(self, name: str) -> ConnectorDescriptor:
        normalized = name.strip().lower()
        try:
            return self._items[normalized]
        except KeyError as exc:
            raise KeyError(f"Unknown connector: {name}") from exc


class ConnectorAdapter:
    def __init__(
        self,
        descriptor: ConnectorDescriptor,
        *,
        base_url: str | None = None,
        token: str | None = None,
    ) -> None:
        self.descriptor = descriptor
        self.base_url = base_url or descriptor.default_base_url
        self.token = token
        if self.base_url is not None:
            _validate_connector_url(self.base_url, descriptor.transport)

    def build_quote_request(self, symbols: Sequence[str]) -> ConnectorRequest:
        if self.base_url is None or self.descriptor.quote_path is None:
            raise ValueError(f"{self.descriptor.name} requires an external bridge before quote requests are available.")
        normalized = [symbol.strip().upper() for symbol in symbols]
        if not normalized or any(not symbol for symbol in normalized):
            raise ValueError("At least one symbol is required.")
        headers = {"Accept": "application/json"}
        if self.descriptor.auth_header is not None:
            if not self.token:
                raise ValueError(f"{self.descriptor.name} requires a local credential.")
            headers[self.descriptor.auth_header] = f"Bearer {self.token}"
        symbol_query = quote(",".join(normalized), safe=",")
        path = self.descriptor.quote_path.format(symbols=symbol_query)
        return ConnectorRequest("GET", f"{self.base_url.rstrip('/')}/{path.lstrip('/')}", headers)

    def normalize_quote(self, symbol: str, payload: Mapping[str, object]) -> NormalizedConnectorQuote:
        last = _first_number(payload, "last", "last_price", "price", "Last")
        if last is None or last <= 0:
            raise ValueError("Connector quote must include a positive last price.")
        timestamp_value = _first_value(payload, "timestamp", "time", "dateTime", "Timestamp")
        timestamp = _parse_timestamp(timestamp_value)
        return NormalizedConnectorQuote(
            connector=self.descriptor.name,
            symbol=symbol.strip().upper(),
            timestamp=timestamp,
            last_price=last,
            bid_price=_first_number(payload, "bid", "bid_price", "Bid"),
            ask_price=_first_number(payload, "ask", "ask_price", "Ask"),
        )

    def paper_signal(self, symbol: str, side: str, quantity: float) -> dict[str, object]:
        normalized_side = side.strip().lower()
        if normalized_side not in {"buy", "sell"}:
            raise ValueError("Paper signal side must be buy or sell.")
        if not isfinite(quantity) or quantity <= 0:
            raise ValueError("Paper signal quantity must be finite and positive.")
        return {
            "connector": self.descriptor.name,
            "mode": "paper",
            "symbol": symbol.strip().upper(),
            "side": normalized_side,
            "quantity": quantity,
            "transmitted": False,
        }


def _builtin_descriptors() -> tuple[ConnectorDescriptor, ...]:
    return (
        ConnectorDescriptor(
            "tradier",
            "rest",
            "https://sandbox.tradier.com/v1",
            "markets/quotes?symbols={symbols}",
            "Authorization",
            ("quotes", "bars", "paper-signals"),
        ),
        ConnectorDescriptor(
            "tradestation",
            "rest",
            "https://api.tradestation.com/v3",
            "marketdata/quotes/{symbols}",
            "Authorization",
            ("quotes", "bars", "paper-signals"),
        ),
        ConnectorDescriptor(
            "metatrader",
            "local_bridge",
            "http://127.0.0.1:5101",
            "quotes?symbols={symbols}",
            None,
            ("quotes", "bars", "paper-signals"),
        ),
        ConnectorDescriptor(
            "ninjatrader",
            "local_bridge",
            "http://127.0.0.1:5102",
            "quotes?symbols={symbols}",
            None,
            ("quotes", "bars", "paper-signals"),
        ),
        ConnectorDescriptor(
            "ctrader",
            "open_api_bridge",
            "http://127.0.0.1:5103",
            "quotes?symbols={symbols}",
            None,
            ("quotes", "bars", "paper-signals"),
        ),
        ConnectorDescriptor(
            "crypto-exchange",
            "rest",
            None,
            "quotes?symbols={symbols}",
            "Authorization",
            ("spot-quotes", "bars", "paper-signals"),
        ),
    )


def _validate_connector_url(value: str, transport: str) -> None:
    parsed = urlsplit(value)
    is_loopback_bridge = (
        transport.endswith("bridge")
        and parsed.scheme == "http"
        and parsed.hostname
        in {
            "127.0.0.1",
            "localhost",
            "::1",
        }
    )
    if parsed.username is not None or parsed.password is not None or not parsed.hostname:
        raise ValueError("Connector URLs must include a host and must not embed credentials.")
    if parsed.scheme != "https" and not is_loopback_bridge:
        raise ValueError("Remote connector URLs must use HTTPS; HTTP is allowed only for loopback bridges.")


def _first_value(payload: Mapping[str, object], *names: str) -> object | None:
    return next((payload[name] for name in names if name in payload), None)


def _first_number(payload: Mapping[str, object], *names: str) -> float | None:
    value = _first_value(payload, *names)
    if value is None:
        return None
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError(f"Connector quote field is not numeric: {value}")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Connector quote field is not numeric: {value}") from exc
    if not isfinite(normalized):
        raise ValueError("Connector quote fields must be finite.")
    return normalized


def _parse_timestamp(value: object | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("Connector quote timestamp must use ISO format.") from exc
    else:
        raise ValueError("Connector quote timestamp must be a datetime or ISO string.")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Connector quote timestamp must be timezone aware.")
    return parsed.astimezone(timezone.utc)
