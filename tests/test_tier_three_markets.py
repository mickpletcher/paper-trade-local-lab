from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from tradeforge.broker_sim.microstructure import MarketMicrostructure
from tradeforge.database.models import OrderSide
from tradeforge.markets.derivatives import CalendarSpread, CFDContract, OTCMetalPosition, PredictionContract, SpreadLeg
from tradeforge.markets.instruments import (
    CreditInstrument,
    FixedIncomeInstrument,
    IndexDerivative,
    InternationalEquity,
    RateInstrument,
    VolatilityInstrument,
)


def test_extended_instrument_models_calculate_values() -> None:
    equity = InternationalEquity("7203", "XTKS", "JPY", "JP", lot_size=100)
    bond = FixedIncomeInstrument(1_000, 0.05, 2)
    rate = RateInstrument(1_000_000, 0.04, 2)
    credit = CreditInstrument(100_000, 0.02, 0.4)
    volatility = VolatilityInstrument(10_000, 0.2)
    derivative = IndexDerivative("SPX", 5_000, 50)

    assert equity.base_currency_value(100, 3_000, 0.007) == pytest.approx(2_100)
    assert bond.price(0.04) > 1_000
    assert rate.mark_to_market(0.05) == pytest.approx(20_000)
    assert credit.expected_loss == pytest.approx(1_200)
    assert volatility.payoff(0.25) == pytest.approx(500)
    assert derivative.profit_and_loss(5_010, 2) == pytest.approx(1_000)


def test_extended_derivative_models_calculate_net_profit_and_loss() -> None:
    cfd = CFDContract(100, 10, financing_rate=0.1)
    spread = CalendarSpread(
        SpreadLeg(100, -1),
        SpreadLeg(105, 1),
        date(2026, 9, 1),
        date(2026, 12, 1),
    )
    metal = OTCMetalPosition("gold", 10, 2_000, storage_bps_per_year=25)

    assert cfd.profit_and_loss(110, 30) < 100
    assert spread.profit_and_loss(98, 110) == pytest.approx(7)
    assert metal.profit_and_loss(2_100, 365) == pytest.approx(950)
    assert PredictionContract(0.4, 10, True).settlement_profit_and_loss == pytest.approx(6)


def test_microstructure_models_halts_queue_latency_limits_odd_lots_and_impact() -> None:
    submitted_at = datetime(2026, 8, 16, 12, tzinfo=UTC)
    model = MarketMicrostructure(
        session_phase="opening_auction",
        upper_price_limit=101,
        round_lot_size=100,
        latency_ms=50,
        queue_ahead_quantity=25,
        daily_volume=10_000,
        market_impact_coefficient=1.0,
    )

    fill = model.simulate_fill(OrderSide.BUY, 100, 100, 75, submitted_at)
    halted = MarketMicrostructure(halted=True).simulate_fill(OrderSide.SELL, 10, 100, 10, submitted_at)

    assert fill.quantity == 50
    assert fill.price == 101
    assert fill.odd_lot
    assert fill.executed_at == submitted_at + timedelta(milliseconds=50)
    assert fill.session_phase == "opening_auction"
    assert halted.quantity == 0
    assert halted.reason == "halted"


@pytest.mark.parametrize(
    "constructor",
    [
        lambda: InternationalEquity("", "XNYS", "USD", "US"),
        lambda: FixedIncomeInstrument(0, 0.05, 1),
        lambda: CreditInstrument(100, 1.1, 0.4),
        lambda: CFDContract(100, 0),
        lambda: PredictionContract(-0.1, 1, True),
        lambda: MarketMicrostructure(lower_price_limit=110, upper_price_limit=100),
    ],
)
def test_extended_models_reject_invalid_contracts(constructor) -> None:
    with pytest.raises(ValueError):
        constructor()
