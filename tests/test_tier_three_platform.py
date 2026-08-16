from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from tests.conftest import add_bar
from tradeforge.analytics.advanced import advanced_analytics, beta, market_regimes, rolling_volatility
from tradeforge.auth.service import AuthenticationError, authenticate_api_key, create_api_key, create_tenant
from tradeforge.backtesting.performance import (
    AnalyticsTask,
    benchmark_vectorized_path,
    run_parallel_analytics,
    vectorized_moving_average_signals,
)
from tradeforge.backtesting.portfolio import AllocationRule, PortfolioBacktestEngine
from tradeforge.connectors.catalog import ConnectorAdapter, ConnectorCatalog
from tradeforge.database.models import APIKey, Experiment, ExperimentArtifact, PriceBar, StrategyRun, Symbol
from tradeforge.plugins.registry import PluginKind, create_default_registry
from tradeforge.runtime.events import Event, EventKind, EventRuntime
from tradeforge.strategies.moving_average_cross import MovingAverageCrossStrategy


def test_event_runtime_processes_timestamp_and_publish_order() -> None:
    runtime = EventRuntime()
    handled: list[str] = []
    runtime.subscribe(EventKind.BAR, lambda event: handled.append(str(event.payload["name"])))
    late = datetime(2026, 8, 16, 12, tzinfo=UTC)
    early = late - timedelta(minutes=1)

    runtime.publish(Event(late, EventKind.BAR, {"name": "late-first"}))
    runtime.publish(Event(early, EventKind.BAR, {"name": "early"}))
    runtime.publish(Event(late, EventKind.BAR, {"name": "late-second"}))

    assert [event.payload["name"] for event in runtime.run(max_events=2)] == ["early", "late-first"]
    assert handled == ["early", "late-first"]
    assert runtime.pending_count == 1
    assert runtime.run()[0].payload["name"] == "late-second"
    with pytest.raises(ValueError, match="timezone aware"):
        Event(datetime(2026, 8, 16), EventKind.NEWS)


def test_advanced_analytics_reports_risk_beta_and_regimes() -> None:
    prices = [100, 101, 102, 101, 105, 108]
    benchmark = [200, 202, 204, 202, 210, 216]

    returns = [0.01, 1 / 101, -1 / 102, 4 / 101, 3 / 105]
    result = advanced_analytics(prices, benchmark, {"market": returns}, window=2)

    assert result["beta"] == pytest.approx(1)
    assert result["factor_betas"] == {"market": pytest.approx(1)}
    assert result["latest_rolling_volatility"] is not None
    assert len(result["market_regimes"]) == len(prices)
    assert rolling_volatility([0.01, -0.01], window=2)[-1] == pytest.approx(0.158745)
    assert beta([1, 2], [1, 1]) is None
    assert market_regimes([100, 101, 102], window=2)[-1] == "bull"


def test_vectorized_and_parallel_analytics_paths() -> None:
    closes = [3, 2, 1, 2, 3, 2, 1]

    signals = vectorized_moving_average_signals(closes, 2, 3)
    parallel = run_parallel_analytics(
        [
            AnalyticsTask("AAPL", tuple(closes), window=2),
            AnalyticsTask("MSFT", tuple(value + 10 for value in closes), window=2),
        ],
        max_workers=2,
    )
    benchmark = benchmark_vectorized_path(closes * 100, 2, 3, maximum_seconds=2)

    assert 1 in signals
    assert -1 in signals
    assert set(parallel) == {"AAPL", "MSFT"}
    assert benchmark["rows"] == 700
    with pytest.raises(ValueError, match="unique"):
        run_parallel_analytics([AnalyticsTask("AAPL", tuple(closes)), AnalyticsTask("AAPL", tuple(closes))])


def test_plugin_registry_exposes_builtins_and_rejects_unknown_plugins() -> None:
    registry = create_default_registry()

    strategy = registry.get(PluginKind.STRATEGY, "moving-average-cross")

    assert strategy is MovingAverageCrossStrategy
    assert {(item.kind.value, item.name) for item in registry.list()} == {
        ("strategy", "moving-average-cross"),
        ("broker", "simulated"),
        ("indicator", "simple-moving-average"),
        ("report", "markdown"),
    }
    with pytest.raises(KeyError, match="Unknown strategy 'missing'"):
        registry.get(PluginKind.STRATEGY, "missing")
    with pytest.raises(ValueError, match="already registered"):
        registry.register(PluginKind.STRATEGY, "moving-average-cross", object())


def test_connector_catalog_builds_safe_requests_and_normalizes_quotes() -> None:
    catalog = ConnectorCatalog()
    adapter = ConnectorAdapter(catalog.get("tradier"), token="secret")

    request = adapter.build_quote_request(["aapl", "MSFT"])
    quote = adapter.normalize_quote(
        "aapl",
        {"last": "101.5", "bid": 101.4, "ask": 101.6, "timestamp": "2026-08-16T12:00:00Z"},
    )
    signal = adapter.paper_signal("AAPL", "buy", 2)

    assert request.url.endswith("markets/quotes?symbols=AAPL,MSFT")
    assert request.headers["Authorization"] == "Bearer secret"
    assert quote.last_price == 101.5
    assert quote.timestamp.tzinfo is UTC
    assert signal["transmitted"] is False
    assert all(not item.live_order_routing for item in catalog.list())
    with pytest.raises(ValueError, match="HTTPS"):
        ConnectorAdapter(catalog.get("tradier"), base_url="http://example.test")
    with pytest.raises(ValueError, match="external bridge"):
        ConnectorAdapter(catalog.get("crypto-exchange")).build_quote_request(["BTC/USD"])


def test_api_key_lifecycle_hashes_rotates_and_revokes_secrets(session) -> None:
    tenant = create_tenant(session, "Research")
    key, secret = create_api_key(session, tenant.id, "dashboard", "viewer", datetime.now(UTC) + timedelta(days=1))

    context = authenticate_api_key(session, secret)

    assert context.tenant_id == tenant.id
    assert context.allows("viewer")
    assert not context.allows("operator")
    assert key.key_hash.startswith("pbkdf2_sha256$")
    assert secret not in key.key_hash
    assert "secret" not in key.__table__.columns
    key.revoked_at = datetime.now(UTC)
    session.flush()
    with pytest.raises(AuthenticationError, match="Invalid"):
        authenticate_api_key(session, secret)
    assert session.scalar(select(APIKey).where(APIKey.id == key.id)) is key


def test_portfolio_backtest_allocates_capital_tracks_experiments_and_events(
    session, symbol, monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    second_symbol = Symbol(ticker="MSFT")
    session.add(second_symbol)
    session.flush()
    closes = [10, 9, 8, 12, 13, 8, 7, 11]
    for index, close in enumerate(closes, start=1):
        add_bar(session, symbol, index, close, close + 1, close - 1, close)
        add_bar(session, second_symbol, index, close + 20, close + 21, close + 19, close + 20)

    result = PortfolioBacktestEngine(
        session,
        lambda: MovingAverageCrossStrategy(short_window=2, long_window=3, order_size=2),
        ["AAPL", "MSFT"],
        datetime(2023, 1, 1, tzinfo=UTC),
        datetime(2023, 1, 8, tzinfo=UTC),
        20_000,
        allocation_rule=AllocationRule.FIXED,
        weights={"AAPL": 0.6, "MSFT": 0.4},
    ).run()

    assert result["starting_cash"] == 20_000
    assert result["allocations"] == {"AAPL": 12_000, "MSFT": 8_000}
    assert result["events_processed"] == 3
    assert len(result["runs"]) == 2
    experiments = session.scalars(select(Experiment)).all()
    assert len(experiments) == 2
    assert len(session.scalars(select(ExperimentArtifact)).all()) == 2
    aapl_experiment = session.scalar(
        select(Experiment)
        .join(StrategyRun, Experiment.strategy_run_id == StrategyRun.id)
        .where(StrategyRun.symbol_id == symbol.id)
    )
    assert aapl_experiment is not None
    bars = session.scalars(select(PriceBar).where(PriceBar.symbol_id == symbol.id).order_by(PriceBar.timestamp)).all()
    dataset = [
        {
            "timestamp": bar.timestamp.isoformat(),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
        }
        for bar in bars
    ]
    expected_digest = hashlib.sha256(
        json.dumps(dataset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    assert aapl_experiment.dataset_sha256 == expected_digest


def test_portfolio_backtest_rolls_back_every_sleeve_when_one_fails(session, symbol, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    incomplete_symbol = Symbol(ticker="MSFT")
    session.add(incomplete_symbol)
    session.flush()
    for index, close in enumerate([10, 9, 8, 12, 13, 8, 7, 11], start=1):
        add_bar(session, symbol, index, close, close + 1, close - 1, close)
    add_bar(session, incomplete_symbol, 1, 30, 31, 29, 30)

    with pytest.raises(ValueError, match="at least two price bars"):
        PortfolioBacktestEngine(
            session,
            lambda: MovingAverageCrossStrategy(short_window=2, long_window=3, order_size=2),
            ["AAPL", "MSFT"],
            datetime(2023, 1, 1, tzinfo=UTC),
            datetime(2023, 1, 8, tzinfo=UTC),
            20_000,
        ).run()

    assert session.scalars(select(StrategyRun)).all() == []
    assert session.scalars(select(Experiment)).all() == []
    reports = tmp_path / "data" / "reports"
    assert not reports.exists() or list(reports.iterdir()) == []


@pytest.mark.parametrize(
    ("symbols", "cash", "weights", "message"),
    [
        (["AAPL", "AAPL"], 1_000, None, "unique"),
        (["AAPL"], 0, None, "positive"),
        (["AAPL", "MSFT"], 1_000, {"AAPL": 1.0}, "match"),
    ],
)
def test_portfolio_backtest_rejects_invalid_allocations(session, symbols, cash, weights, message) -> None:
    with pytest.raises(ValueError, match=message):
        PortfolioBacktestEngine(
            session,
            lambda: MovingAverageCrossStrategy(2, 3, 1),
            symbols,
            datetime(2023, 1, 1, tzinfo=UTC),
            datetime(2023, 1, 2, tzinfo=UTC),
            cash,
            allocation_rule=AllocationRule.FIXED if weights is not None else AllocationRule.EQUAL,
            weights=weights,
        )


def test_semantic_release_invokes_the_release_workflow_without_a_tag_push_event() -> None:
    root = Path(__file__).resolve().parents[1]
    semantic_release = (root / ".github" / "workflows" / "semantic-release.yml").read_text(encoding="utf-8")
    release = (root / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")

    assert "uses: ./.github/workflows/release.yml" in semantic_release
    assert "workflow_call:" in release
    assert "ref: ${{ inputs.tag || github.ref }}" in release
