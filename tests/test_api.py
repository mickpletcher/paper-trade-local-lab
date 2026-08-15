from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from tradeforge.api.app import app
from tradeforge.config import get_settings
from tradeforge.database.migrations import init_db
from tradeforge.database.models import AccountSnapshot, LiveQuote, Position, Strategy, StrategyRun, Symbol
from tradeforge.database.session import session_scope


def test_openapi_contains_endpoint_examples() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    health_example = document["paths"]["/health"]["get"]["responses"]["200"]["content"]["application/json"]["example"]
    orders_example = document["paths"]["/orders"]["get"]["responses"]["200"]["content"]["application/json"]["example"]
    strategy_runs_example = document["paths"]["/strategy-runs"]["get"]["responses"]["200"]["content"][
        "application/json"
    ]["example"]
    quotes_example = document["paths"]["/quotes"]["get"]["responses"]["200"]["content"]["application/json"]["example"]
    portfolio_example = document["paths"]["/portfolio"]["get"]["responses"]["200"]["content"]["application/json"][
        "example"
    ]

    assert health_example == {"status": "ok", "database": "ok"}
    assert orders_example[0]["status"] == "filled"
    assert strategy_runs_example[0]["strategy"] == "moving-average-cross"
    assert quotes_example[0]["provider"] == "alpaca"
    assert portfolio_example["positions"][0]["symbol"] == "AAPL"


def test_quotes_and_portfolio_endpoints(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")
    monkeypatch.setenv("TRADEFORGE_QUOTE_STALE_AFTER_SECONDS", "300")
    init_db()
    with session_scope() as session:
        symbol = Symbol(ticker="AAPL")
        session.add(symbol)
        session.flush()
        strategy = Strategy(name="api-valuation")
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
                quantity=3,
                average_cost=100.0,
                realized_pnl=0.0,
            )
        )
        session.add(
            AccountSnapshot(
                strategy_run_id=run.id,
                timestamp=datetime(2026, 5, 12, 20, 0, tzinfo=UTC),
                cash=9000.0,
                equity=9300.0,
                realized_pnl=0.0,
                unrealized_pnl=0.0,
            )
        )
        session.add(
            LiveQuote(
                symbol_id=symbol.id,
                provider="alpaca",
                quote_timestamp=datetime(2026, 5, 12, 20, 1, tzinfo=UTC),
                fetched_at=datetime.now(UTC),
                last_price=110.0,
                bid_price=109.9,
                ask_price=110.1,
                previous_close=108.0,
                currency="USD",
                raw_payload_json="{}",
            )
        )

    with TestClient(app) as client:
        quotes_response = client.get("/quotes")
        portfolio_response = client.get("/portfolio", params={"strategy_run_id": run.id})
        unknown_portfolio_response = client.get("/portfolio", params={"strategy_run_id": "missing"})

    assert quotes_response.status_code == 200
    assert portfolio_response.status_code == 200
    assert unknown_portfolio_response.status_code == 404
    assert quotes_response.json()[0]["symbol"] == "AAPL"
    assert portfolio_response.json()["strategy_run_id"] == run.id
    assert portfolio_response.json()["market_value"] == 330.0
    assert portfolio_response.json()["total_equity"] == 9330.0


def test_metrics_endpoint_is_opt_in(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")
    init_db()

    with TestClient(app) as client:
        disabled_response = client.get("/metrics")

    assert disabled_response.status_code == 404

    monkeypatch.setenv("TRADEFORGE_ENABLE_METRICS", "true")
    get_settings.cache_clear()
    with TestClient(app) as client:
        client.get("/health")
        enabled_response = client.get("/metrics")

    assert enabled_response.status_code == 200
    assert "tradeforge_http_requests_total" in enabled_response.text
    assert 'path="/health"' in enabled_response.text


def test_settings_are_cached_until_explicitly_cleared(monkeypatch) -> None:
    monkeypatch.setenv("TRADEFORGE_STARTING_CASH", "1000")
    first = get_settings()
    monkeypatch.setenv("TRADEFORGE_STARTING_CASH", "2000")

    assert get_settings() is first
    assert get_settings().starting_cash == 1000

    get_settings.cache_clear()

    assert get_settings().starting_cash == 2000


def test_api_lifespan_initializes_database_and_health_checks_it(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert (tmp_path / "data" / "tradeforge.db").exists()
