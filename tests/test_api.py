from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import event

from tradeforge.api.app import app
from tradeforge.api.dashboard import render_dashboard
from tradeforge.auth.service import create_api_key, create_tenant
from tradeforge.config import Settings, get_settings
from tradeforge.constants import DEFAULT_TENANT_ID
from tradeforge.database.migrations import init_db
from tradeforge.database.models import AccountSnapshot, LiveQuote, Order, Position, Strategy, StrategyRun, Symbol
from tradeforge.database.session import get_application_engine, session_scope


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


def test_default_tenant_constant_is_shared_by_settings_and_models() -> None:
    assert Settings.model_fields["default_tenant_id"].default == DEFAULT_TENANT_ID
    assert StrategyRun.__table__.c.tenant_id.default.arg == DEFAULT_TENANT_ID


def test_dashboard_counts_symbols_in_the_database(session, symbol) -> None:
    statements: list[str] = []

    def capture_statement(connection, cursor, statement, parameters, context, executemany) -> None:
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    engine = session.get_bind()
    event.listen(engine, "before_cursor_execute", capture_statement)
    try:
        document = render_dashboard(session, None)
    finally:
        event.remove(engine, "before_cursor_execute", capture_statement)

    assert "<strong>Symbols</strong><div>1</div>" in document
    assert any("count(" in statement.lower() and "symbols" in statement.lower() for statement in statements)


def test_api_lifespan_initializes_database_and_health_checks_it(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert (tmp_path / "data" / "tradeforge.db").exists()


def test_relationship_endpoints_use_bounded_eager_load_queries(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")
    init_db()
    with session_scope() as session:
        for index, ticker in enumerate(("AAPL", "MSFT"), start=1):
            symbol = Symbol(ticker=ticker)
            strategy = Strategy(name=f"strategy-{index}")
            session.add_all([symbol, strategy])
            session.flush()
            run = StrategyRun(
                strategy_id=strategy.id,
                symbol_id=symbol.id,
                start_date=datetime(2026, 8, 14, 9, 0, tzinfo=UTC),
                end_date=datetime(2026, 8, 14, 16, 0, tzinfo=UTC),
            )
            session.add_all(
                [
                    run,
                    Position(symbol_id=symbol.id, quantity=index, average_cost=100, realized_pnl=0),
                    Order(
                        symbol_id=symbol.id,
                        side="buy",
                        order_type="market",
                        quantity=index,
                        status="open",
                    ),
                ]
            )

    statements: list[str] = []

    def count_statement(connection, cursor, statement, parameters, context, executemany) -> None:
        if statement.lstrip().upper().startswith(("SELECT", "WITH")):
            statements.append(statement)

    with TestClient(app) as client:
        engine = get_application_engine()
        event.listen(engine, "before_cursor_execute", count_statement)
        try:
            for path, query_budget in (("/positions", 1), ("/orders", 1), ("/strategy-runs", 1)):
                statements.clear()
                response = client.get(path)
                assert response.status_code == 200
                assert len(response.json()) == 2
                assert len(statements) == query_budget
        finally:
            event.remove(engine, "before_cursor_execute", count_statement)


def test_api_auth_roles_dashboard_and_tenant_isolation(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("TRADEFORGE_DATABASE_URL", "sqlite:///data/tradeforge.db")
    monkeypatch.setenv("TRADEFORGE_API_AUTH_ENABLED", "true")
    monkeypatch.setenv("TRADEFORGE_ENABLE_METRICS", "true")
    get_settings.cache_clear()
    init_db()
    with session_scope() as session:
        first_tenant = create_tenant(session, "first")
        second_tenant = create_tenant(session, "second")
        _, first_secret = create_api_key(session, first_tenant.id, "dashboard", "viewer")
        _, operator_secret = create_api_key(session, first_tenant.id, "metrics", "operator")
        symbol = Symbol(ticker="AAPL")
        first_strategy = Strategy(name="first-strategy")
        second_strategy = Strategy(name="second-strategy")
        session.add_all([symbol, first_strategy, second_strategy])
        session.flush()
        first_run = StrategyRun(
            tenant_id=first_tenant.id,
            strategy_id=first_strategy.id,
            symbol_id=symbol.id,
            start_date=datetime(2026, 8, 16, 9, tzinfo=UTC),
            end_date=datetime(2026, 8, 16, 16, tzinfo=UTC),
        )
        second_run = StrategyRun(
            tenant_id=second_tenant.id,
            strategy_id=second_strategy.id,
            symbol_id=symbol.id,
            start_date=datetime(2026, 8, 16, 9, tzinfo=UTC),
            end_date=datetime(2026, 8, 16, 16, tzinfo=UTC),
        )
        session.add_all([first_run, second_run])
        session.flush()
        session.add_all(
            [
                Position(strategy_run_id=first_run.id, symbol_id=symbol.id, quantity=1, average_cost=100),
                Position(strategy_run_id=second_run.id, symbol_id=symbol.id, quantity=2, average_cost=100),
            ]
        )

    with TestClient(app) as client:
        missing = client.get("/positions")
        health_response = client.get("/health")
        positions_response = client.get("/positions", headers={"X-TradeForge-Key": first_secret})
        runs_response = client.get("/strategy-runs", headers={"X-TradeForge-Key": first_secret})
        dashboard_response = client.get("/dashboard", headers={"X-TradeForge-Key": first_secret})
        viewer_metrics = client.get("/metrics", headers={"X-TradeForge-Key": first_secret})
        operator_metrics = client.get("/metrics", headers={"X-TradeForge-Key": operator_secret})

    assert missing.status_code == 401
    assert health_response.status_code == 200
    assert [item["quantity"] for item in positions_response.json()] == [1]
    assert [item["strategy"] for item in runs_response.json()] == ["first-strategy"]
    assert dashboard_response.status_code == 200
    assert "first-strategy" in dashboard_response.text
    assert "second-strategy" not in dashboard_response.text
    assert "Content-Security-Policy" in dashboard_response.headers
    assert viewer_metrics.status_code == 403
    assert operator_metrics.status_code == 200
