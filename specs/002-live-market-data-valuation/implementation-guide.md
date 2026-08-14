# Live Data Feed Implementation Guide

## Purpose

This guide explains how to add live market data to TradeForge so open positions can be valued in near real time while all trading stays local.

The key boundary is simple:

1. Market data may come from external providers.
2. Orders, fills, cash, positions, and execution remain local.
3. Historical backtest data stays separate from live quote data.

## Recommended First Implementation

The safest first implementation is:

1. Start with one stock quote provider.
2. Poll or stream latest quote data into a dedicated local table.
3. Revalue local positions from that quote table.
4. Expose quote and valuation data through the API.
5. Do not change the simulated broker or backtest flow yet.

For the first provider, the strongest practical choices are:

1. Alpaca
2. Polygon
3. Twelve Data

Recommended order:

1. Alpaca if you want a clean stock focused first pass with official SDK support and clear docs.
2. Polygon if low latency U.S. stock feeds matter more than simplicity.
3. Twelve Data if you want one provider that can later expand into forex, crypto, and global assets.

## Official Provider References

### U.S. Equities And Multi Asset Providers

1. Alpaca Market Data API
   Docs: [About Market Data API](https://docs.alpaca.markets/v1.3/docs/about-market-data-api)
   Real time stocks: [Real time Stock Data](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data)
   Streaming overview: [WebSocket Stream](https://docs.alpaca.markets/docs/streaming-market-data)
   Python SDK: [alpaca-py real time stock data](https://alpaca.markets/sdks/python/api_reference/data/stock/live.html)

2. Polygon
   Docs: [Stocks WebSocket Overview](https://polygon.io/docs/stocks/ws_getting-started)
   Quickstart: [WebSocket Quickstart](https://polygon.io/docs/websocket/quickstart?auth=signup)

3. Twelve Data
   Docs: [API Documentation](https://twelvedata.com/docs)
   API usage: [Advanced API Usage](https://twelvedata.com/docs/advanced/api-usage)
   Streaming overview: [How to stream the data](https://support.twelvedata.com/en/articles/5620516-how-to-stream-the-data)

4. Alpha Vantage
   Docs: [API Documentation](https://www.alphavantage.co/documentation/)
   Main site: [Alpha Vantage](https://www.alphavantage.co/)

### Crypto Exchange Feeds

1. Coinbase Exchange
   Docs: [Exchange WebSocket Overview](https://docs.cdp.coinbase.com/exchange/websocket-feed)
   Channels: [Exchange WebSocket Channels](https://docs.cdp.coinbase.com/exchange/websocket-feed/channels)

2. Kraken
   Docs: [WebSocket v2 Ticker](https://docs.kraken.com/api/docs/websocket-v2/ticker/)
   FAQ: [Kraken WebSocket FAQ](https://support.kraken.com/articles/360022326871-kraken-websocket-api-frequently-asked-questions)

## Provider Choice Guidance

### Best First Stock Provider

Alpaca is the most balanced first implementation for this repo.

Why:

1. Clear stock WebSocket documentation.
2. Clear feed options such as IEX, SIP, and delayed SIP.
3. Official Python support.
4. Good fit for a local valuation loop.

Known feed choices from the official docs:

1. `v2/iex`
2. `v2/sip`
3. `v2/delayed_sip`
4. `v1beta1/boats`
5. `v1beta1/overnight`

### Best U.S. Equity Depth Option

Polygon is a strong second choice if you want a more market data heavy platform.

Why:

1. Clear WebSocket support for trades, quotes, and aggregates.
2. Good U.S. equity focus.
3. Better fit if this repo later grows toward richer real time dashboards.

### Best Broad Coverage Option

Twelve Data is a strong choice if you want one provider for more than U.S. stocks.

Why:

1. Stocks, forex, crypto, ETFs, and global instruments.
2. API plus WebSocket support.
3. Good long term provider flexibility.

### Best Crypto First Option

If crypto valuation becomes important, use a direct exchange feed instead of forcing a stock provider to handle crypto first.

Recommended first crypto providers:

1. Coinbase
2. Kraken

See also:

* `feed-options.md` for ranked provider guidance by easiest first implementation, best overall fit, and later additions

## Recommended Repo Design

Add live quotes as a new path beside historical market data.

Recommended modules:

1. `src/tradeforge/market_data/live_base.py`
   Provider contract and normalized models.

2. `src/tradeforge/market_data/live_alpaca.py`
   Alpaca implementation.

3. `src/tradeforge/market_data/live_polygon.py`
   Polygon implementation later if needed.

4. `src/tradeforge/market_data/live_twelve_data.py`
   Twelve Data implementation later if needed.

5. `src/tradeforge/valuation/service.py`
   Current valuation calculations for positions and total equity.

6. `src/tradeforge/valuation/models.py`
   Optional response models if you want to keep API contracts clean.

7. `src/tradeforge/database/models.py`
   New live quote table.

8. `src/tradeforge/api/app.py`
   Quote and valuation endpoints.

9. `src/tradeforge/cli.py`
   Quote refresh commands if CLI control is part of the first pass.

## Do Not Reuse Historical Bars For This

Do not write live quotes into `price_bars`.

Keep these separate:

1. `price_bars`
   Historical replay and backtest bars

2. `live_quotes`
   Current market state for local valuation

Reasons:

1. Historical bars and live quotes have different semantics.
2. Quote timestamps can update many times within the same minute.
3. You need freshness and provider metadata that do not belong in backtest bars.

## Recommended Database Model

Add a table like `live_quotes`.

Recommended columns:

1. `id`
2. `symbol_id`
3. `provider`
4. `asset_class`
5. `quote_timestamp`
6. `last_price`
7. `bid_price`
8. `ask_price`
9. `bid_size`
10. `ask_size`
11. `previous_close`
12. `currency`
13. `market_session`
14. `fetched_at`
15. `is_stale`
16. `raw_payload_json`

Recommended uniqueness rule:

1. Unique on `symbol_id` plus `provider`

That gives one latest quote row per symbol and provider in the first pass.

## Normalized Quote Contract

Every provider adapter should map into one normalized internal shape before persistence.

Recommended normalized object:

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class LiveQuote:
    symbol: str
    provider: str
    asset_class: str
    quote_timestamp: datetime
    last_price: float | None
    bid_price: float | None
    ask_price: float | None
    bid_size: float | None
    ask_size: float | None
    previous_close: float | None
    currency: str | None
    market_session: str | None
    raw_payload_json: str
```

Design rules:

1. Normalize symbol casing.
2. Convert timestamps to UTC before storage.
3. Preserve raw payload for debugging.
4. Keep provider specific fields out of the rest of the app.

## Provider Interface

Recommended base contract:

```python
from abc import ABC, abstractmethod


class QuoteProvider(ABC):
    name: str

    @abstractmethod
    async def get_latest_quotes(self, symbols: list[str]) -> list[LiveQuote]:
        raise NotImplementedError
```

If you choose streaming first, also support:

```python
class StreamingQuoteProvider(QuoteProvider):
    @abstractmethod
    async def stream_quotes(self, symbols: list[str]):
        raise NotImplementedError
```

## Polling Versus Streaming

### Best First Pass

Use polling first unless you need second by second updates immediately.

Why polling first:

1. Simpler to test.
2. Easier to run from CLI or background job.
3. Less connection state to manage.
4. Easier failure recovery.

Good first polling interval:

1. 5 seconds for actively watched symbols
2. 15 seconds if you want lower provider cost

### When To Add Streaming

Add WebSocket streaming when:

1. You want near real time dashboard updates.
2. You want better quote freshness than polling allows.
3. Provider plan limits support it comfortably.

## Refresh Loop Design

Recommended first implementation:

1. Read active symbols from positions and optional watchlist.
2. Fetch latest quotes from provider.
3. Normalize each quote.
4. Upsert into `live_quotes`.
5. Mark stale state based on freshness policy.
6. Recalculate local valuation on demand in the API.

Do not update valuation by mutating positions directly.

Instead:

1. Keep positions as execution state.
2. Compute market value and unrealized profit and loss from positions plus `live_quotes`.

## Freshness Policy

You need an explicit stale rule.

Recommended first rule:

1. Quote is fresh if `now_utc - fetched_at <= 15 seconds`
2. Quote is stale if older than 15 seconds during market hours
3. Quote may be expected stale outside market hours

Recommended fields returned by API:

1. `quote_timestamp`
2. `fetched_at`
3. `age_seconds`
4. `is_stale`
5. `stale_reason`

## Valuation Rules

For long equity positions:

1. Use `last_price` if available
2. If no `last_price`, fall back to midpoint of bid and ask when both exist
3. If neither exists, mark valuation unavailable

Recommended formulas:

1. `market_value = quantity * mark_price`
2. `unrealized_pnl = (mark_price - average_cost) * quantity`
3. `total_equity = cash + sum(all market_value)`

For API response shape:

```json
{
  "cash": 100000.0,
  "market_value": 12450.0,
  "total_equity": 112450.0,
  "unrealized_pnl": 340.0,
  "positions": [
    {
      "symbol": "AAPL",
      "quantity": 100,
      "average_cost": 185.2,
      "mark_price": 188.6,
      "market_value": 18860.0,
      "unrealized_pnl": 340.0,
      "is_stale": false
    }
  ]
}
```

## API Design

Recommended endpoints:

1. `GET /quotes`
   Return latest quotes by symbol

2. `GET /portfolio`
   Return current portfolio valuation

3. `GET /account`
   Return cash, market value, total equity, and stale quote summary

Example quote response:

```json
[
  {
    "symbol": "AAPL",
    "provider": "alpaca",
    "last_price": 188.61,
    "bid_price": 188.60,
    "ask_price": 188.62,
    "quote_timestamp": "2026-05-12T19:12:10.321000Z",
    "fetched_at": "2026-05-12T19:12:11.004000Z",
    "is_stale": false
  }
]
```

## CLI Design

Recommended first CLI commands:

1. `tradeforge refresh-quotes --symbols AAPL,MSFT`
2. `tradeforge show-valuation`
3. `tradeforge show-quotes`

Alternative:

If you want less CLI surface at first, add only:

1. `tradeforge refresh-quotes`

and expose the rest through the API.

## Implementation Path By Provider

### Alpaca First Pass

Recommended first mode:

1. Start with REST or latest quote endpoint if available in your chosen SDK path.
2. Move to WebSocket only after the valuation path is proven.

If using streaming:

1. Connect to `wss://stream.data.alpaca.markets/{version}/{feed}`
2. Start with `v2/iex` for a simpler first pass if it meets your needs
3. Subscribe only to symbols held locally
4. Handle reconnects and authentication failures explicitly

Why Alpaca first:

1. Good Python support
2. Clear stock quote semantics
3. Good path for U.S. equities valuation

### Polygon First Pass

Recommended use:

1. Use WebSocket quotes if you want a feed first architecture.
2. Normalize Polygon quote payloads into the internal `LiveQuote`.
3. Keep provider specific event types inside the adapter only.

Why use Polygon:

1. Strong U.S. market data focus
2. Clear quote and aggregate feed structure

### Twelve Data First Pass

Recommended use:

1. Use if you want one provider that can later cover stocks, forex, crypto, and global assets.
2. Start with latest price or quote polling.
3. Add WebSocket later if near real time updates are needed.

### Coinbase Or Kraken For Crypto

Recommended approach:

1. Add crypto support as a separate provider implementation.
2. Do not mix exchange specific pair naming into the rest of the app.
3. Normalize symbols internally such as `BTCUSD` or `BTC/USD` based on your chosen canonical format.

## Canonical Symbol Rules

You need one internal symbol rule now so provider adapters stay clean later.

Recommended internal approach:

1. Keep current `symbols.ticker` as the local canonical ticker.
2. Add optional provider mapping later if needed.

Examples:

1. Equity
   Internal: `AAPL`
   Alpaca: `AAPL`
   Polygon: `AAPL`
   Twelve Data: `AAPL`

2. Crypto
   Internal: `BTCUSD`
   Coinbase external: `BTC-USD`
   Kraken external: `BTC/USD`

If crypto gets added, you will likely need a provider symbol mapping table.

## Failure Handling

Do not let quote failure affect trading state.

Rules:

1. If quote refresh fails, do not mutate orders, positions, or cash.
2. Mark quote status stale.
3. Return stale indicators in API responses.
4. Log provider errors with symbol, provider, and timestamp.
5. Keep the last good quote unless you explicitly want empty state on failure.

Recommended behavior:

1. Last known good quote remains visible
2. `is_stale` becomes `true`
3. `stale_reason` explains timeout, auth failure, connection loss, or market closed

## Testing Strategy

Add tests in this order:

1. Quote normalization tests
2. Quote upsert tests
3. Quote freshness tests
4. Valuation math tests
5. API tests for `/quotes`, `/portfolio`, and `/account`
6. Provider failure tests

Do not rely on live provider calls in the test suite.

Use mocked provider responses only.

## Recommended First Milestone

The cleanest first milestone is:

1. Add `live_quotes` table
2. Add `QuoteProvider` contract
3. Implement one provider adapter
4. Add `tradeforge refresh-quotes`
5. Add `/quotes`
6. Add `/portfolio`

That gives immediate value without touching simulated execution logic.

## Recommended Second Milestone

After the first milestone works:

1. Add background refresh scheduling
2. Add quote freshness summary in `/account`
3. Add watchlist support
4. Add second provider implementation

## Recommended Third Milestone

Only after the valuation path is stable:

1. Add streaming support
2. Add crypto quote provider
3. Add richer dashboards
4. Add intraday valuation snapshots if needed

## Final Recommendation

Implement this in narrow layers:

1. quote storage
2. provider adapter
3. refresh loop
4. valuation service
5. API exposure

Keep the local trading engine untouched until live valuation is proven stable.
