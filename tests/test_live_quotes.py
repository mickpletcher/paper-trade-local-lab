from __future__ import annotations

from datetime import UTC, datetime

import pytest

from tradeforge.config import Settings
from tradeforge.database.models import AccountSnapshot, LiveQuote, Position, Strategy, StrategyRun
from tradeforge.market_data.live import (
    AlpacaSnapshotQuoteProvider,
    NormalizedQuote,
    QuoteProviderError,
    refresh_live_quotes,
)
from tradeforge.valuation.service import build_portfolio_valuation


class FakeQuoteProvider:
    def __init__(self, quotes: list[NormalizedQuote]):
        self.quotes = quotes

    def get_latest_quotes(self, symbols: list[str]) -> list[NormalizedQuote]:
        return [quote for quote in self.quotes if quote.symbol in symbols]


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
