from __future__ import annotations

from fastapi.testclient import TestClient

from tradeforge.api.app import app


def test_openapi_contains_endpoint_examples() -> None:
    client = TestClient(app)

    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    health_example = document["paths"]["/health"]["get"]["responses"]["200"]["content"]["application/json"]["example"]
    orders_example = document["paths"]["/orders"]["get"]["responses"]["200"]["content"]["application/json"]["example"]
    strategy_runs_example = document["paths"]["/strategy-runs"]["get"]["responses"]["200"]["content"]["application/json"]["example"]

    assert health_example == {"status": "ok"}
    assert orders_example[0]["status"] == "filled"
    assert strategy_runs_example[0]["strategy"] == "moving-average-cross"
