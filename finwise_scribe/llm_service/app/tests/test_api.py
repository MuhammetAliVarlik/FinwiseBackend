from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

def test_health_check(client: TestClient):
    """Verify the LLM service health endpoint is alive."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_generate_prompt_endpoint(client: TestClient):
    """Verify /predict uses the current contract and response payload."""
    payload = {
        "symbol": "AAPL",
        "market_data": {
            "rsi": 56.3,
            "rsi_signal": "NEUTRAL",
            "trend": "BULLISH",
            "macd_hist": 0.12,
        },
    }

    mocked_result = {
        "symbol": "AAPL",
        "signal": "BULLISH",
        "prediction_token": "P_SURGE_V_HIGH",
        "prediction": "P_SURGE_V_HIGH",
        "confidence": 0.82,
        "confidence_score": 82,
        "history_used": "symbolized_technical_context",
        "reasoning": "RSI and trend are both supportive.",
        "divergence": "NONE",
        "shadow_baseline": {},
    }

    engine_mock = AsyncMock()
    engine_mock.predict = AsyncMock(return_value=mocked_result)

    with patch("app.main.get_engine", return_value=engine_mock):
        response = client.post("/predict", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["signal"] == "BULLISH"
    assert data["prediction_token"] == "P_SURGE_V_HIGH"
    assert "reasoning" in data