from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock
from urllib.error import URLError
from urllib.request import Request

import pytest

from tradeforge.config import Settings
from tradeforge.database.models import AccountSnapshot, LiveQuote, Position, Strategy, StrategyRun
from tradeforge.market_data.live import (
    AlpacaSnapshotQuoteProvider,
    NormalizedQuote,
    QuoteProviderError,
    _RejectQuoteRedirects,
    refresh_live_quotes,
    serialize_quote,
)
from tradeforge.valuation.service import build_portfolio_valuation


class FakeQuoteProvider:
    def __init__(self, quotes: list[NormalizedQuote]):
        self.quotes = quotes

    def get_latest_quotes(self, symbols: list[str]) -> list[NormalizedQuote]:
        return [quote for quote in self.quotes if quote.symbol in symbols]


def test_alpaca_provider_parses_root_symbol_map(monkeypatch) -> None:
    payload = {
        "AAPL": {
            "latestTrade": {"p": 188.61, "t": "2026-05-12T20:15:00Z"},
            "latestQuote": {"bp": 188.6, "ap": 188.62, "bs": 10, "as": 12, "t": "2026-05-12T20:15:00Z"},
            "minuteBar": {"c": 188.59, "t": "2026-05-12T20:15:00Z"},
            "prevDailyBar": {"c": 187.12},
        }
    }
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    monkeypatch.setattr("tradeforge.market_data.live._open_quote_request", lambda request, timeout: response)
    settings = SimpleNamespace(
        alpaca_data_url="https://data.alpaca.markets",
        alpaca_feed="iex",
        alpaca_api_key_id="test-key",
        alpaca_api_secret_key="test-secret",
        quote_retry_attempts=3,
        quote_retry_base_seconds=0,
        quote_retry_max_seconds=30,
    )

    quotes = AlpacaSnapshotQuoteProvider(settings).get_latest_quotes(["AAPL"])

    assert len(quotes) == 1
    assert quotes[0].symbol == "AAPL"
    assert quotes[0].last_price == 188.61
    assert quotes[0].bid_price == 188.6
    assert quotes[0].ask_price == 188.62
    assert quotes[0].previous_close == 187.12
    assert json.loads(quotes[0].raw_payload_json) == payload["AAPL"]


def test_alpaca_provider_retries_transient_failures(monkeypatch) -> None:
    payload = {"AAPL": {"latestTrade": {"p": 188.61, "t": "2026-05-12T20:15:00Z"}}}
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    attempts = iter([URLError("temporary failure"), response])

    def fake_urlopen(request, timeout):
        result = next(attempts)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr("tradeforge.market_data.live._open_quote_request", fake_urlopen)
    delays: list[float] = []
    monkeypatch.setattr("tradeforge.market_data.live.sleep", delays.append)
    settings = SimpleNamespace(
        alpaca_data_url="https://data.alpaca.markets",
        alpaca_feed="iex",
        alpaca_api_key_id="test-key",
        alpaca_api_secret_key="test-secret",
        quote_retry_attempts=2,
        quote_retry_base_seconds=60,
        quote_retry_max_seconds=30,
    )

    quotes = AlpacaSnapshotQuoteProvider(settings).get_latest_quotes(["AAPL"])

    assert quotes[0].last_price == 188.61
    assert delays == [30]


@pytest.mark.parametrize(
    "base_url",
    [
        "http://data.alpaca.markets",
        "file:///etc/passwd",
        "https:///missing-host",
        "https://user:password@data.alpaca.markets",  # pragma: allowlist secret
    ],
)
def test_alpaca_provider_rejects_unsafe_base_urls(base_url: str) -> None:
    settings = Settings(TRADEFORGE_ALPACA_DATA_URL=base_url)

    with pytest.raises(QuoteProviderError, match="must be an HTTPS URL"):
        AlpacaSnapshotQuoteProvider(settings)


def test_alpaca_provider_accepts_https_base_url() -> None:
    settings = Settings(TRADEFORGE_ALPACA_DATA_URL="https://data.alpaca.markets/")

    provider = AlpacaSnapshotQuoteProvider(settings)

    assert provider.base_url == "https://data.alpaca.markets"


def test_alpaca_provider_rejects_redirects() -> None:
    handler = _RejectQuoteRedirects()
    request = Request(
        "https://data.alpaca.markets/v2/stocks/snapshots",
        headers={"APCA-API-KEY-ID": "test-key", "APCA-API-SECRET-KEY": "test-secret"},
    )

    with pytest.raises(QuoteProviderError, match="redirects are not allowed"):
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            {},
            "https://redirect.example/snapshots",
        )


@pytest.mark.parametrize(
    ("snapshot", "message"),
    [
        ({"latestTrade": {"p": -1, "t": "2026-05-12T20:15:00Z"}}, "finite positive number"),
        ({"latestTrade": {"p": "NaN", "t": "2026-05-12T20:15:00Z"}}, "finite positive number"),
        ({"latestTrade": {"p": float("nan"), "t": "2026-05-12T20:15:00Z"}}, "invalid JSON constant"),
        (
            {
                "latestTrade": {"p": 100, "t": "2026-05-12T20:15:00Z"},
                "latestQuote": {"bs": 1.5},
            },
            "nonnegative integer",
        ),
        ({"latestTrade": {"t": "2026-05-12T20:15:00Z"}}, "no usable price"),
        ({"latestTrade": {"p": 100, "t": "2026-05-12T20:15:00"}}, "timezone-aware"),
        ({"latestTrade": {"p": 100, "t": "not-a-timestamp"}}, "timezone-aware"),
        ({"latestTrade": []}, "must be an object"),
        (
            {"latestQuote": {"bp": 102, "ap": 101, "t": "2026-05-12T20:15:00Z"}},
            "crossed market",
        ),
    ],
)
def test_alpaca_provider_rejects_invalid_quote_payloads(monkeypatch, snapshot, message) -> None:
    response = MagicMock()
    response.read.return_value = json.dumps({"AAPL": snapshot}).encode("utf-8")
    response.__enter__.return_value = response
    monkeypatch.setattr("tradeforge.market_data.live._open_quote_request", lambda request, timeout: response)
    settings = SimpleNamespace(
        alpaca_data_url="https://data.alpaca.markets",
        alpaca_feed="iex",
        alpaca_api_key_id="test-key",
        alpaca_api_secret_key="test-secret",
        quote_retry_attempts=1,
        quote_retry_base_seconds=0,
        quote_retry_max_seconds=30,
    )

    with pytest.raises(QuoteProviderError, match=message):
        AlpacaSnapshotQuoteProvider(settings).get_latest_quotes(["AAPL"])


def test_refresh_live_quotes_upserts_existing_rows(session, symbol) -> None:
    first = NormalizedQuote(
        symbol="AAPL",
        provider="fake",
        quote_timestamp=datetime(2026, 5, 12, 20, 0, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 12, 20, 0, 1, tzinfo=UTC),
        last_price=101.5,
        bid_price=101.4,
        ask_price=101.6,
        bid_size=10,
        ask_size=12,
        previous_close=99.0,
        currency="USD",
        raw_payload_json='{"first": true}',
    )
    second = NormalizedQuote(
        symbol="AAPL",
        provider="fake",
        quote_timestamp=datetime(2026, 5, 12, 20, 1, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 12, 20, 1, 1, tzinfo=UTC),
        last_price=102.5,
        bid_price=102.4,
        ask_price=102.6,
        bid_size=15,
        ask_size=14,
        previous_close=99.0,
        currency="USD",
        raw_payload_json='{"second": true}',
    )

    refresh_live_quotes(session, ["AAPL"], provider=FakeQuoteProvider([first]))
    refresh_live_quotes(session, ["AAPL"], provider=FakeQuoteProvider([second]))

    quotes = session.query(LiveQuote).all()
    assert len(quotes) == 1
    assert quotes[0].last_price == 102.5
    assert quotes[0].bid_size == 15
    assert quotes[0].raw_payload_json == '{"second": true}'


def test_refresh_live_quotes_rejects_incomplete_provider_response(session, symbol) -> None:
    with pytest.raises(QuoteProviderError, match="missing: AAPL"):
        refresh_live_quotes(session, ["AAPL"], provider=FakeQuoteProvider([]))

    assert session.query(LiveQuote).all() == []


def test_refresh_live_quotes_rejects_invalid_normalized_quote(session, symbol) -> None:
    invalid = NormalizedQuote(
        symbol="AAPL",
        provider="fake",
        quote_timestamp=datetime.now(UTC),
        fetched_at=datetime.now(UTC),
        last_price=float("inf"),
        bid_price=None,
        ask_price=None,
        bid_size=None,
        ask_size=None,
        previous_close=None,
        currency="USD",
        raw_payload_json="{}",
    )

    with pytest.raises(QuoteProviderError, match="invalid last price"):
        refresh_live_quotes(session, ["AAPL"], provider=FakeQuoteProvider([invalid]))

    assert session.query(LiveQuote).all() == []


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"bid_size": -1}, "invalid bid size"),
        ({"fetched_at": datetime(2026, 5, 12, 20, 15)}, "invalid fetch timestamp"),
        ({"raw_payload_json": "not-json"}, "invalid raw payload"),
    ],
)
def test_refresh_live_quotes_validates_provider_contract(session, symbol, changes, message) -> None:
    valid = NormalizedQuote(
        symbol="AAPL",
        provider="fake",
        quote_timestamp=datetime(2026, 5, 12, 20, 15, tzinfo=UTC),
        fetched_at=datetime(2026, 5, 12, 20, 15, 1, tzinfo=UTC),
        last_price=100,
        bid_price=99,
        ask_price=101,
        bid_size=1,
        ask_size=1,
        previous_close=98,
        currency="USD",
        raw_payload_json="{}",
    )

    with pytest.raises(QuoteProviderError, match=message):
        refresh_live_quotes(session, ["AAPL"], provider=FakeQuoteProvider([replace(valid, **changes)]))

    assert session.query(LiveQuote).all() == []


def test_quote_staleness_uses_market_timestamp(session, symbol) -> None:
    current_time = datetime.now(UTC)
    quote = LiveQuote(
        symbol_id=symbol.id,
        provider="fake",
        quote_timestamp=current_time - timedelta(minutes=5),
        fetched_at=current_time,
        last_price=100,
        raw_payload_json="{}",
    )
    session.add(quote)
    session.flush()

    payload = serialize_quote(quote, stale_after_seconds=30)

    assert payload["age_seconds"] >= 300
    assert payload["fetch_age_seconds"] <= 1
    assert payload["is_stale"] is True


def test_build_portfolio_valuation_marks_positions_to_market(session, symbol) -> None:
    strategy = Strategy(name="manual-live-valuation")
    session.add(strategy)
    session.flush()
    run = StrategyRun(
        strategy_id=strategy.id,
        symbol_id=symbol.id,
        start_date=datetime(2026, 5, 12, 19, 0, tzinfo=UTC),
        end_date=datetime(2026, 5, 12, 20, 0, tzinfo=UTC),
    )
    session.add(run)
    session.flush()
    session.add(
        Position(
            strategy_run_id=run.id,
            symbol_id=symbol.id,
            quantity=2,
            average_cost=100.0,
            realized_pnl=5.0,
        )
    )
    session.add(
        AccountSnapshot(
            strategy_run_id=run.id,
            timestamp=datetime(2026, 5, 12, 20, 0, tzinfo=UTC),
            cash=9500.0,
            equity=9700.0,
            realized_pnl=5.0,
            unrealized_pnl=0.0,
        )
    )
    session.add(
        LiveQuote(
            symbol_id=symbol.id,
            provider="fake",
            quote_timestamp=datetime(2026, 5, 12, 20, 1, tzinfo=UTC),
            fetched_at=datetime.now(UTC),
            last_price=105.0,
            bid_price=104.9,
            ask_price=105.1,
            previous_close=99.0,
            currency="USD",
            raw_payload_json="{}",
        )
    )
    session.flush()

    payload = build_portfolio_valuation(session, stale_after_seconds=30)

    assert payload["cash"] == 9500.0
    assert payload["market_value"] == 210.0
    assert payload["total_equity"] == 9710.0
    assert payload["unrealized_pnl"] == 10.0
    assert payload["positions"][0]["symbol"] == "AAPL"
    assert payload["positions"][0]["mark_price"] == 105.0


def test_portfolio_uses_newest_quote_across_providers(session, symbol) -> None:
    strategy = Strategy(name="quote-selection")
    session.add(strategy)
    session.flush()
    run = StrategyRun(
        strategy_id=strategy.id,
        symbol_id=symbol.id,
        start_date=datetime(2026, 5, 12, 19, 0, tzinfo=UTC),
        end_date=datetime(2026, 5, 12, 20, 0, tzinfo=UTC),
    )
    session.add(run)
    session.flush()
    session.add(Position(strategy_run_id=run.id, symbol_id=symbol.id, quantity=1, average_cost=75, realized_pnl=0))
    session.add(
        AccountSnapshot(
            strategy_run_id=run.id,
            timestamp=datetime(2026, 5, 12, 20, 0, tzinfo=UTC),
            cash=1000,
            equity=1075,
            realized_pnl=0,
            unrealized_pnl=0,
        )
    )
    session.add_all(
        [
            LiveQuote(
                symbol_id=symbol.id,
                provider="newer-provider",
                quote_timestamp=datetime(2026, 5, 12, 20, 1, tzinfo=UTC),
                fetched_at=datetime(2026, 5, 12, 20, 1, tzinfo=UTC),
                last_price=100,
                raw_payload_json="{}",
            ),
            LiveQuote(
                symbol_id=symbol.id,
                provider="inserted-last-but-older",
                quote_timestamp=datetime(2026, 5, 12, 19, 59, tzinfo=UTC),
                fetched_at=datetime(2026, 5, 12, 19, 59, tzinfo=UTC),
                last_price=50,
                raw_payload_json="{}",
            ),
        ]
    )
    session.flush()

    payload = build_portfolio_valuation(session, stale_after_seconds=30, strategy_run_id=run.id)

    assert payload["market_value"] == 100
    assert payload["positions"][0]["quote_provider"] == "newer-provider"


def test_build_portfolio_valuation_preserves_cash_for_flat_runs(session, symbol) -> None:
    strategy = Strategy(name="flat-live-valuation")
    session.add(strategy)
    session.flush()
    run = StrategyRun(
        strategy_id=strategy.id,
        symbol_id=symbol.id,
        start_date=datetime(2026, 5, 12, 19, 0, tzinfo=UTC),
        end_date=datetime(2026, 5, 12, 20, 0, tzinfo=UTC),
        completed_at=datetime(2026, 5, 12, 20, 1, tzinfo=UTC),
    )
    session.add(run)
    session.flush()
    session.add(
        Position(
            strategy_run_id=run.id,
            symbol_id=symbol.id,
            quantity=0,
            average_cost=0.0,
            realized_pnl=250.0,
        )
    )
    session.add(
        AccountSnapshot(
            strategy_run_id=run.id,
            timestamp=datetime(2026, 5, 12, 19, 30, tzinfo=UTC),
            cash=10_000.0,
            equity=10_000.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
        )
    )
    session.add(
        AccountSnapshot(
            strategy_run_id=run.id,
            timestamp=datetime(2026, 5, 12, 20, 0, tzinfo=UTC),
            cash=10_250.0,
            equity=10_250.0,
            realized_pnl=250.0,
            unrealized_pnl=0.0,
        )
    )
    session.flush()

    payload = build_portfolio_valuation(session, stale_after_seconds=30)

    assert payload["cash"] == 10_250.0
    assert payload["market_value"] == 0.0
    assert payload["total_equity"] == 10_250.0
    assert payload["positions_count"] == 0
    assert payload["positions"] == []


def test_portfolio_valuation_scopes_cash_to_requested_run(session, symbol) -> None:
    strategy = Strategy(name="run-scoping")
    session.add(strategy)
    session.flush()
    runs = [
        StrategyRun(
            strategy_id=strategy.id,
            symbol_id=symbol.id,
            started_at=datetime(2026, 5, 12, 18 + index, 0, tzinfo=UTC),
            start_date=datetime(2026, 5, 12, 18 + index, 0, tzinfo=UTC),
            end_date=datetime(2026, 5, 12, 19 + index, 0, tzinfo=UTC),
        )
        for index in range(2)
    ]
    session.add_all(runs)
    session.flush()
    session.add_all(
        [
            AccountSnapshot(
                strategy_run_id=run.id,
                timestamp=run.end_date,
                cash=cash,
                equity=cash,
                realized_pnl=0,
                unrealized_pnl=0,
            )
            for run, cash in zip(runs, [10_100, 10_200], strict=True)
        ]
    )
    session.flush()

    first = build_portfolio_valuation(session, stale_after_seconds=30, strategy_run_id=runs[0].id)
    latest = build_portfolio_valuation(session, stale_after_seconds=30)

    assert first["strategy_run_id"] == runs[0].id
    assert first["cash"] == 10_100
    assert latest["strategy_run_id"] == runs[1].id
    assert latest["cash"] == 10_200


def test_portfolio_valuation_rejects_unknown_run(session) -> None:
    with pytest.raises(ValueError, match="Unknown strategy run"):
        build_portfolio_valuation(session, stale_after_seconds=30, strategy_run_id="missing")
